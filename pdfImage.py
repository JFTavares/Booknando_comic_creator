import pdf2image
from PIL import Image
import time
import sys

original = sys.argv[1]

#DECLARE CONSTANTS
PDF_PATH = original
DPI = 200
OUTPUT_FOLDER = None
FIRST_PAGE = None
LAST_PAGE = None
FORMAT = 'jpg'
THREAD_COUNT = 1
USERPWD = None
USE_CROPBOX = True
STRICT = False

def pdftopil():

    pil_images = pdf2image.convert_from_path(PDF_PATH, dpi=DPI, output_folder=OUTPUT_FOLDER, first_page=FIRST_PAGE, last_page=LAST_PAGE, fmt=FORMAT, thread_count=THREAD_COUNT, userpw=USERPWD, use_cropbox=USE_CROPBOX, strict=STRICT)
    return pil_images
    
def save_images(pil_images):
    #This method helps in converting the images in PIL Image file format to the required image format
    index = 3
    for image in pil_images:
        image.save("image/page_" + str(index) + ".jpg")
        index += 1

if __name__ == "__main__":
    pil_images = pdftopil()
    save_images(pil_images)