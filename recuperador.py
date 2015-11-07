#!/usr/bin/env python
# -*- coding: utf-8 -*-

## AUTOR: CARLOS MILLÁN SOLER ##


###########################################################################
############################## DECLARACIONES ##############################
###########################################################################


import re
import sys
import math
import codecs
try:
	import cPickle as pickle
except:
	import pickle

from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer



if len(sys.argv) != 2:
    print "\nUso: recuperador.py <rutaIndice>\n"
    sys.exit(1)

rutaIndices = sys.argv[1]

stemmer = SnowballStemmer('spanish')

stopwords = [p.decode('utf-8') for p in stopwords.words('spanish')]

OPERACIONES = tuple("AND OR NOT".split())
PREFIJOS = tuple("headline: text: category: date:".split())


###########################################################################
################################ FUNCIONES ################################
###########################################################################


## Guarda en disco un objeto dado ##
def cargar_objeto(fichero):
	with open(fichero, 'rb') as fh:
		indices = pickle.load(fh)
	return indices

## Devuelve el primer y segundo elemento de cada tupla de una lista de tuplas ##
def acortaLista(lista):
    return [(e[0], e[1]) for e in lista]

## Calcula la intersección de una lista de términos de un diccionario ##
def interseccion(lista, dicc):
    if len(lista) == 1:
        return acortaLista(dicc[lista[0]]) \
		if dicc.has_key(lista[0]) else []
    else:
        res = acortaLista(dicc[lista[0]]) \
        if dicc.has_key(lista[0]) else []

        if len(res) == 0: return res

        for palabra in lista:
            if not dicc.has_key(palabra): return []

            aux = [tupla for tupla in acortaLista(dicc[palabra])]

            res = list(set(aux) & set(res))

        return res

## Calcula la unión de una lista de término en un diccionario ##
def union(lista, dicc):
    if len(lista) == 1:
        return acortaLista(dicc[lista[0]]) \
		if dicc.has_key(lista[0]) else []

    else:
        res = []

        for palabra in lista:
            if dicc.has_key(palabra):
                tuplas = [tupla for tupla in acortaLista(dicc[palabra])]

            for tupla in tuplas:
                res.append(tupla)

        return list(set(res))

## Calcula la intersección de una lista de tuplas ##
def interseccTuplas(listaS):
    res = listaS[0]

    for lista in listaS:
        res = list(set(lista) & set(res))

    return res

## Calcula la unión de una lista de stems en un diccionario ##
def unionStems(listaS, dicc):
    res = []

    for stem in listaS:
        if dicc.has_key(stem):
            entrada = dicc[stem]
            tuplas = [tupla for tupla in acortaLista(entrada)]
            res = list(set(res) | set(tuplas))

    return res

## Calcula el complementario de un término en un diccionario ##
def complementario(termino, dicc):
    total = []

    for lista in dicc.values():
        for tupla in lista:
            total.append((tupla[0], tupla[1]))

    total = set(total)

    valorT = set(acortaLista(dicc[termino])) if dicc.has_key(termino) else set([])

    return list(total - valorT)

## Calcula el complementario de un término dados sus valores en un diccionario ##
def complementarioP(postings, dicc):
    total = []

    for lista in dicc.values():
        for tupla in lista:
            total.append((tupla[0], tupla[1]))

    total = set(total)

    return list(total - set(postings))

## Calcula la intersección de dos listas de valores ##
def interseccionL(listaP, listaS):
    return list(set(listaP) & set(listaS))

## Calcula la unión de dos listas de valores ##
def unionL(listaP, listaS):
    return list(set(listaP) | set(listaS))

## Devuelve el correspondiente diccionario dado un prefijo ##
def recuperaDicc(dicc):
    if dicc == 'headline:': return titulosDicc
    elif dicc == 'category:': return categoriasDicc
    elif dicc == 'date:': return fechasDicc
    elif dicc == 'text:': return cuerpoDicc

## Ordena una lista de tuplas siguiendo el esquema del log-pesado ##
def ordenaRelevancia(res, terms):
    aux = []

    for tupla in res:
        puntos = 0

        for termino in terms:
            if termino[0] in recuperaDicc(termino[1]):
                entrada = recuperaDicc(termino[1])[termino[0]]

                for valor in entrada:
                    if docNot(valor) == tupla and termino[1] in ['headline:', 'text:']:
                        puntos += 1 + math.log(len(valor[2]))
                        break

            elif len(termino[0].split()) > 1:
                cons = sacaValores(termino[0].split(), termino[1])
                puntos += 1 + math.log(len(cons))

        aux.append((puntos, tupla[0], tupla[1]))

    return sorted(aux, reverse=True)

