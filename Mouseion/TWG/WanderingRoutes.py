#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

from flask import Flask, flash, redirect, escape, url_for, request, make_response, render_template_string, render_template, send_from_directory, current_app, g, jsonify, abort


from flask_menu import Menu, register_menu, MenuEntryMixin



from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, gen_salt, check_password_hash
import os, sqlite3, hashlib, datetime
from hashlib import sha256

from __init__ import app, session, mysql

from WanderingForms import ArticleEditorForm, LoginForm, NewUserForm, HerbEditorForm, NewCategoryForm, NewShelfForm
from WanderingFunctions import * # get_article, build_titles, build_categories, make_category_tree, print_categories, create_error_graphix, allowed_file






class User():

    pass

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
# @register_menu(app, '.home', 'Home', order=0)
def index():
    session['CONTENT_PAGE'] = request.url
    if 'username' in session:
        return render_template('neoindex.html', username=session['username'])
    else:
        return render_template('neoindex.html')
    # resp = make_response(render_template('neoindex.html'))
    # resp.set_cookie('username', 'Michael Rendier')
    # print(resp, dir(resp))
    # print(resp.get_json())
    # return resp
    # return render_template('neoindex.html')

@app.route("/login", methods=['GET', 'POST'])
# @register_menu(app, '.login', 'Login', order=1)
def login():
    session['CONTENT_PAGE'] = request.url
    if 'username' in session:
        return redirect(url_for('.index'))

    else:
        if request.method == 'POST':
            userName = request.form['username']
            password = request.form['password']
            hashword = sha256(password.encode()).hexdigest()
            cur = mysql.connection.cursor()
            cur.execute(f"""SELECT * FROM `TWGdb`.`users` WHERE `userName` = '{userName}'""")
            row = cur.fetchone()

            if not row:
                return redirect(url_for('.new_user', uname=userName))

            else:
                if hashword == row[-1]:
                    session['username'] = row[1]
                    session['hashword'] = row[6]
                    session['firstname'] = row[2]
                    session['lastname'] = row[3]
                    session['email'] = row[4]
                    session['usergroup'] = row[5]

                    return redirect(url_for('.index', target='_top'))
            # return do_the_login()
        else:
            print("Howdy!")
            # return show_the_login_form()
            return render_template('login.html', target='_top')

    # return 'login'

@app.route("/logout")
# @register_menu(app, '.logout', 'Logout', order=2)
def logout():
    # remove the username from the sesson if it's there
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('.index'))

@app.route('/debug')
# @register_menu(app, '.debug', 'Debug', order=4)
def print_vars():
    if 'usergroup' in session:
        if session['usergroup'] == 'The Wandering God':
            debugList = [
                f"app.root_path: {app.root_path}",
                f"app.instance_path: {app.instance_path}",
                f"app.static_url_path: {app.static_url_path}",
                f"app.static_folder: {app.static_folder}",
                f"app.url_map: {app.url_map}",
                f"app.config['IMAGE_FOLDER']: {app.config['IMAGE_FOLDER']}",
                f"app.config['UPLOAD_FOLDER']: {app.config['UPLOAD_FOLDER']}",
                f"app.config['ALLOW_EXTENSIONS']: {app.config['ALLOW_EXTENSIONS']}",
                f"app.config: {app.config}",
                f"app.secret_key: {app.secret_key}",
                f"session: {session}",
                f"request: {request}",
                f"g object: {g}"
                # f"current_app.config['DATABASE']: {current_app.config['DATABASE']}"
            ]
            debugList = [i for i in debugList]

            resp = make_response((render_template('debug.html', debugList=debugList)))
            return resp
        else:
            abort(403, description="Forbidden: You are not allowed to access this page.")
    else:
        abort(403, description="Forbidden: You are not allowed to access this page.")

@app.route("/wandering")
# @register_menu(app, '.wanderingg', 'Wandering', order=3)
def wandering():
    session['CONTENT_PAGE'] = url_for('top_page')
    flash('BreadCrumbs')
    if 'username' not in session:
        return redirect(url_for('login'))

    else:
        return render_template('wandering.html')

