    def _add_container(self):
        self._add_from_bytes('META-INF/container.xml', dedent("""\
        <?xml version="1.0"?>
           <container version="1.0" xmlns="{cont_urn}">
          <rootfiles>
            <rootfile full-path="OEBPS/{opf_name}" media-type="{mt}"/>
          </rootfiles>
        </container>
        """).rstrip().format(**self.d))