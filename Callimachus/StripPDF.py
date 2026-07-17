#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import io

from PyQt6.QtCore import QObject

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage



class PDFStrip(QObject):
	
	def __init__(self, parent):
		super(PDFStrip, self).__init__(parent)
		QObject.__init__(self)
		
	def __del__(self):
		
		pass
	
	def extract_text_by_page(self, pdf_path):
		with open(pdf_path, 'rb') as fh:
			for page in PDFPage.get_pages(fh,
										  caching=True,
										  check_extractable=True):
				resource_manager = PDFResourceManager()
				fake_file_handle = io.StringIO()
				converter = TextConverter(resource_manager, fake_file_handle)
				page_interpreter = PDFPageInterpreter(resource_manager, converter)
				page_interpreter.process_page(page)
				
				text = fake_file_handle.getvalue()
				filetext.append(text)
				text = text.replace("\t", " ")
				yield text
				
				# close open handles
				converter.close()
				fake_file_handle.close()