@app.route('/images/<path:path>')
def send_img(path):
    return send_from_directory('static', 'images/' + path)

@app.route("/menu")
def menu():
    session['MENU_TITLE'] = 'Menu'
    return render_template('menu.html')

@app.route("/top")
def top_page():
    articles = get_article(featured=True)
    for article in articles:
        # print("BEFORE", article[9])
        article[9] = article[9].replace("&rsquo;", "'").replace("&quot;", '"').replace("&amp;rsquo;", "'").replace("&amp;quot;", '"')
        # print("AFTER", article[9])
    return render_template('top.html', articles=articles)

@app.route("/herb/<herbName>")
def show_herb(herbName):
    session['CONTENT_PAGE'] = request.url
    herb = get_herb(herbName)
    return render_template('herb.html', herb=herb)
    pass

@app.route('/herbs')
def list_herbs():
    session["MENU_TITLE"] = "Herbs"
    session['CONTENT_PAGE'] = request.url
    herbs = get_herbs()
    herbs = sorted(herbs, key=lambda herb: herb[1])
    return render_template('herbs.html', herbs=herbs)
    pass

@app.route('/herb_editor/<herbName>', methods=['GET', 'POST'])
def herb_editor(herbName):
    session['CONTENT_PAGE'] = request.url
    form = HerbEditorForm()

    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST' and form.validate_on_submit():
            id = request.form['id']
            Name = request.form['herbName']
            Scientific = request.form['herbScientific']
            Location = request.form['herbLocation']
            Climate = request.form['herbClimate']
            Reference = request.form['herbReferenceLink']
            Images = request.form['herbImages']
            Description = request.form['herbDescription']
            row = [id, Name, Scientific, Location, Climate, Reference, Images, Description]
            try:
                db = mysql.connection
                cur = db.cursor()
                sql = f"UPDATE `TWGdb`.`herbs` SET `herbName`='{row[1]}', `herbScientific`='{row[2]}', `herbLocation`='{row[3]}', `herbClimate`='{row[4]}', `herbReferenceLink`='{row[5]}', `herbImages`='{row[6]}', `herbDescription`='{row[7]}'"
                cur.execute(sql)
                db.commit()
                flash('Herb Saved')

            except Exception as e:
                flash(f"Problem inserting into db: {str(e)}")
                print(f"Problem inserting into db: {str(e)}")

            herb = get_herb(herbName)
            session['CONTENT_PAGE'] = url_for('show_herb', herbName=herb[1])
            return render_template('herb.html', herb=herb)

        else:
            session['CONTENT_PAGE'] = request.url
            herb = get_herb(herbName)
            form.id.data = herb[0]
            form.herbName.data = herb[1]
            form.herbScientific.data = herb[2]
            form.herbLocation.data = herb[3]
            form.herbClimate.data = herb[4]
            form.herbReferenceLink.data = herb[5]
            form.herbImages.data = herb[6]
            form.herbDescription.data = herb[7]
            return render_template('herbeditor.html', form=form)
    pass

