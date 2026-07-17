#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from flask import Flask, session
from flask_mysqldb import MySQL
from flask_menu import Menu
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_login import LoginManager
# from flask_admin.contrib.fileadmin import BaseView
import os

app = Flask(__name__)

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

app.config.from_object(Config)

menu = Menu(app)
mysql = MySQL(app)
ckeditor = CKEditor(app)
bootstrap = Bootstrap(app)


# SESSION_TYPE = 'redis'

# set optional bootswatch theme
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
#
# admin = Admin(app, name='The Wandering God', template_mode='bootstrap3')
# # add admin views here
# # admin.add_view(ModelView(User, db.session))
# # admin.add_view(ModelView(Post, db.session))
#
# login_manager = LoginManager()
# login_manager.init_app(app)

# app.add_url_rule

from WanderingRoutes import *


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)