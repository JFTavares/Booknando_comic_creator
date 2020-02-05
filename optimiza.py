from PIL import Image,ImageFilter


def resize_image(file_name):
    basewidth = 1600
    file_imagem = Image.open(file_name)
    x, y = file_imagem.size
    wpercent = (basewidth/float(file_imagem.size[0]))
    hsize = int((float(file_imagem.size[1])*float(wpercent)))
    nova_imagem = file_imagem.resize((basewidth,hsize), Image.ANTIALIAS)
    dpi = file_imagem.info['dpi']

    if dpi[0] > 301:
        dpi = (300, 300)
        nova_imagem.save(file_name, dpi=dpi)
        print('Salvando a imagem ', file_name)
    else:
        print('Imagem com dpi ', dpi)