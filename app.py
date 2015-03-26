'''
TODO
- disable availabilities with appointments for students
- limit events by date range
- timezone concerns - user awareness (is calendar in GMT?)
- performance concerns
- handle colors client side
- don't change the past, marty
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
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()
    g.db.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def get_teachers():
    cur = g.db.execute("select id, name from teachers")
    return [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

def get_students():
    cur = g.db.execute("select id, name from students")
    return [dict(id=row[0], name=row[1]) for row in cur.fetchall()]

def event_data_from_row(row, current_student_id):
    if current_student_id is not None:
        current_student_id = int(current_student_id)
    event = { 'start': row['start_time'], 'title': row['teacher_name'], 'color': '#3a87ad' }
    mine = row['student_id'] is not None and row['student_id'] == current_student_id

    if mine:
        if int(row['missing_teacher']) == 1:
            event['title'] = 'CANCELLED ({0})'.format(row['teacher_name'])
            event['color'] = 'red'
        else:
            event['color'] = 'green'
    else:
        if row['student_id'] is not None:
            event['color'] = '#eee'

    return event

def teacher_event_data_from_row(row):
    event = { 'start': row['start_time'], 'title': 'available', 'color': '#3a87ad' }

    if row['student_name'] is not None:
        event['title'] = row['student_name']
        event['color'] = 'green'

    if int(row['missing_teacher']) == 1:
        event['color'] = 'red'

    return event

def unix_to_dbtime(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(t)))

@app.route("/")
def show_student():
    return render_template("student.html", students=get_students(), teachers=get_teachers())

@app.route("/teacher")
def show_teacher():
    return render_template("teacher.html", teachers=get_teachers())

@app.route("/events")
def list_events():
    cur = g.db.execute("""
select availabilities.start_time, teachers.id as teacher_id, teachers.name as teacher_name,
       students.id as student_id, students.name as student_name, 0 as missing_teacher
from availabilities
    join teachers
        on teachers.id = availabilities.teacher_id
    left join appointments
        on appointments.teacher_id = availabilities.teacher_id
        and appointments.start_time = availabilities.start_time
    left join students on students.id = appointments.student_id
    where teachers.id = ?
union all
select appointments.start_time, teachers.id as teacher_id, teachers.name as teacher_name,
       students.id as student_id, students.name as student_name, 1 as missing_teacher
from appointments
    join students
        on students.id = appointments.student_id
    join teachers
        on teachers.id = appointments.teacher_id
    left join availabilities
        on appointments.teacher_id = availabilities.teacher_id
        and appointments.start_time = availabilities.start_time
    where students.id = ?
        and teachers.id = ?
        and availabilities.teacher_id is null
        """, [request.args['teacher_id'], request.args['student_id'], request.args['teacher_id']])
    events = [event_data_from_row(row, request.args['student_id']) for row in cur.fetchall()]
    return json.dumps(events)

@app.route("/teacher_events")
def list_events_for_teacher():
    cur = g.db.execute("""
select availabilities.start_time, teachers.id as teacher_id, teachers.name as teacher_name,
       students.id as student_id, students.name as student_name, 0 as missing_teacher
from availabilities
    join teachers
        on teachers.id = availabilities.teacher_id
    left join appointments
        on appointments.teacher_id = availabilities.teacher_id
        and appointments.start_time = availabilities.start_time
    left join students on students.id = appointments.student_id
    where teachers.id = ?
union all
select appointments.start_time, teachers.id as teacher_id, teachers.name as teacher_name,
       students.id as student_id, students.name as student_name, 1 as missing_teacher
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
    events = [teacher_event_data_from_row(row) for row in cur.fetchall()]
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
