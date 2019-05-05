from PyPDF2 import PdfFileWriter,PdfFileReader,PdfFileMerger
import sys

original = sys.argv[1]
target   = original[:-4] + '.cropped.pdf'



reader = PdfFileReader(open(original,"rb"))
numPage = reader.getNumPages()

page = reader.getPage(0)

lowerLeft = page.trimBox.getLowerLeft()
lowerRight = page.trimBox.getLowerRight()
upperLeft = page.trimBox.getUpperLeft()
upperRight = page.trimBox.getUpperRight()

writer = PdfFileWriter()

for i in range(numPage):
    page = reader.getPage(i)
    page.cropBox.setLowerLeft(lowerLeft)
    page.cropBox.setLowerRight(lowerRight)
    page.cropBox.setUpperLeft(upperLeft)
    page.cropBox.setUpperRight(upperRight)
    writer.addPage(page)

salvaFile = open(target, 'wb')
writer.write(salvaFile)
salvaFile.close()