@app.route('/herb/new', methods=['GET', 'POST'])
def new_herb():
    session['CONTENT_PAGE'] = request.url
    form = HerbEditorForm()

    if 'username' not in session:
        return redirect(url_for('login'))

    else:
        if request.method == 'POST' and form.validate_on_submit():
            id = request.form['id']
            Name = request.form['herbName']
            Scientific = request.form['herbScientific']
            Location = request.form['herbLocation']
            Climate = request.form['herbClimate']
            Reference = request.form['herbReferenceLink']
            Images = request.form['herbImages']
            Description = request.form['herbDescription']
            row = [id, Name, Scientific, Location, Climate, Reference, Images, Description]
            try:
                db = mysql.connection
                cur = db.cursor()
                row = list(map(str, row))
                sql = """INSERT INTO `TWGdb`.`herbs` (`id`, `herbName`, `herbScientific`, `herbLocation`, `herbClimate`, `herbReferenceLink`, `herbImages`, `herbDescription`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                args = [None, row[1], row[2], row[3], row[4], row[5], row[6], row[7]]
                cur.execute(sql, args)
                db.commit()
                flash('Herb Saved')

            except Exception as e:
                # flash(f"Problem inserting into db: {str(e)}")
                print(f"Problem inserting into db: {str(e)}")
            herbs = get_herbs()
            herbName = herbs[-1][1]
            herb = get_herb(herbName)
            session['CONTENT_PAGE'] = url_for('show_herb', herbName=herb[1])
            return render_template('herb.html', herb=herb)

        else:
            session['CONTENT_PAGE'] = request.url
            herbs = get_herbs()
            nextID = herbs[-1][0] + 1
            form.id.data = nextID

            return render_template('herbeditor.html', form=form)
    pass

@app.route("/article_editor/<articleName>", methods=["GET", "POST"])
def article_editor(articleName):
    session['CONTENT_PAGE'] = request.url
    form = ArticleEditorForm()

    if 'username' not in session:
        return redirect(url_for('login'))

    else:
        if request.method == 'POST' and form.validate_on_submit():
            id = request.form['id']
            Name = request.form['articleName']
            Author = request.form['articleAuthor']
            Date = request.form['articleDate']
            Url = request.form['articleUrl']
            CategoryParent = request.form['articleCategoryParent']
            Category = request.form['articleCategory']
            Title = request.form['articleTitle']
            Intro = request.form['articleIntro'].replace('"', '&quot;').replace("'", '&rsquo;')
            Text = request.form['articleText'].replace('"', '&quot;').replace("'", '&rsquo;')
            Featured = request.form['articleFeatured']
            row = [id, Name, Author, Date, Url, CategoryParent, Category, Title, Intro, Text, Featured]
            try:
                db = mysql.connection
                cur = db.cursor()
                sql = f"""UPDATE `TWGdb`.`articles` SET `articleName`='{row[1]}', `articleAuthor`='{row[2]}', `articleDate`='{row[3]}', `articleUrl`='{row[4]}', `articleCategoryParent`='{row[5]}', `articleCategory`='{row[6]}', `articleTitle`='{row[7]}', `articleIntro`='{row[8]}', `articleText`='{row[9]}', `articleFeatured`={row[10]} WHERE `id`={row[0]}"""
                cur.execute(sql)
                db.commit()
                flash('Article Saved')
            except Exception as e:
                flash(f"Problem inserting into db: {str(e)}")
                print("Problem inserting into db: " + str(e))

            article = get_article(articleName)
            article[9] = article[9].replace("&amp;rsquo;", "'").replace("&amp;quot;", '"').replace("&rsquo;", "'").replace("&quot;", '"')  # .replace('""', '"')
            session['CONTENT_PAGE'] = url_for('read_article', articleName=article[1])
            return render_template('article.html', article=article)
        else:
            session['CONTENT_PAGE'] = request.url
            # print("REQUEST", request.url)
            article = get_article(articleName)
            # print("ARTICLE", article)
            # print("FORM", form)
            # print("CKEDITOR", ckeditor)
            form.id.data = article[0]
            form.articleName.data = article[1]
            form.articleAuthor.data = article[2]
            form.articleDate.data = article[3]
            form.articleUrl.data = article[4]
            form.articleCategoryParent.data = article[5]
            form.articleCategory.data = article[6]
            form.articleTitle.data = article[7]
            form.articleIntro.data = article[8]
            form.articleText.data = article[9].replace("&amp;rsquo;", "'").replace("&amp;quot;", '"').replace("&rsquot;", "'").replace("&quot;", '"')
            form.articleFeatured.data = article[10]
            return render_template('ckeditor.html', form=form)

@app.route('/article/new', methods=['GET', 'POST'])
def new_article(): # add validations TODO
    session['CONTENT_PAGE'] = request.url
    form = ArticleEditorForm()

    if 'username' not in session:
        return redirect(url_for('login'))

    else:
        if request.method == 'POST' and form.validate_on_submit():
            id = request.form['id']
            Name = request.form['articleTitle'].replace(" ", "-").lower()
            Author = request.form['articleAuthor']
            Date = request.form['articleDate']
            Url = request.form['articleUrl']
            CategoryParent = request.form['articleCategoryParent']
            Category = request.form['articleCategory']
            Title = request.form['articleTitle']
            Intro = request.form['articleIntro'].replace('"', '&quot;').replace("'", '&rsquo;')
            Text = request.form['articleText'].replace('"', '&quot;').replace("'", '&rsquo;')
            Featured = request.form['articleFeatured']
            try:
                db = mysql.connection
                cur = db.cursor()
                # sql = f"""UPDATE `TWGdb`.`articles` SET `articleName`='{row[1]}', `articleAuthor`='{row[2]}', `articleDate`='{row[3]}', `articleUrl`='{row[4]}', `articleCategoryParent`='{row[5]}', `articleCategory`='{row[6]}', `articleTitle`='{row[7]}', `articleIntro`='{row[8]}', `articleText`='{row[9]}', `articleFeatured`={row[10]} WHERE `id`={row[0]}"""
                sql = "INSERT INTO `TWGdb`.`articles` (`id`, `articleName`, `articleAuthor`, `articleDate`, `articleUrl`, `articleCategoryParent`, `articleCategory`, `articleTitle`, `articleIntro`, `articleText`, `articleFeatured`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                args = [None, Name, Author, Date, Url, CategoryParent, Category, Title, Intro, Text, Featured]
                cur.execute(sql, args)
                db.commit()
                message = f"Article '{Title}' Saved"
                flash(message)

            except Exception as e:
                flash(f"Problem inserting into db: {str(e)}")
                print("Problem inserting into db: " + str(e))

            article = get_article(Name)
            article[9] = article[9].replace("&amp;rsquo;", "'").replace("&amp;quot;", '"').replace("&rsquo;", "'").replace("&quot;", '"')  # .replace('""', '"')
            session['CONTENT_PAGE'] = url_for('read_article', articleName=article[1])
            return render_template('article.html', article=article)

        else:
            session['CONTENT_PAGE'] = request.url
            # print("REQUEST", request.url)
            newId = get_new_article_id()
            # print("ARTICLE", article)
            # print("FORM", form)
            # print("CKEDITOR", ckeditor)
            form.id.data = newId
            form.articleAuthor.data = session['username']
            form.articleDate.data = datetime.datetime.now().strftime("%a %b %e, %H:%M")

            return render_template('ckeditor.html', form=form)
    pass

@app.route("/article/<articleName>", methods=['GET', 'POST'])
def read_article(articleName):
    session['CONTENT_PAGE'] = request.url
    article = get_article(articleName)
    article[9] = article[9].replace("&amp;rsquo;", "'").replace("&amp;quot;", '"').replace("&rsquo;", "'").replace("&quot;", '"')#.replace('""', '"')
    return render_template('article.html', article=article)

@app.route("/articles/")
def show_articles():
    session['MENU_TITLE'] = 'Articles'
    titles = build_titles()
    return render_template('articles.html', titles=titles)

@app.route("/articles/<category>")
def show_category(category):
    session["MENU_TITLE"] = category.title()
    titles = build_titles(group=category)
    # print("CATEGORY:\n", category)
    # print("TITLES:\n", titles)
    return render_template('articles.html', titles=titles)

@app.route("/categories/")
def show_categories():
    session['MENU_TITLE'] = 'Categories'
    categories = build_categories()
    htmlList = []
    print_categories(categories, 'The Wandering God', htmlList)
    # print("HTMLLIST:\n", htmlList)
    htmlString = '\n'.join(htmlList)
    # print("HTMLSTRING:\n", htmlString)
    return render_template('categories.html', htmlString=htmlString)

@app.route('/category/new', methods=['GET', 'POST'])
def new_category():
    session['MENU_TITLE'] = 'New Category'
    form = NewCategoryForm()
    categories = list_categories()
    # print("CATEGORIES\n", categories)
    form.parentCategory.choices = [(category[1], category[1]) for category in categories]
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST' and form.validate_on_submit():
            newCategory = request.form['newCategory']
            parentCategory = request.form['parentCategory']
            try:
                db = mysql.connection
                cur = db.cursor()
                sql = "INSERT INTO `TWGdb`.`categories` (`id`, `categoryName`, `categoryParent`) VALUES (%s, %s, %s)"
                args = [None, newCategory, parentCategory]
                cur.execute(sql, args)
                db.commit()
                message = f'New Category "{newCategory}"\nParent: "{parentCategory}" Saved'
                flash(message)

            except Exception as e:
                flash(f"Problem inserting into db: {str(e)}")
                print(f"Problem inserting into db: {str(e)}")

            session['CONTENT_PAGE'] = url_for('show_categories')
            categories = build_categories()
            htmlList = []
            print_categories(categories, 'The Wandering God', htmlList)
            # print("HTMLLIST:\n", htmlList)
            htmlString = '\n'.join(htmlList)
            # print("HTMLSTRING:\n", htmlString)
            return render_template('categories.html', htmlString=htmlString)

            pass

        else:
            session['CONTENT_PAGE'] = request.url
            return render_template('cateditor.html', form=form)

@app.route("/library")
def show_library():
    session['MENU_TITLE'] = 'Library'
    # shelves = os.listdir()
    path = '/static/docs/pdfs/'
    bookShelf = sorted(os.listdir(app.root_path + path))
    # print(bookShelf)
    shelves = [shelf for shelf in bookShelf if "." not in shelf]
    # print(shelves)
    books = [path + book for book in bookShelf if book.endswith('.pdf')]
    # print(books)
    return render_template('library.html', books=books, shelves=shelves)

@app.route('/library/<shelf>')
def show_shelf(shelf):
    session['MENU_TITLE'] = shelf
    flash(shelf.capitalize())
    path = f'/static/docs/pdfs/{shelf}/'
    bookShelf = sorted(os.listdir(app.root_path + path))
    books = [path + book for book in bookShelf if book.endswith('.pdf')]
    shelves = [shelf for shelf in bookShelf if "." not in shelf]
    return render_template('library.html', books=books, shelves=shelves, back=True)
    pass

@app.route('/library/new_shelf', methods=['GET', 'POST'])
def new_shelf():
    session['MENU_TITLE'] = 'New Library Shelf'
    form = NewShelfForm()
    if 'username' not in session:
        return redirect(url_for('login'))

    else:
        if request.method == 'POST' and form.validate_on_submit():
            newShelf = request.form['newShelf']
            path = '/static/docs/pdfs/'
            try:
                os.makedirs(app.root_path + path + newShelf)
                message = f"Successfully Created New Shelf:\n{newShelf:^30s}"
                flash(message)

            except Exception as e:
                flash(f'Failed to create new directory:\n{str(e)}')
                print(f'Failed to create new directory:\n{str(e)}')

            session['CONTENT_PAGE'] = url_for('show_library')
            return redirect(url_for('show_library'))

        else:
            session['CONTENT_PAGE'] = request.url
            return render_template('shelfeditor.html', form=form)

@app.route('/upload/book', methods=['GET', 'POST'])
def upload_book():

    pass

@app.route("/upload", methods=["GET", "POST"])
def upload_files():
    if request.method == 'POST':
        # f = request.files['the_file']
        # f.save(os.path.join(app.root_path, 'uploads') + secure_filename(f.filename))
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not selet file, browser also
        # submit an empty part without filename
        if file.filename == "":
            flash('No Selected File')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['uploadFolder'], filename))
            return redirect(url_for('uploaded_file', filename=filename))
    return """
    <!doctype html>
    <title>Upload New File</title>
    <h1>Upload New file</h1>
    <form method=post enctype=multipart/form-data>
        <input type=file name=file>
        <input type=submit value=Upload>
    </form>
    """

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['uploadFolder'], filename)

@app.route("/images/")
def load_image():
    return f"Should be a pic list here:"

@app.route('/projects/')
def projects():

    menu = """
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN">
            <html>
                <head>
                    <title>Michael Rendier: The Wandering God</title>
                    <style type="text/css">
                        <!--
                        body,td,th {
                            color: #FFFFFF;
                        }
                        body {
                            background-color: #000000;
                        }
                        div {
                            background-color: #ffffff;
                        }
                        #menu {
                            width: 250px;
                            height: 100px;
                            color: black;
                            border-width: 1px;
                            border-style: solid;
                            border-color: black;
                        }
                        
                        #logodesc {
                            height:auto;
                            width:auto;
                        }
                        .style1 {font-size: small}
                        
                        .right {
                            text-align: right;
                            float: right;
                        }
                        -->
                    </style>
                </head>
                <body>
                    <div id=menu >
                        The Project Page:
                        <div class='right'>
                            <a href='/projects/hello'>Hello World</a></br>
                            <a href='/projects/herbs'>Herb Database</a>
                        </div>
                    </div>
            """
    return menu

@app.route('/projects/herbs')
def plant_me():
    return '<p align="center" style="color: white;">Plantation Plant Trigun</p>'

@app.route('/user', methods=['GET', 'POST'])
def new_user():
    form = NewUserForm()
    if request.method == 'POST' and form.validate_on_submit():
        details = request.form
        userName = details['uname']
        password = details['passwd']
        password2 = details['passwd2']
        firstName = details['fname']
        lastName = details['lname']
        email = details['email']
        hashword = sha256(password.encode()).hexdigest()
        if password != password2:
            return render_template('user.html', errorMsg="Passwords do not match!")
        cur = mysql.connection.cursor()
        cur.execute(f"""SELECT * FROM `TWGdb`.`users` WHERE `userEmail` = '{email}'""")
        rows = cur.fetchall()
        if len(rows) > 0: # Email exists
            return render_template('user.html', errorMsg=f"Email {email} already exists.")
        cur.execute(f"""SELECT * FROM `TWGdb`.`users` WHERE `userName` = '{userName}""")
        rows = cur.fetchall()
        if len(rows) > 0: # Username exists
            return render_template('user.html', errorMsg=f"Username {userName} already exists.")
        #
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO `TWGdb`.`users` (`id`, `userName`, `userFirstName`, `userLastName`, `userEmail`, `userGroup`, `userPassword`) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (None, userName, firstName, lastName, email, "UNSET", hashword))
        mysql.connection.commit()
        cur.close()
        session['username'] = userName
        session['hashword'] = hashword
        session['firstname'] = firstName
        session['lastname'] = lastName
        session['email'] = email
        return redirect(url_for('.index'))

    else:
        form.userName.data = request.args.get('uname')
        return render_template('user.html', form=form, uname=request.args.get('uname'))

