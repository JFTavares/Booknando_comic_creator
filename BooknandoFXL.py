#!/usr/bin/env python
# coding: utf-8
# Booknando Comic Creator 0.1. 
# baseado em: ComicIO: copyright (C) 2016, Daejuan Jacobs
# Just need Python v3
# Automatic create ePub3 Fixed Layout
# ToDo
# * Add page count
# * dc:identifier for UPC/ISBN http://www.idpf.org/epub/30/spec/epub30-publications.html#sec-opf-dcidentifier
# * Coverimage.xtml
# * Fix {title}
# * YAML/JSON load metadata

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


class Jpg2Epub(object):
    
    version = 1  # class version when used as library

    def __init__(self, title, file_name=None, creator=None,                       title_sort=None, publisher=None,
                 series=None, img_width=None, img_height=None,  series_idx=None, verbose=0):
        self._output_name = file_name if file_name else \
            title.replace(' ', '_') + '.epub'
        self._files = None
        self._zip = None  # the in memory zip file
        self._zip_data = None
        self._content = []
        self._count = 1
        self._series = series
        self._series_idx = series_idx
        self.d = dict(
            title=title,
            title_sort=title_sort if title_sort else title,
            creator=creator if creator else 'Jose Fernando',
            publisher=publisher if publisher else 'Editora Booknando',
            img_width=img_width if img_width else '768',
            img_height=img_height if img_height else '1024',
            opf_name="content.opf",
            toc_name="toc.ncx",
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
            uuid=None,
            nav_point=None,
            nav_uuid=None,
        )

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        if value is None:
            if isinstance(self._zip_data, str):
                return
            self._write_toc()
            self._write_content()
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

    def add_image_file(self, file_name):
        self._add_image_file(file_name)
        self._count += 1
    """
    #nav_point id cannot start with a number according to epub spec.
    """
    def _write_toc(self):
        self._add_from_bytes('OEBPS/'+self.d['toc_name'], dedent("""\
        <?xml version='1.0' encoding='utf-8'?>
        <ncx xmlns="{ncx_ns}" version="2005-1" xml:lang="eng">
          <head>
            <meta content="{uuid}" name="dtb:uid"/>
            <meta content="2" name="dtb:depth"/>
            <meta content="Booknando Comic Creator v0.1" name="dtb:generator"/>
            <meta content="0" name="dtb:totalPageCount"/>
            <meta content="0" name="dtb:maxPageNumber"/>
          </head>
          <docTitle>
            <text>Sumário</text>
          </docTitle>
          <navMap>
            <navPoint id="{lead_ltr}{nav_uuid}" playOrder="1">
              <navLabel>
                <text>Start</text>
              </navLabel>
              <content src="{nav_point}"/>
            </navPoint>
          </navMap>
        </ncx>
        """).format(**self.d))
        self._content.append((self.d['toc_name'], 'ncx',
                              'application/x-dtbncx+xml'))

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
                spine.append('<itemref idref="{}"/>'.format(f[1]))
        d['manifest'] = '\n    '.join(manifest)
        d['spine'] = '\n    '.join(spine)
        d['ts'] = datetime.datetime.utcnow().isoformat() + '+00:00'
        d['series'] = ''
        if self._series:
            d['series'] = \
                u'\n' \
                '<meta name="calibre:series" content="{}"/>' \
                '<meta name="calibre:series_index" content="{}"/>'.format(
                    self._series, self._series_idx)
        self._add_from_bytes('OEBPS/'+self.d["opf_name"], dedent(u"""\
        <?xml version='1.0' encoding='utf-8'?>
        <package xmlns="{opf_ns}" unique-identifier="BookID" version="3.0" prefix="rendition: {rendition} ibooks: {ibooks}">
        <metadata xmlns:dcterms="{dcterms_ns}" xmlns:dc="{dc_ns}">

            <dc:title>{title}</dc:title>
            <dc:creator>{creator}</dc:creator>
            <dc:publisher>{publisher}</dc:publisher>
            <dc:language>pt-br</dc:language>
            <meta content="cover-image" name="cover" />
            <dc:date>{dctime}</dc:date>

            <dc:identifier id="BookID">{uuid}</dc:identifier>
            <meta property="dcterms:modified">{dctime}</meta>        
            <meta property="rendition:layout">pre-paginated</meta>	
            <meta property="rendition:orientation">auto</meta>
            <meta property="rendition:spread">both</meta>
            <meta property="ibooks:specified-fonts">true</meta>
          </metadata>
          <manifest>
            <item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml" />
            <item href="CSS/{style_sheet}" id="css" media-type="text/css"/>
            {manifest}
            <item href="toc.ncx" id="ncx" media-type="application/x-dtbncx+xml"/>
          </manifest>
          <spine toc="ncx">
            {spine}
          </spine>
        </package>
        """).format(**d).encode('utf-8'))
    def _write_nav(self):
        d = self.d.copy()
        nav = []
        d['nav'] = ''
        for f in self._content:
            if f[1].startswith('html'):
                nav.append('<li><a href="{}">Page {}</a></li>'.format(*f))
        d['nav'] = '\n    '.join(nav)
        self._add_from_bytes('OEBPS/'+self.d["nav_name"], dedent(u"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml"
            xmlns:epub="http://www.idpf.org/2007/ops">
          <head>
            <meta http-equiv="default-style" content="text/html; charset=utf-8"/>
            <title>{title}</title>
            <link rel="stylesheet" href="CSS/{style_sheet}" type="text/css"/>
          </head>
          <body>
            <!-- Start of Nav Structures -->
            <!-- Main Contents -->
            <nav epub:type="toc" id="toc">
            <h1>Sumário</h1>
                <ol>
                    {nav}
                </ol>
            </nav>
            </body>
        </html>
        """).format(**d).encode('utf-8'))

    def _add_html(self, title):
        file_name = self._name(False)
        d = self.d.copy()
        d['title'] = title
        d['img_name'] = self._name()
        self._add_from_bytes('OEBPS/'+file_name, dedent(u"""\
        <?xml version='1.0' encoding='utf-8'?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" 
                xmlns:epub="http://www.idpf.org/2007/ops" 
                xmlns:ev="http://www.w3.org/2001/xml-events"
                xmlns:ibooks="http://apple.com/ibooks/html-extensions"
                lang="pt-br" xml:lang="pt-br">
        <head>
            <title>{title}</title>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <meta name="viewport" content="width={img_width}, height={img_height}" />
            <link href="CSS/{style_sheet}" rel="stylesheet" type="text/css"/>
        </head>
         <body>
            <div class="pageImage">
              <img src="Image/{img_name}" alt="{title}"/>
            </div>
        </body>
        </html>
        """).format(**d).encode('utf-8'))
        self._content.append((file_name, 'html{}'.format(self._count),
                              'application/xhtml+xml'))
        if self.d['nav_point'] is None:
            self.d['nav_point'] = file_name
            self._write_style_sheet()

# Nova função para gravar aquivo
    def _write_file_from_template(self, file, template, data):
        template_file=open(template)
        template=template_file.read()
        self._add_from_bytes(file, dedent(template).format(**data).encode('utf-8'))

    def _write_style_sheet(self):
        file_name = self.d['style_sheet']
        self._write_file_from_template('OEBPS/CSS/'+file_name, 'template/css.tmpl', self.d)
        self._content.append((file_name, 'css', 'text/css'))

    def _name(self, image=True):
        """no leading zero's necessary in zip internal filenames"""
        return 'pag_{}.{}'.format(self._count, 'jpg' if image else 'xhtml')

    def _add_image_file(self, file_name, width=None, height=None,
                        strip=None, max_strip_pixel=None, z=None):
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
        self._content.append((self._name(), 'img{}'.format(self._count),
                              'image/jpeg'))

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

class CBFormat(object):
    def __init__(self, files, title, file_name=None):
        #self.path = path
        self.files = files
        self._output_name = file_name if file_name else \
            title.replace(' ', '_') + '.cbz'

    def __enter__(self):
        return self

    def __exit__(self, typ, value, traceback):
        self.zipdir()

    def zipdir(self):
        zipf = zipfile.ZipFile(self._output_name, 'w', zipfile.ZIP_DEFLATED)
        for file in self.files:
            zipf.write(file, compress_type=zipfile.ZIP_DEFLATED)
        zipf.close()


def do_epub(args):
    with Jpg2Epub(args.title, title_sort=args.title_sort,
                   file_name=args.output_name,
                   series=args.series, series_idx=args.index,
                   creator=args.creator, publisher=args.publisher, img_width=args.width, img_height=args.height, verbose=0) as j2e:
        for file_name in args.file_names:
            j2e.add_image_file(file_name)

def do_cbz(args):
    with CBFormat(args.file_names, args.title) as cb:
        cb.zipdir()


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("--type", "-T", required=True)
    parser.add_argument("--title", "-t", required=True)
    parser.add_argument("--title-sort", help="alternative title for sorting")
    parser.add_argument(
        "--output_name", "-o",
        help="epub name if not specified, derived from title",
    )
    parser.add_argument("--series", help="series name")
    parser.add_argument("--index", help="series index")
    parser.add_argument("--creator", help="Creator/Author")
    parser.add_argument("--publisher", help="Publisher")
    parser.add_argument("--width", help="Image width")
    parser.add_argument("--height", help="Image height")
    parser.add_argument("file_names", nargs="+")
    args = parser.parse_args()

    if args.type == "epub":
        do_epub(args)
    elif args.type == "cbz":
        do_cbz(args)


if __name__ == "__main__":
    main()
