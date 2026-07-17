#!/usr/bin/python3
# -*- coding: utf-8 -*-
__all__ = []
__version__ = '3.6.6'
__author__ = 'rendier'

import string
import polyglot
from polyglot.text import Text, Word
from polyglot.transliteration import Transliterator

# Language Detection
print("Language Detection")
detect = Text("Bonjour, Mesdames.")
print("Language Detected: Code={}, Name={}\n".format(detect.language.code, detect.language.name))

# Tokenization
print("Tokenization")
token = Text("Beautiful is better than ugly."
		   "Explicit is better than implicit. "
		   "Simple is beter than complex.")
print("Zen Words:", token.words)
print("Zen Sentences:", token.sentences)

# Speech Tagging
print("Part of Speech Tagging")
stagging = Text(u"O primeiro uso de desobediência civil em massa ocorreu em setembro de 1906.")
print("{:<16}{}".format("Word", "POS Tag") + "\n" + "-" * 30)
for word, tag in stagging.pos_tags:
	print(u"{:<16}{:>2}".format(word, tag))
print("Language Detected: Code={}, Name={}\n".format(stagging.language.code, stagging.language.name))

# Named Entity Recognition
print("Named Entity Recognition")
names = Text(u"In Großbritannien war Gandhi mit dem westlichen Lebensstil vertraut geworden")
print(names.entities)
print("Language Detected: Code={}, Name={}\n".format(names.language.code, names.language.name))

# Polarity
print("Polarity")
print("{:<16}{}".format("Word", "Polarity")+"\n"+"-"*30)
for w in token.words[:6]:
	print("{:<16}{:>2}".format(w, w.polarity))
	
# Embeddings
print("Embeddings")
embedded = Word("Obama", language="en")
print("Neighbors (Synonms) of {}".format(word)+"\n"+"-"*30)
for w in embedded.neighbors:
	print("{:<16}".format(w))
print("\n\nThe first 10 dimensions out the {} dimensions\n".format(embedded.vector.shape[0]))
print(word.vector[:10])

# Morphology
print("Morphology")
morph = Text("Preprocessing is an essential step.").words[0]
print("Morphemes:", morph.morphemes)

# Transliteration
print("Transliteration")
transliterator = Transliterator(source_lang="en", target_lang="ru")
print(transliterator.transliterate(token))



			
			