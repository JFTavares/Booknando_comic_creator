#!/usr/bin/env python
from PIL import Image,ImageFilter


def resize_image(file_name):
    basewidth = 1200
    file_imagem = Image.open(file_name)
    x, y = file_imagem.size
    if x == basewidth:
        print('Imagem já otimizada: ', file_name)
    else:
        wpercent = (basewidth/float(file_imagem.size[0]))
        hsize = int((float(file_imagem.size[1])*float(wpercent)))
        nova_imagem = file_imagem.resize((basewidth,hsize), Image.ANTIALIAS)

        dpi = (300, 300)
        nova_imagem.save(file_name, dpi=dpi)
        print('Salvando a imagem ', file_name)
