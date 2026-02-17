from PyPDF2 import PdfReader

file = open("chevrolet.pdf", "rb") # use your PDF filename
reader = PdfReader(file)

print(len(reader.pages)) # number of pages
print(reader.pages[0].extract_text()) # text from first page