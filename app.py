'''
TODO
x request and show availabilities
x initiate db
x use db for teachers
x use db for teacher events
- create availabilities from event ranges
- create student page showing availabilities
- click event to create appointment
- show/disable (for student) availabilities with appointments
- delete availabilities
- show warning for failed appointments
- delete appointments
- handle multiple students
- timezone concerns
- performance concerns

personal reference...
http://flask-script.readthedocs.org/en/latest/
https://flask-migrate.readthedocs.org/en/latest/
https://pythonhosted.org/Flask-SQLAlchemy/quickstart.html
http://flask.pocoo.org/docs/0.10/tutorial/introduction/
http://flask.pocoo.org/docs/0.10/api/
http://fullcalendar.io/docs/usage/

sqlite3 /tmp/flaskr.db < schema.sql
'''

import sqlite3
import time
from flask import Flask, g, request, session, redirect, url_for, \
    abort, render_template, flash, json, jsonify
from contextlib import closing
from flask.ext.bower import Bower

# configuration (move to file)
DATABASE = 'data/schedule.db'

app = Flask(__name__)
app.config.from_object(__name__)
Bower(app)

def connect_db():
    print app.config['DATABASE']
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route("/")
def show_student():
    return render_template("student.html")

@app.route("/teacher")
def show_teacher():
    cur = g.db.execute("select id, name from teachers")
    teachers = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]
    return render_template("teacher.html", teachers=teachers)

@app.route("/events")
def list_events():
    cur = g.db.execute("""select start_time, teachers.name as teacher_name
                       from availabilities
                       join teachers on teachers.id = availabilities.teacher_id
                       where teachers.id = ?""", request.args['teacher_id'])
    events = [dict(start=row[0], title=row[1]) for row in cur.fetchall()]
    return json.dumps(events)

@app.route('/add', methods=['POST'])
def add_availability():
    teacher_id = request.form['teacher_id']
    start_sec = request.form['start_time']
    end_sec = request.form['end_time']
    starts = [time.gmtime(t) for t in range(int(start_sec), int(end_sec), 1800)]
    for start in starts:
        start_fmt = time.strftime("%Y-%m-%d %H:%M:%S", start)
        g.db.execute('insert into availabilities (teacher_id, start_time) values (?, ?)', [teacher_id, start_fmt])
    g.db.commit()
    return "OK"

if __name__ == "__main__":
    app.run(debug=True)
