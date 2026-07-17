#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from __init__ import mysql
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor, CKEditorField
from wtforms import StringField, SubmitField, SelectField, SelectFieldBase, SelectMultipleField, RadioField, BooleanField, DateField, DateTimeField, DecimalField, FileField, FloatField, FormField, HiddenField, IntegerField, MultipleFileField, PasswordField, TextAreaField, TextField, TimeField
from wtforms.widgets import TextArea, PasswordInput, RadioInput, TableWidget, ListWidget, CheckboxInput, Input, TextInput, FileInput, HiddenInput, HTMLString, Option, SubmitInput, Select
from wtforms.validators import Required, DataRequired, InputRequired, URL, IPAddress, MacAddress, NumberRange, Regexp, ValidationError, Email, EqualTo, HostnameValidation, Optional, UUID, Length

# StringField, SubmitField, SelectField, SelectFieldBase,
# SelectMultipleField, RadioField, BooleanField, DateField,
# DateTimeField, DecimalField, FileField, FloatField,
# FormField, HiddenField, IntegerField, MultipleFileField,
# PasswordField, TextAreaField, TextField, TimeField

# TextArea, PasswordInput, RadioInput, TableWidget,
# ListWidget, CheckboxInput, Input, TextInput,
# FileInput, HiddenInput, HTMLString, Option,
# SubmitInput, Select

# Required, DataRequired, InputRequired, URL,
# IPAddress, MacAddress, NumberRange, Regexp,
# ValidationError, Email, EqualTo, HostnameValidation,
# Optional, UUID, Length

class HerbEditorForm(FlaskForm):
    id = StringField('id')
    herbName = StringField('Name')
    herbScientific = StringField('Scientific Name')
    herbLocation = StringField('Location')
    herbClimate = StringField('Climate')
    herbReferenceLink = StringField('Reference Link')
    herbImages = CKEditorField('Images')
    herbDescription = CKEditorField('Description')
    submit = SubmitField('Save')

class ArticleEditorForm(FlaskForm):
    id = StringField('id')
    articleName = StringField('Name')
    articleAuthor = StringField('Author')
    articleDate = StringField('Date')
    articleUrl = StringField('Url')
    articleCategoryParent = StringField('Parent')
    articleCategory = StringField('Category')
    articleTitle = StringField('Title')
    articleIntro = CKEditorField('Intro', validators=[DataRequired()])
    articleText = CKEditorField('Content', validators=[DataRequired()])
    articleFeatured = StringField('Featured')
    submit = SubmitField('Save')

class LoginForm(FlaskForm):
    username = StringField('username')
    password = PasswordField('password')
    login = SubmitField('Login')

class NewUserForm(FlaskForm):
    userName = StringField('uname')
    password = PasswordField('passwd')
    password2 = PasswordField('passwd2')
    firstName = StringField('fname')
    lastName = StringField('lname')
    email = StringField('email')
    submit = SubmitField('Register')

class NewCategoryForm(FlaskForm):
    newCategory = StringField('Category')
    parentCategory = SelectField('Parent')
    submit = SubmitField('Save')

class NewShelfForm(FlaskForm):
    newShelf = StringField('Shelf')
    submit = SubmitField('Create')