## Devuelve el snippet en un texto de una lista de palabras ##
def snippet(cuerpo, palabras):
    res = ''
    pCuerpo = [palabra[0] for palabra in palabras if palabra[0] in cuerpo.lower()]

    for p in pCuerpo:
        index = cuerpo.lower().find(p)
        indices = [m.start() for m in re.finditer(p, cuerpo)]

        for indice in indices:
            palabra = cuerpo[indice : len(p)+indice]

            if not cuerpo[indice-1].isalnum() and not cuerpo[indice+len(p)+1].isalnum():
                index = indice

        i = index
        while cuerpo[i] != '.':
            i -= 1

        j = index
        while cuerpo[j] != '.':
            j += 1

        res += '[...] ' + cuerpo[i+1:j] + ' [...]\n' if cuerpo[i+1:j] not in res else ''

    return res

## Recupera el texto comprendido entre dos palabras ##
def subcadena(cadena, pI, pF):
    return cadena[cadena.find(pI)+len(pI):cadena.find(pF)]

## Dada una tupla recupera la noticia corrspondiente de disco ##
def extraeNoticia(docNot):
    documento = codecs.open(docID[docNot[1]], 'r', 'utf-8').read()

    noticias = documento.split('<DOC>')
    noticias.pop(0)

    noticia = noticias[docNot[2]][:-8]

    titulo = subcadena(noticia, '<TITLE>', '</TITLE>')
    texto = subcadena(noticia, '<TEXT>', '</TEXT>')

    return (titulo, texto)

## Imprime los resultados obtenidos ##
def imprimir(res, talla, listaQ):
    i = 0

    if talla != 0:
        for tupla in res:
            noticia = extraeNoticia(tupla)

            print '--------------------------------------------------'
            print "Fichero:", docID[tupla[1]], '\tPuntuación:', tupla[0]
            print '\n', noticia[0]

            if talla < 3:
                print '\n', noticia[1]

            elif talla < 6:
                print snippet(noticia[1], listaQ)

            else:
                if i == 10: break
                i += 1

    if talla == 1:
        print '\n', talla, "noticia relevante recuperada"
    else:
		print '\n', talla, "noticias relevantes recuperadas"

## Aplica las operaciones del query a los valores de los términos del query ##
def computa(listaTerms, listaOPS):
    if len(listaOPS) == 0: return listaTerms[0] if len(listaTerms) > 0 else []

    res = []

    i = 0

    longitud = len(listaTerms)

    for operacion in listaOPS:
        primero = listaTerms.pop(0)
        segundo = listaTerms.pop(0)

        if operacion == 'AND':
            computacion = interseccionL(primero, segundo)
        elif operacion == 'OR':
            computacion = unionL(primero, segundo)

        res = computacion
        listaTerms.insert(0, res)

    return res

## Devuelve el primer y segundo elemento de una tupla (doc, noticia) ##
def docNot(lista):
    return (lista[0], lista[1])

## Calcula las noticias en las que aparecen una serie de términos consecutivos ##
def consecutivos(listaT, dicc):
    i = 0
    posP = 0

    listaN = []

    while i < len(listaT):
        if not dicc.has_key(listaT[i]): return []
        listaN.append((listaT[i], posP))
        posP += 1
        i += 1

    intersecc = []

    if stemming:
        aux = []

        for e in listaN:
            stem = stemmer.stem(e[0])
            unionS = unionStems(stems[stem], dicc)
            aux.append(unionS)

        intersecc = interseccTuplas(aux)

    else:
        intersecc = interseccion([e[0] for e in listaN], dicc)

    res = []

    for tupla in intersecc:
        resTupla = []

        for entrada in listaN:
            if stemming:
                stem = stemmer.stem(entrada[0])
                posicionesS = []

                for s in stems[stem]:
                    if dicc.has_key(s):
                        valor = dicc[s]

                        for resultado in valor:
                            if docNot(resultado) == tupla:
                                for posicion in resultado[2]:
                                    posicionesS.append(posicion)

                resTupla.append(posicionesS)

            else:
                valor = dicc[entrada[0]]

                for resultado in valor:
                    if docNot(resultado) == tupla:
                        resTupla.append(resultado[2])

        if len(resTupla) == len(listaN):
            posiciones = resTupla[0]

            for pos in posiciones:
                i = 0
                continua = True

                for elemento in listaN:
                    suma = elemento[1]
                    if pos + suma not in resTupla[i]:
                        continua = False

                    i += 1

                if continua and tupla not in res:
                    res.append(tupla)

    return res

