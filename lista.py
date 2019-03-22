import csv
 
lista_toc = []
nav = []

with open('toc.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',') 

    for linha in spamreader:
        lista_toc.append(linha)
        
    i = 0
    for f in lista_toc:
        nav.append('<li><a href="pag_{}">{}</a></li>'.format(lista_toc[i][1], lista_toc[i][0]))
        i = i+1
print(nav)