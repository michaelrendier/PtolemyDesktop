#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
# from flask_mysqldb import MySQL
from __init__ import app, mysql
import os
from PIL import Image, ImageFont, ImageDraw

# mysql = MySQL(app)

def get_article(title=None, featured=None):
    cur = mysql.connection.cursor()
    if featured:
        cur.execute(f"SELECT * FROM `TWGdb`.`articles` WHERE `articleFeatured` = 1")
        rows = list(map(list, cur.fetchall()))
        for row in rows:
            row[9] = row[9].replace("\r\n", r"<br>").replace("\n", r"<br>")
        featured = None
        return rows

    cur.execute(f"SELECT * FROM `TWGdb`.`articles` WHERE `articleName` = '{title}'")
    row = list(cur.fetchone())
    row[9] = row[9].replace("\r\n", r"<br>")
    return row

def get_herbs():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `TWGdb`.`herbs`")
    rows = list(map(list, cur.fetchall()))
    return rows

def get_herb(name):
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM `TWGdb`.`herbs` WHERE `herbName` = '{name}'")
    row = list(cur.fetchone())
    return row

def get_new_article_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `TWGdb`.`articles`")
    rows = cur.fetchall()
    newId = rows[-1][0] + 1

    return newId

def build_titles(group=None, featured=None):
    titles = []
    cur = mysql.connection.cursor()

    # print(rows)
    # print("THESE", rows[0][5].lower().replace(' ', '-'), rows[0][6].lower().replace(' ', '-'))
    if group:
        group = group.replace("-", " ").title()
        # print("GROUP:\n", group)
        sql = f"SELECT * FROM `TWGdb`.`articles` WHERE `articleCategory` = '{group}' OR `articleCategoryParent` = '{group}'"
        # print("SQL:\n", sql)
        cur.execute(sql)
        rows = list(map(list, cur.fetchall()))
        # print("ROWS:\n", rows)
        titles = [[i[7], i[1]] for i in rows if i[5] == f"{group}" or i[6] == f"{group}"]
    else:
        cur.execute(f"SELECT * FROM `TWGdb`.`articles`")
        rows = list(map(list, cur.fetchall()))
        titles = [[i[7], i[1]] for i in rows]
    # print(titles)
    return titles

def list_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `TWGdb`.`categories`")
    categories = list(map(list, cur.fetchall()))

    return categories

def build_categories():
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * from `TWGdb`.`categories`")
    rows = list(map(list, cur.fetchall()))
    # print("ROWS", rows)
    categories = make_category_tree(rows[1:])
    # print("CATEGORIES\n", categories)

    return categories

def make_category_tree(list_child_parent):
    has_parent = set()
    all_items = {}
    for _, child, parent in list_child_parent:
        if parent not in all_items:
            all_items[parent] = {}
        if child not in all_items:
            all_items[child] = {}
        all_items[parent][child] = all_items[child]
        has_parent.add(child)

    result = {}
    for key, value in all_items.items():
        if key not in has_parent:
            result[key] = value
    return result

def print_categories(dictObj, parent, htmlList):
    if len(dictObj):
        # print(f"<ul>")
        # htmlList.append("<ul>")
        for k,v in dictObj.items():
            # print(f"<li><a href='/categories/{k}' id='{k}-{parent}'>{k}</a></li>")
            string = f"<li style='font-size: small;'><a href='/articles/{k.lower().replace(' ', '-')}' id='{k}-{parent}'>{k}</a></li>"
            htmlList.append(string.replace("{", "{{").replace("}", "}}"))
            print_categories(v, k, htmlList)
        # print(f"</ul>")
        # htmlList.append("</ul>")

def create_error_graphix(error):

    err = f"{error.code}: {error.name}"
    img = Image.new('RGBA', (len(err) * 19, 55), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(os.path.join(app.root_path, 'static', 'fonts', 'Machinegun.ttf'), 24)
    draw.text((5, 23), err, font=font)

    img.save(os.path.join(app.root_path, 'static', 'images', 'error', f"error_{error.code}.png"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['allowedExtensions']

def print_request(request):
    print(request.data)
    print(request.args)
    print(request.files)
    print(request.values)
    print(request.json)