## Devuelve los valores de un término en un diccionario ##
def valoresT(termino, dicc, esComplementario):
    if stemming:
        stem = stemmer.stem(termino[0])

        if stems.has_key(stem):
            return unionStems(stems[stem], dicc) if not esComplementario \
		    else complementarioP(union(stems[stem], dicc), dicc)
        else:
            return []

    else:
        if esComplementario:
            return complementario(termino[0], dicc)
        else:
            return acortaLista(dicc[termino[0]]) \
	        if len(termino) > 0 and dicc.has_key(termino[0]) else []

## Distingue entre términos consecutivos o un solo término para calcular sus valores ##
def sacaValores(listaT, dicc, complementario=False):
    diccionario = cuerpoDicc
    res = []

    diccionario = recuperaDicc(dicc)

    return consecutivos(listaT, diccionario) if len(listaT) > 1 \
	else valoresT(listaT, diccionario, complementario)

## Método principal para tratar la query ##
def trataConsulta(listaQ):
    global stop
    global stemming

    if "STOPWORDS" in listaQ:
        stop = True
        listaQ.pop(listaQ.index('STOPWORDS'))

    if "STEMMING" in listaQ:
        stemming = True
        listaQ.pop(listaQ.index('STEMMING'))

    operaciones = []
    valores = []
    consulta = []
    termsConsulta = []

    i = 0

    while i < len(listaQ):
        terminos = []
        termino = listaQ[i]

        esStop = False

        if stop:
            pref = 0

            for prefijo in PREFIJOS:
                if termino.startswith(prefijo):
                    pref = len(prefijo)

            if termino[pref:] in stopwords:
                esStop = True
                if i == 0:
                    i += 1

                elif len(operaciones) > 0:
                    operaciones.pop()

        if termino in OPERACIONES:
            if termino == 'NOT' and listaQ[i-1] not in OPERACIONES:
                operaciones.append("AND")

            operaciones.append(termino)

        elif not esStop:
            pref = ''
            diccionario = 'text:'

            for prefijo in PREFIJOS:
                if termino.startswith(prefijo):
                    pref = prefijo
                    diccionario = prefijo
                    break

            termino = termino[len(pref) : ].lower()

            terminoC = termino[1 : ] if termino.startswith('"') else termino

            if termino.startswith('"'):
                terminos.append(termino[1 : ])
                consulta.append(termino[1 : ])

                while True:
                    i += 1
                    siguiente = listaQ[i]

                    if siguiente.endswith('"'):
                        terminos.append(siguiente[ : -1])
                        consulta.append(siguiente[ : -1])
                        terminoC += ' ' + siguiente[ : -1]
                        break
                    else:
                        terminos.append(siguiente)
                        consulta.append(siguiente)
                        terminoC += ' ' + siguiente

            else:
                terminos.append(termino)
                consulta.append(termino)

            termsConsulta.append((terminoC, diccionario))

            if len(operaciones) > 0 and operaciones[-1].endswith("NOT"):
                valores.append(sacaValores(terminos, diccionario, True))
                operaciones.pop(-1)
            else:
                valores.append(sacaValores(terminos, diccionario))

        i += 1

    i = 0
    elemNOT = ''

    for elemento in listaQ:
        if elemento == 'NOT':
            elemNOT = listaQ[i+1]
        i += 1

    for tupla in termsConsulta:
        if tupla[0] in elemNOT:
            termsConsulta.pop(termsConsulta.index(tupla))

    return valores, operaciones, termsConsulta


###########################################################################
################################## MAIN ###################################
###########################################################################


print "Cargando índice..."

#   0          1            2             3           4         5
#(docID, fechasDicc, categoriasDicc, titulosDicc, cuerpoDicc, stems)#
indices = cargar_objeto(rutaIndices)

docID = indices[0]
fechasDicc = indices[1]
categoriasDicc = indices[2]
titulosDicc = indices[3]
cuerpoDicc = indices[4]
stems = indices[5]

print "Ok!"

while True:
    stop = False
    stemming = False

    query = raw_input("\nConsulta: ").decode('utf-8')

    if query == '': break

    print ''

    terminos, operaciones, consulta = trataConsulta(query.split())

    resultado = computa(terminos, operaciones)

    imprimir(ordenaRelevancia(resultado, consulta), len(resultado), consulta)
