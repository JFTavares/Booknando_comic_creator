#!/usr/bin/env python
# coding: utf-8
# Create by: José Fernando Tavares - Booknando Livros
# Twitter: @JFTavares
# email: fernando@booknando.com.br
# Booknando Comic Creator v0.2. 
# Just need Python v3
# TO-DO: 
#   - Renomear imagens
#   - Ler metadados das imagens
#   - Leitura, recorte e importação de PDF
#   - Manipular inDesign


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
import optimiza


class ComicCreator(object):
    
    version = 2  # class version when used as library


    def __init__(self, file_name=None, meta_file=None, toc_file=None,  verbose=0):

        self._output_name = file_name
        self.toc_file = toc_file
        self._files = None
        self._zip = None  # the in memory zip file
        self._zip_data = None
        self._content = []
        self._count = 1
        self._open_metadata(meta_file)
        self.meta_info = dict(
            title=metadata['title'],
            creator= metadata['author'],
            publisher=metadata['publisher'],
            illustrator=metadata['illustrator'],
            translator= metadata['translator'],
            rights=metadata['rights'],
            source=metadata['source'],
            ibooksVersion=metadata['ibooksVersion'],
            img_width = metadata['img_width'],
            img_height = metadata['img_height'],
            opf_name="content.opf",
            nav_name="nav.xhtml",
            dctime=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            opf_ns='http://www.idpf.org/2007/opf',
            xsi_ns='http://www.w3.org/2001/XMLSchema-instance',
            dcterms_ns='http://purl.org/dc/terms/',
            dc_ns='http://purl.org/dc/elements/1.1/',
            rendition='http://www.idpf.org/vocab/rendition/#',
            ibooks='http://vocabulary.itunes.apple.com/rdf/ibooks/vocabulary-extensions-1.0/',
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
            self.meta_info['nav_point'] = None
            with open(self._output_name, 'wb') as ofp:
                ofp.write(self._zip_data.getvalue())

            return True
        return False

    def _open_metadata(self, meta_file):
        with open(meta_file) as f:
            global metadata
            metadata=yaml.safe_load(f)

    def add_image_file(self, file_name):
        self._add_image_file(file_name)
        self._count += 1

    def _write_content(self):
        d = self.meta_info.copy()
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
                    '<item href="Images/{}" id="{}" media-type="{}"/>'.format(*f))

            if f[1].startswith('html'):
                if int(f[3])%2:
                    spine.append('<itemref idref="{}" properties="page-spread-right" />'.format(f[1]))
                else:
                    spine.append('<itemref idref="{}" properties="page-spread-left" />'.format(f[1]))


        d['manifest'] = '\n    '.join(manifest)
        d['spine'] = '\n    '.join(spine)
        d['ts'] = datetime.datetime.utcnow().isoformat() + '+00:00'
        self._write_file_from_template('OEBPS/'+self.meta_info["opf_name"], 'template/content.tmpl', d)        



    def _read_create_toc(self,d):
        lista_toc = []
        nav = []
        d['nav'] = ''
        with open(self.toc_file, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',') 

            for linha in spamreader:
                lista_toc.append(linha)               

            for f in lista_toc:
                nav.append('<li><a href="pag_{}.xhtml">{}</a></li>'.format(f[1], f[0]))
                d['nav'] = '\n    '.join(nav)


    def _create_page_list(self,d):
        page_list = []  
        d['page_list'] = ''
        for f in self._content:
            if f[1].startswith('html'):
                page_list.append('<li><a href="{}">{}</a></li>'.format(f[0],f[3]))
                d['page_list'] = '\n    '.join(page_list)     

    def _write_nav(self):
        d = self.meta_info.copy()
        self._read_create_toc(d) 
        self._create_page_list(d)      
        self._write_file_from_template('OEBPS/'+self.meta_info["nav_name"], 'template/nav.tmpl', d)

    def _add_html(self, title):
        file_name = self._name(False)
        d = self.meta_info.copy()
        d['img_name'] = self._name()
        self._write_file_from_template('OEBPS/'+file_name, 'template/html.tmpl', d)     
        self._content.append((file_name, 'html{}'.format(self._count), 'application/xhtml+xml', '{}'.format(self._count)))

    # Função para gravar arquivo usando um template
    def _write_file_from_template(self, file, template, data):
        template_file=open(template)
        template=template_file.read()
        self._add_from_bytes(file, template.format(**data).encode('utf-8'))

    def _write_style_sheet(self):
        file_name = self.meta_info['style_sheet']
        self._write_file_from_template('OEBPS/Styles/'+file_name, 'template/css.tmpl', self.meta_info)
        self._content.append((file_name, 'css', 'text/css'))

    def _name(self, image=True):
        return 'pag_{}.{}'.format(self._count, 'jpg' if image else 'xhtml')

    def _add_image_file(self, file_name, z=None):
        z = z if z else self.zip  # initializes if not done yet
        self._add_html(file_name)

        z.write(file_name, 'OEBPS/Images/'+self._name())
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
        self.meta_info['uuid'] = uuid.uuid4()
        self.meta_info['lead_ltr'] = random.choice(string.ascii_lowercase)
        self.meta_info['nav_uuid'] = uuid.uuid4()
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
        self._write_file_from_template('META-INF/container.xml', 'template/container.tmpl', self.meta_info)

def make_epub(args):
    with ComicCreator(               
                   file_name=args.output,meta_file=args.meta, toc_file=args.toc, verbose=0) as single_file_item:
        for file_name in args.file_names:
            optimiza.resize_image(file_name)
            single_file_item.add_image_file(file_name)


def main():
    parser = argparse.ArgumentParser(description='Gerador de Comic Books no formato ePub3 FLX')
    parser.add_argument("--output", "-o", help = "Nome do arquivo", required=True)
    parser.add_argument("--meta", help = "Arquivo de metadados", required=True)
    parser.add_argument("--toc", help="Arquivo de sumário", required=True)
    parser.add_argument("file_names", nargs="+")
    args = parser.parse_args()

    make_epub(args)


if __name__ == "__main__":
    main()
