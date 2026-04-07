from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
import sqlite3
connection = sqlite3.connect('portfolios.db', check_same_thread=False)
cursor = connection.cursor()
import uuid
uid = str(uuid.uuid4())
from werkzeug.utils import secure_filename
import requests

tool_icons = {
        "Python":"🐍", "Flask":"🌶️", "HTML":"📄", "CSS":"🎨", "HTML/CSS":"🖌️", "Git":"🔧",
        "GitHub":"🌄", "Telegram":"✈️", "SQL":"🗄️", "SQLite":"📘", "Javascript":"⚡", "JS":"⚡", "Jinja":"🧩"
    }

connection.commit()
@app.route('/')
def index():
    connection = sqlite3.connect('portfolios.db', check_same_thread=False)
    cursor = connection.cursor()
    everything = cursor.execute('select * from portfolio').fetchall()
    print(everything)
    filter_skill = request.args.get('skill')
    portfolios = []
    if filter_skill:
        filter_skill = filter_skill.strip().lower()
    else:
        filter_skill = None
    for _,uuid,name,bio,github,telegram,avatar,skills_str in everything:
        skills=[]
        if skills_str:
            for s in skills_str.split(','):
                s = s.strip()
                if s:
                    skills.append(s)
            skills_lower = []
            for s in skills:
                skills_lower.append(s.lower())
        else:
            skills_lower = []
        if filter_skill is None or filter_skill in skills_lower:
            portfolios.append({
                "name": name, 'bio': bio, 'github': github, 'telegram': telegram,
                'avatar': avatar, 'skills': skills_lower, 'uuid': uuid
            })
    return render_template('all_portfolios.html', portfolios=portfolios, tool_icons=tool_icons, current_skill=filter_skill or '')

@app.route('/form')
def form():
    return render_template("form.html")

@app.route('/generate', methods=['POST'])
def generate():
    form = request.form
    print(form['name'], form['bio'], form['telegram'], form['skills'], form['github'])
    avatar = request.files.get('avatar')
    uid = str(uuid.uuid4())
    avatar_filename = ''
    if avatar and avatar.filename:
        filename = secure_filename(f"{uid}_{avatar.filename}")
        avatar_path = f"static/uploads/{filename}"
        avatar.save(avatar_path)
        avatar_filename = avatar_path.replace("static/", "")
    github = form['github'].strip().replace('https://github.com/', '').replace('/', '')
    cursor.execute('insert into portfolio (uuid, name, bio, github, telegram, avatar, skills) values (?, ?, ?, ?, ?, ?, ?)',
                   (uid, form['name'], form['bio'], github, form['telegram'], avatar_filename, form['skills'])
                   )
    connection.commit()
    connection.close()
    return redirect(url_for('index'))

@app.route('/portfolio/<uuid>', )
def view_portfolio(uuid):

    connection = sqlite3.connect('portfolios.db', check_same_thread=False)
    cursor = connection.cursor()
    row = cursor.execute('select name, bio, github, telegram, avatar, skills from portfolio where uuid = ?', (uuid,)).fetchone()
    connection.close()
    if not row:
        return "Портфолио не найдено", 404
    name, bio, github, telegram, avatar, skills_str = row
    print(row)
    skills = []
    if skills_str:
        for s in skills_str.split(','):
            skills.append(s.strip())
    projects = []
    try:
        r = requests.get(f'https://api.github.com/users/{github}/repos')
        if r.ok :
            for project in r.json()[:6]:
                projects.append({
                    'title':project['name'],
                    'description': project['description'] if project['description'] else 'Without description',
                    'link':project['html_url'],
                })
    except Exception as e:
        print(e)
    return render_template('portfolio_template.html', projects=projects, name=name, bio=bio,
                           tool_icons=tool_icons, github=github, telegram=telegram, avatar=avatar, skills=skills)
if __name__ == "__main__":
    app.run()
