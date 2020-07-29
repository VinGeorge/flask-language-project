from flask import Flask, render_template, request  # сперва подключим модуль
import json
import os
import random
import phonenumbers
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField
import flask_sqlalchemy
import flask_migrate


app = Flask(__name__)  # объявим экземпляр фласка
app.secret_key = "randomstring"
teachers_file = 'data/teachers.json'
goals_file = 'data/goals.json'

with open(teachers_file) as f:
   teachers = json.load(f)

with open(goals_file) as f:
   goals = json.load(f)


weekday_names = \
    {
        "mon": "Понедельник",
        "tue": "Вторник",
        "sun": "Воскресенье",
        "sat": "Суббота",
        "fri": "Пятница",
        "thu": "Четверг",
        "wed": "Среда"
    }

goal_icons = \
    {
        "travel": '⛱',
        "study": '🏫',
        "work": '🏢',
        "relocate": '🚜'
    }

request_times = \
    {
        "s": "1-2 часа в неделю",
        "m": "3-5 часа в неделю",
        "l": "5-7 часа в неделю",
        "xl": "7-10 часа в неделю"
    }

# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///language.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = flask_sqlalchemy.SQLAlchemy(app)
migrate = flask_migrate.Migrate(app, db)

goals_asso = db.Table('goals_asso',
                      db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id')),
                      db.Column('goal_id', db.Integer, db.ForeignKey('goals.id'))
                      )

class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    about = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float)
    price = db.Column(db.Integer, nullable=False)
    picture = db.Column(db.String, nullable=False)
    goals = db.relationship('Goal',
                            secondary=goals_asso,
                            back_populates='teachers')

class Goal(db.Model):
    __tablename__ = 'goals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    users_name = db.Column(db.String, nullable=False)
    picture = db.Column(db.String, nullable=False)
    requests = db.relationship('Request')
    teachers = db.relationship('Teacher',
                            secondary=goals_asso,
                            back_populates='goals')


class Request(db.Model):
    __tablename__ = 'requests'

    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String, nullable=False)
    students = db.relationship('Student')
    goals = db.relationship('Goal')
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    phone = db.Column(db.String, nullable=False)
    requests = db.relationship('Request')
    classes = db.relationship('Class')


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    teachers = db.relationship('Teacher')
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    students = db.relationship('Student')
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    calendar = db.relationship('Calendar')
    calendar_id = db.Column(db.Integer, db.ForeignKey("calendar.id"))


class Calendar(db.Model):
    __tablename__ = 'calendar'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=True)
    users_name = db.Column(db.String, nullable=True)
    time = db.Column(db.String, nullable=True)
    classes = db.relationship('Class')
    schedule = db.relationship('Schedule')


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_avalible = db.Column(db.Boolean, nullable=False)
    teachers = db.relationship('Teacher')
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"))
    calendar = db.relationship('Calendar')
    calendar_id = db.Column(db.Integer, db.ForeignKey("calendar.id"))


def import_goals():
    for name, users_name in goals.items():
        db.session.add(
            Goal(
                name=name,
                users_name=users_name,
                picture=goal_icons[name]
            )
        )
    db.session.commit()


def import_teachers():

    for teacher in teachers:
        new_teacher = Teacher(
                name=teacher['name'],
                about=teacher['about'],
                rating=teacher['rating'],
                price=teacher['price'],
                picture=teacher['picture']
        )
        db.session.add(new_teacher)
        for goal in teacher['goals']:
            new_goal = Goal.query.filter(Goal.name == goal).first()
            new_goal.teachers.append(new_teacher)


def import_calendar():
    for day, times in teachers[1]['free'].items():
        for time in times:
            db.session.add(Calendar(
                name=day,
                users_name=weekday_names[day],
                time=time
            )
            )
    db.session.commit()



# db.create_all()


