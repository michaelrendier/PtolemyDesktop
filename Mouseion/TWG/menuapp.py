from flask import Flask
from flask import render_template_string
from flask_menu import Menu, register_menu

app = Flask(__name__)
Menu(app=app)

def tmpl_show_menu():
    return render_template_string(
        """
        <ul class="menu">
        {%- for item in current_menu.children %}
            <li>{% if item.active %}*{% endif %}<a href="/{{ item.text|lower }}">{{ item.text }}</a></li>
        {% endfor -%}
        </ul>
        """)

@app.route('/')
@register_menu(app, '.', 'Home', order=0)
def index():
    return tmpl_show_menu()

@app.route('/first')
@register_menu(app, '.first', 'First', order=1)
def first():
    return tmpl_show_menu()

@app.route('/second')
@register_menu(app, '.second', 'Second', order=2)
def second():
    return tmpl_show_menu()

if __name__ == '__main__':
    app.run(debug=True)
