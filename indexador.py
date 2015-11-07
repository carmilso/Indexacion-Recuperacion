#!/usr/bin/env python
# -*- coding: utf-8 -*-

## AUTOR: CARLOS MILLÁN SOLER ##


###########################################################################
############################## DECLARACIONES ##############################
###########################################################################


## 1 para activarlos y 0 para desactivarlos ##
STOPWORDS = 0
STEMMING = 1

import sys
import codecs
from glob import glob
try:
	import cPickle as pickle
except:
	import pickle

if STOPWORDS:
    from nltk.corpus import stopwords
    stopwords = [p.decode('utf-8') for p in stopwords.words('spanish')]
if STEMMING:
    from nltk.stem import SnowballStemmer
    stemmer = SnowballStemmer('spanish')



if len(sys.argv) != 3:
    print("Uso: indexador.py <directorioDocs> <nombreIndice>")
    sys.exit(1)

directorio = sys.argv[1]
indiceNombre = sys.argv[2]

docID = {}
cuerpoDicc = {}
categoriasDicc = {}
titulosDicc	= {}
fechasDicc = {}
stems = {}


###########################################################################
################################ FUNCIONES ################################
###########################################################################


## Recupera el texto comprendido entre dos palabras ##
def subcadena(cadena, pI, pF):
    return cadena[cadena.find(pI)+len(pI):cadena.find(pF)]

## Calcula el stem de una palabra dada y actualiza su entrada en el diccionario ##
def stemiza(palabra):
    stem = stemmer.stem(palabra)

    if not stems.has_key(stem):
        stems[stem] = [palabra]
    elif palabra not in stems[stem]:
        stems[stem].append(palabra)

## Actualiza la entrada de una palabra en su respectivo diccionario ##
def indexaPalabra(dicc, palabra, info, pos=False):
    if STOPWORDS and palabra in stopwords: return

    if not dicc.has_key(palabra):
        if STEMMING: stemiza(palabra)
        dicc[palabra] = [info]
    else:
        if pos:
            lista = dicc[palabra][-1]
            if lista[0] == info[0] and lista[1] == info[1]:
                lista[2].append(info[2][0])
            else:
                dicc[palabra].append(info)
        else:
            dicc[palabra].append(info)
            dicc[palabra] = list(set(dicc[palabra]))

## Normaliza una palabra eliminando los signos de puntuación ##
def trataPalabra(palabra):
    return ''.join([c if c.isalnum() else '' for c in palabra])

## Imprime el progreso de la indexación ##
def progreso(acabados, total):
    print str(acabados*100/total) + "%", '[' + '='*acabados + ' '*(total-acabados) + ']',

## Guarda en disco un objeto dado ##
def guardarObjeto(objeto, fichero):
	with open(fichero, 'wb') as fh:
		pickle.dump(objeto, fh, pickle.HIGHEST_PROTOCOL)


###########################################################################
################################## MAIN ###################################
###########################################################################


d = 0

print ''

docs = glob(directorio+"/*.sgml")
lenDocs = len(docs)

for doc in docs:
    print "\rIndexando", doc + "...",

    docID[d] = doc
    documento = codecs.open(doc, 'r', 'utf-8').read()

    noticias = documento.split('<DOC>')
    noticias.pop(0)

    n = 0

    for noticia in noticias:
        noticia = noticia[:-8]
        noticiaID = (d, n)

        titular = subcadena(noticia, '<TITLE>', '</TITLE>')

        posc = 0
        post = 0

        for palabra in titular.lower().split():
            info = [d, n, [post]]
            indexaPalabra(titulosDicc, trataPalabra(palabra), info, True)
            post += 1

        categoria = subcadena(noticia, '<CATEGORY>', '</CATEGORY>').lower()
        indexaPalabra(categoriasDicc, categoria, noticiaID)

        fecha = subcadena(noticia, '<DATE>', '</DATE>')
        indexaPalabra(fechasDicc, fecha, noticiaID)

        texto = subcadena(noticia, '<TEXT>', '</TEXT>')

        for palabra in texto.lower().split():
            info = [d, n, [posc]]
            sw = indexaPalabra(cuerpoDicc, trataPalabra(palabra), info, True)
            posc += 1

        n += 1

    d += 1

    progreso(d, lenDocs)

indices = (docID, fechasDicc, categoriasDicc, titulosDicc, cuerpoDicc, stems)

guardarObjeto(indices, indiceNombre)

print "\n\nÍndice guardado!\n"