class BookingForm(FlaskForm):
    student_name = StringField("Ваше имя")
    student_phone = StringField("Ваш телефон")
    clientWeekday = HiddenField("clientWeekday")
    clientTeacher = HiddenField("clientTeacher")
    clientTime = HiddenField("clientTime")

class RequestForm(FlaskForm):
    student_name = StringField("Ваше имя")
    student_phone = StringField("Ваш телефон")
    student_goal = RadioField('Ваша цель', choices=[(key, value) for key, value in goals.items()])
    student_available_time = RadioField('Доступное время', choices=[(key, value) for key, value in request_times.items()])

# Создаем страницы

@app.route('/')
def main():

    teachers_id = [teacher['id'] for teacher in teachers]
    random_id_list = random.choices(teachers_id, k=6)

    random_teacher = [teacher for teacher in teachers if teacher['id'] in random_id_list]

    return render_template('index.html', goals=goals, icons=goal_icons, teachers=random_teacher)


@app.route('/teachers/')
def render_teachers():

    return render_template('index.html', goals=goals, icons=goal_icons, teachers=teachers)


@app.route('/profiles/<int:teacher_id>/')
def render_profiles(teacher_id):

    for teacher in teachers:
        if teacher['id'] == teacher_id:

            teacher_name = teacher['name']
            teacher_about = teacher['about']
            teacher_rating = teacher['rating']
            teacher_picture = teacher['picture']
            teacher_price = teacher['price']
            teacher_goals = teacher['goals']
            schedule = teacher['free']


    return render_template('profile.html', teacher_id=teacher_id, name=teacher_name, about=teacher_about, rating=teacher_rating,
                           picture=teacher_picture, price=teacher_price, teacher_goals=teacher_goals,
                           main_goals=goals, schedule=schedule, weekday_names=weekday_names)

@app.route('/goals/<goal>/')
def render_goals(goal):

    teachers_list = [teacher for teacher in teachers if goal in teacher['goals']]

    return render_template('goal.html', icons=goal_icons, goal=goal, goals=goals, teachers=teachers_list)

@app.route('/request/')
def render_request():

    form = RequestForm()

    return render_template("request.html", form=form)

@app.route('/request_done/', methods=["POST", "GET"])
def render_request_done():

    form = RequestForm()

    if request.method == 'POST':

        form = RequestForm()

        goal = form.student_goal.data
        time = form.student_available_time.data
        name = form.student_name.data
        parsed_phone = phonenumbers.parse(form.student_phone.data, 'RU')
        formated_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        with open("requests.json", "w") as f:
            json.dump([name, formated_phone, time, goal], f)

    return render_template("request_done.html", request_times=request_times, form=form, goal=goal, time=time, name=name, phone=formated_phone, goals=goals)

@app.route('/booking/<int:teacher_id>/<week_day>/<time>/')
def render_booking(teacher_id, week_day, time):

    form = BookingForm(clientWeekday=week_day, clientTeacher=teacher_id, clientTime=time)

    for teacher in teachers:
        if teacher['id'] == teacher_id:

            teacher_name = teacher['name']
            teacher_picture = teacher['picture']
            schedule = teacher['free']


    return render_template("booking.html", form=form, teacher_name=teacher_name, teacher_picture=teacher_picture,
                           schedule=schedule, week_day=week_day, time=time, weekday_names=weekday_names)


@app.route('/booking_done/', methods=["POST", "GET"])
def render_booking_done():

    if request.method == 'POST':

        form = BookingForm()

        name = form.student_name.data
        parsed_phone = phonenumbers.parse(form.student_phone.data, 'RU')
        formated_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        with open("data/booking.json", "w") as f:
            json.dump([name, formated_phone, form.clientWeekday.data, form.clientTime.data], f)

        return render_template("booking_done.html", form=form, weekday_names=weekday_names, name=name, phone=formated_phone)


if __name__ == '__main__':
    import_calendar()
    import_goals()
    import_teachers()
    print(1)
    # app.run()
