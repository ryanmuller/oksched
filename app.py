'''
TODO
x request and show availabilities
x initiate db
x use db for teachers
x use db for teacher events
x create availabilities from event ranges
x create student page showing availabilities
x click event to create appointment
x show availabilities with appointments
x nicer showing of appointments
x delete availabilities
x show warning for failed appointments
x delete appointments
- handle multiple students
- disable availabilities with appointments for students
- limit events by date range
- timezone concerns
- performance concerns
- handle colors client side
- don't change the past, marty

personal reference...
http://flask-script.readthedocs.org/en/latest/
https://flask-migrate.readthedocs.org/en/latest/
https://pythonhosted.org/Flask-SQLAlchemy/quickstart.html
http://flask.pocoo.org/docs/0.10/tutorial/introduction/
http://flask.pocoo.org/docs/0.10/api/
http://fullcalendar.io/docs/usage/
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

def get_teachers():
    cur = g.db.execute("select id, name from teachers")
    return [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

def event_title(teacher_name, student_name, missing):
    if missing:
        return "{1} (cancelled by {0})".format(teacher_name, student_name)
    elif teacher_name and student_name:
        return "{0} & {1}".format(teacher_name, student_name)
    else:
        return teacher_name

def event_color(scheduled, missing):
    if missing:
        return "red"
    elif scheduled:
        return "green"
    else:
        return "#3a87ad"

def unix_to_dbtime(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(t)))

@app.route("/")
def show_student():
    return render_template("student.html", teachers=get_teachers())

@app.route("/teacher")
def show_teacher():
    return render_template("teacher.html", teachers=get_teachers())

@app.route("/events")
def list_events():
    cur = g.db.execute("""
select availabilities.start_time, teachers.name as teacher_name, students.name as student_name, 0 as missing_teacher_name
from availabilities
    join teachers
        on teachers.id = availabilities.teacher_id
    left join appointments
        on appointments.teacher_id = availabilities.teacher_id
        and appointments.start_time = availabilities.start_time
    left join students on students.id = appointments.student_id
    where teachers.id = ?
union all
select appointments.start_time, teachers.name as teacher_name, students.name as student_name, 1 as missing_teacher_name
from appointments
    join students
        on students.id = appointments.student_id
    join teachers
        on teachers.id = appointments.teacher_id
    left join availabilities
        on appointments.teacher_id = availabilities.teacher_id
        and appointments.start_time = availabilities.start_time
    where teachers.id = ?
        and availabilities.teacher_id is null
        """, [request.args['teacher_id'], request.args['teacher_id']])
    events = [dict(start=row[0], title=event_title(row[1], row[2], row[3] == 1), color=event_color(row[2] is not None, row[3] == 1)) for row in cur.fetchall()]
    return json.dumps(events)

@app.route('/add', methods=['POST'])
def create_availability():
    teacher_id = request.form['teacher_id']
    start_sec = request.form['start_time']
    end_sec = request.form['end_time']
    starts = [time.gmtime(t) for t in range(int(start_sec), int(end_sec), 1800)]
    for start in starts:
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", start)
        g.db.execute('insert into availabilities (teacher_id, start_time) values (?, ?)', [teacher_id, start_time])
    g.db.commit()
    return "OK"

@app.route('/remove', methods=['DELETE'])
def destroy_availability():
    teacher_id = request.form['teacher_id']
    start_time = unix_to_dbtime(request.form['start_time'])
    g.db.execute('delete from availabilities where teacher_id = ? and start_time = ?', [teacher_id, start_time])
    g.db.commit()
    return "OK"

@app.route('/match', methods=['POST'])
def create_appointment():
    student_id = request.form['student_id']
    teacher_id = request.form['teacher_id']
    start_time = unix_to_dbtime(request.form['start_time'])
    g.db.execute('insert into appointments (student_id, teacher_id, start_time) values (?, ?, ?)', [student_id, teacher_id, start_time])
    g.db.commit()
    return "OK"

@app.route('/cancel', methods=['DELETE'])
def destroy_appointment():
    student_id = request.form['student_id']
    start_time = unix_to_dbtime(request.form['start_time'])
    g.db.execute('delete from appointments where student_id = ? and start_time = ?', [student_id, start_time])
    g.db.commit()
    return "OK"

if __name__ == "__main__":
    app.run(debug=True)
