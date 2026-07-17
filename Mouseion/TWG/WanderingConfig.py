#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from __init__ import app
import os



class Config(object):
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
    IMAGE_FOLDER = os.path.join(app.root_path, 'static', 'images')  # "/static/images/"
    ALLOW_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'txt', 'rtf', 'odf', 'pdf'}
    MAX_CONTENT_LENGTH = 50 * 1024 ** 2
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'phpmyadmin'
    MYSQL_PASSWORD = 'SriLanka65'
    MYSQL_DB = 'TWGdb'
    MYSQL_USE_UNICODE = True
    SECRET_KEY = b'#H%*&H#Rww3r4h'
    CKEDITOR_PKG_TYPE = 'full'
    CKEDITOR_SERVE_LOCAL = True
    CKEDITOR_HEIGHT = 900

    pass