@app.route('/user/<userName>')
def show_user_profile(userName):
    # show the user profile for 'username'
    page = """<!doctype html><title>Hello from Flask</title>{% if userName %}  <h1>Hello {{ userName }}!</h1>{% else %}  <h1>Hello, World!</h1>{% endif %}"""
    resp = make_response(page)
    resp.set_cookie('username', userName)

    return page

@app.errorhandler(HTTPException)
def HTTPError(error):
    create_error_graphix(error)
    return render_template("error/etemplate.html", error=error, root=app.root_path, url=request)


# def get_article(title=None, featured=None):
#     cur = mysql.connection.cursor()
#     if featured:
#         cur.execute(f"SELECT * FROM `TWGdb`.`articles` WHERE `articleFeatured` = 1")
#         rows = list(map(list, cur.fetchall()))
#         for row in rows:
#             row[9] = row[9].replace("\r\n", r"<br>").replace("\n", r"<br>")
#         featured = None
#         return rows
#
#     cur.execute(f"SELECT * FROM `TWGdb`.`articles` WHERE `articleName` = '{title}'")
#     row = list(cur.fetchone())
#     row[9] = row[9].replace("\r\n", r"<br>")
#     return row
#
# def build_titles(group=None, featured=None):
#     titles = []
#     cur = mysql.connection.cursor()
#     cur.execute(f"SELECT * FROM `TWGdb`.`articles`")
#     rows = list(cur.fetchall())
#     # print(rows)
#     # print("THESE", rows[0][5].lower().replace(' ', '-'), rows[0][6].lower().replace(' ', '-'))
#     if group:
#         # print("GROUP:\n", group)
#         titles = [[i[7], i[1]] for i in rows if i[5].lower().replace(' ', '-') == f"{group}" or i[6].lower().replace(' ', '-') == f"{group}"]
#     else:
#         titles = [[i[7], i[1]] for i in rows]
#     # print(titles)
#     return titles
#
#
# def build_categories():
#     cur = mysql.connection.cursor()
#     cur.execute(f"SELECT * from `TWGdb`.`categories`")
#     rows = cur.fetchall()
#     # print("ROWS", rows)
#     categories = make_category_tree(rows[1:])
#     # print("CATEGORIES\n", categories)
#
#     return categories
#
# def make_category_tree(list_child_parent):
#     has_parent = set()
#     all_items = {}
#     for _, child, parent in list_child_parent:
#         if parent not in all_items:
#             all_items[parent] = {}
#         if child not in all_items:
#             all_items[child] = {}
#         all_items[parent][child] = all_items[child]
#         has_parent.add(child)
#
#     result = {}
#     for key, value in all_items.items():
#         if key not in has_parent:
#             result[key] = value
#     return result
#
# def print_categories(dictObj, parent, htmlList):
#     if len(dictObj):
#         # print(f"<ul>")
#         # htmlList.append("<ul>")
#         for k,v in dictObj.items():
#             # print(f"<li><a href='/categories/{k}' id='{k}-{parent}'>{k}</a></li>")
#             string = f"<li style='font-size: small;'><a href='/articles/{k.lower().replace(' ', '-')}' id='{k}-{parent}'>{k}</a></li>"
#             htmlList.append(string.replace("{", "{{").replace("}", "}}"))
#             print_categories(v, k, htmlList)
#         # print(f"</ul>")
#         # htmlList.append("</ul>")
#
# def print_categories_back(dictObj, parent, indent, htmlList):
#     if len(dictObj):
#         # print(f"{'  ' * indent}<ul>")
#         htmlList.append(f"{' ' * indent}<ul>")
#         for k,v in dictObj.items():
#             # print(f"{' ' * (indent+1)}<li><a href='/categories/{k}' id='{k}-{parent}'>{k}</a></li>")
#             htmlList.append(f"{' ' * (indent+1)}<li><a href='categories/{k}' id='{k}-{parent}'>{k}</a></li>")
#             print_categories(v, k, indent+1, htmlList)
#         # print(f"{' ' * indent}</ul>")
#         htmlList.append(f"{'  ' * indent}</ul>")
#
# def create_error_graphix(error):
#
#     err = f"{error.code}: {error.name}"
#     img = Image.new('RGBA', (len(err) * 19, 55), (0, 0, 0, 0))
#     draw = ImageDraw.Draw(img)
#     font = ImageFont.truetype(os.path.join(app.root_path, 'static', 'fonts', 'Machinegun.ttf'), 24)
#     draw.text((5, 23), err, font=font)
#
#     img.save(os.path.join(app.root_path, 'static', 'images', 'error', f"error_{error.code}.png"))
#
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['allowedExtensions']
#
# def print_request(request):
#     print(request.data)
#     print(request.args)
#     print(request.files)
#     print(request.values)
#     print(request.json)


# class CategoryForm(Form):
#
#     category = StringField()
#     pass
# with app.test_request_context():
#     print(url_for('.plant_me'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
