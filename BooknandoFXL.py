#!/usr/bin/env python
# coding: utf-8
# Booknando Comic Creator 0.1. 
# baseado em: ComicIO: copyright (C) 2016, Daejuan Jacobs
# Just need Python v3
# TO-DO: 
#   - Renomear imagens
#   - Capturar tamanho dos metadados da imagem
#   - Leitura, recorte e importação de PDF


import os, sys
from io import open
from textwrap import dedent
from io import BytesIO
import zipfile
import uuid
import datetime
import random
import string
import argparse
import yaml
import csv


class ComicCreator(object):
    
    version = 1  # class version when used as library

    def __init__(self, file_name=None, meta_file=None, toc_file=None,  verbose=0):
        self._output_name = file_name
        self.toc_file = toc_file
        self._files = None
        self._zip = None  # the in memory zip file
        self._zip_data = None
        self._content = []
        self._count = 1
        self._open_metadata(meta_file)
        self.d = dict(
            title=metadata['title'],
            creator= metadata['author'],
            publisher=metadata['publisher'],
            img_width = metadata['img_width'],
            img_height = metadata['img_height'],
            opf_name="content.opf",
            nav_name="nav.xhtml",
            dctime=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            ncx_ns='http://www.daisy.org/z3986/2005/ncx/',
            opf_ns='http://www.idpf.org/2007/opf',
            xsi_ns='http://www.w3.org/2001/XMLSchema-instance',
            dcterms_ns='http://purl.org/dc/terms/',
            dc_ns='http://purl.org/dc/elements/1.1/',
            rendition='http://www.idpf.org/vocab/rendition/#',
            ibooks='http://vocabulary.itunes.apple.com/rdf/ibooks/vocabulary-extensions-1.0/',
            cal_ns='http://calibre.kovidgoyal.net/2009/metadata',
            cont_urn='urn:oasis:names:tc:opendocument:xmlns:container',
            mt='application/oebps-package+xml',  # media-type
            style_sheet='design.css',
            alt = metadata['alt'],
            uuid=None,
            isbn=metadata['ISBN'],
            nav_point=None,
            nav_uuid=None,
        )

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        if value is None:
            if isinstance(self._zip_data, str):
                return
            self._write_content()
            self._write_style_sheet()
            self._write_nav()
            self._zip.close()
            self._zip = None
            self.d['nav_point'] = None
            with open(self._output_name, 'wb') as ofp:
                ofp.write(self._zip_data.getvalue())
            # minimal test: listing contents of EPUB
            # os.system('unzip -lv ' + self._output_name)
            return True
        return False

    def _open_metadata(self, meta_file):
        with open(meta_file) as f:
            global metadata
            metadata = yaml.safe_load(f)

    def add_image_file(self, file_name):
        self._add_image_file(file_name)
        self._count += 1

    def _write_content(self):
        d = self.d.copy()
        manifest = []
        spine = []
        d['manifest'] = ''
        d['spine'] = ''
        for f in self._content:
            if f[1].startswith('html'):
                manifest.append(
                    '<item href="{}" id="{}" media-type="{}"/>'.format(*f))
            if f[1].startswith('img'):
                manifest.append(
                    '<item href="Image/{}" id="{}" media-type="{}"/>'.format(*f))

            if f[1].startswith('html'):
                numero = int(f[3])
                if numero%2:
                    spine.append('<itemref idref="{}" properties="page-spread-right" />'.format(f[1]))
                else:
                    spine.append('<itemref idref="{}" properties="page-spread-left" />'.format(f[1]))

        d['manifest'] = '\n    '.join(manifest)
        d['spine'] = '\n    '.join(spine)
        d['ts'] = datetime.datetime.utcnow().isoformat() + '+00:00'

        self._write_file_from_template('OEBPS/'+self.d["opf_name"], 'template/content.tmpl', d)        

    def _write_nav(self):
        d = self.d.copy()
        nav = []
        lista_toc = []
        page_list = []
        d['nav'] = ''


        with open(self.toc_file, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',') 

            for linha in spamreader:
                lista_toc.append(linha)
                
            i = 0
            for f in lista_toc:
                nav.append('<li><a href="pag_{}.xhtml">{}</a></li>'.format(lista_toc[i][1], lista_toc[i][0]))
                i = i+1
                d['nav'] = '\n    '.join(nav)
        
        d['page_list'] = ''
        for f in self._content:
            if f[1].startswith('html'):
                page_list.append('<li><a href="{}">{}</a></li>'.format(f[0],f[3]))
        d['page_list'] = '\n    '.join(page_list)
        
        self._write_file_from_template('OEBPS/'+self.d["nav_name"], 'template/nav.tmpl', d)

    def _add_html(self, title):
        file_name = self._name(False)
        d = self.d.copy()
       # d['title'] = title
        d['img_name'] = self._name()
        self._write_file_from_template('OEBPS/'+file_name, 'template/html.tmpl', d)
        
        self._content.append((file_name, 'html{}'.format(self._count), 'application/xhtml+xml', '{}'.format(self._count)))



# Nova função para gravar arquivo
    def _write_file_from_template(self, file, template, data):
        template_file=open(template)
        template=template_file.read()
        self._add_from_bytes(file, dedent(template).format(**data).encode('utf-8'))

    def _write_style_sheet(self):
        file_name = self.d['style_sheet']
        self._write_file_from_template('OEBPS/CSS/'+file_name, 'template/css.tmpl', self.d)
        self._content.append((file_name, 'css', 'text/css'))

    def _name(self, image=True):
        return 'pag_{}.{}'.format(self._count, 'jpg' if image else 'xhtml')

    def _add_image_file(self, file_name, width=None, height=None, strip=None, max_strip_pixel=None, z=None):
        z = z if z else self.zip  # initializes if not done yet
        self._add_html(file_name)
        # you can compress JPEGs, but with little result (1-8%) and
        # more complex/slow decompression (zip then jpeg)
        # Gain 2.836 Mb -> 2.798 Mb ( ~ 1% difference )
        if width:
           im = EpubImage(file_name)
           z.writestr(self._name(), im.read(), zipfile.ZIP_STORED)
        else:
            z.write(file_name, 'OEBPS/Image/'+self._name())
        self._content.append((self._name(), 'img{}'.format(self._count), 'image/jpeg'))

    @property
    def zip(self):
        if self._zip is not None:
            return self._zip
        self._zip_data = BytesIO()
        # create zip with default compression
        #self._zip_data = '/var/tmp/epubtmp/yy.zip'
        self._zip = zipfile.ZipFile(self._zip_data, "a",
                                    zipfile.ZIP_DEFLATED, False)
        self.d['uuid'] = uuid.uuid4()
        self.d['lead_ltr'] = random.choice(string.ascii_lowercase)
        self.d['nav_uuid'] = uuid.uuid4()
        self._add_mimetype()
        self._add_container()
        return self._zip

    def _add_from_bytes(self, file_name, data, no_compression=False):
        self._zip.writestr(
            file_name, data,
            compress_type=zipfile.ZIP_STORED if no_compression else None)

    def _add_mimetype(self):
        self._add_from_bytes('mimetype', dedent("""\
        application/epub+zip
        """).rstrip(), no_compression=True)

    def _add_container(self):
        self._add_from_bytes('META-INF/container.xml', dedent("""\
        <?xml version="1.0"?>
           <container version="1.0" xmlns="{cont_urn}">
          <rootfiles>
            <rootfile full-path="OEBPS/{opf_name}" media-type="{mt}"/>
          </rootfiles>
        </container>
        """).rstrip().format(**self.d))



def do_epub(args):
    with ComicCreator(               
                   file_name=args.output,meta_file=args.meta, toc_file=args.toc, verbose=0) as j2e:
        for file_name in args.file_names:
            j2e.add_image_file(file_name)


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        "--output", "-o", 
        help="epub name if not specified, derived from title", required=True
    )
    parser.add_argument("--meta", help="Arquivo de metadados", required=True)
    parser.add_argument("--toc", help="Arquivo de sumário", required=True)
    parser.add_argument("file_names", nargs="+")
    args = parser.parse_args()

    do_epub(args)


if __name__ == "__main__":
    main()
