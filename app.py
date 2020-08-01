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
    schedule = db.relationship('Schedule')
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
    name = db.Column(db.String, nullable=False)
    users_name = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
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

        for day, times in teacher['free'].items():
            for time, value in times.items():
                calendar_params = Calendar.query.filter(db.and_(Calendar.name == day, Calendar.time == time)).first()
                new_reserve = Schedule(is_avalible=value, calendar=calendar_params, teachers=new_teacher)
                db.session.add(new_reserve)

    db.session.commit()



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


def request_frequency():

    for value in request_times.values():
        db.session.add(Request(
            frequency=value
        )
        )
    db.session.commit()

class BookingForm(FlaskForm):
    student_name = StringField("Ваше имя")
    student_phone = StringField("Ваш телефон")
    clientWeekday = HiddenField("clientWeekday")
    clientTeacher = HiddenField("clientTeacher")
    clientTime = HiddenField("clientTime")

class RequestForm(FlaskForm):
    student_name = StringField("Ваше имя")
    student_phone = StringField("Ваш телефон")

    student_goal = RadioField('Ваша цель', choices=[(goal.name, goal.users_name) for goal in Goal.query.all()])
    student_available_time = RadioField('Доступное время', choices=[(item.frequency, item.frequency) for item in Request.query.distinct()])

# Создаем страницы

@app.route('/')
def main():

    goals = [goal for goal in Goal.query.all()]
    teachers_id = [teacher.id for teacher in Teacher.query.distinct()]
    random_id_list = random.choices(teachers_id, k=6)
    random_teachers = [teacher for teacher in Teacher.query.filter(Teacher.id.in_(random_id_list)).all()]

    return render_template('index.html', goals=goals, teachers=random_teachers)


@app.route('/teachers/')
def render_teachers():

    goals = [goal for goal in Goal.query.all()]
    all_teachers = [teacher for teacher in Teacher.query.all()]

    return render_template('index.html', goals=goals, teachers=all_teachers)


@app.route('/profiles/<int:teacher_id>/')
def render_profiles(teacher_id):

    teacher_info = Teacher.query.filter(Teacher.id == teacher_id).first_or_404()

    teacher_goals =  db.session.query(Goal.users_name, Goal.name).select_from(Teacher)\
        .join(goals_asso).join(Goal).filter(Teacher.id==teacher_id).all()

    teacher_avalible_times = db.session.query(Calendar.name, Calendar.users_name, Calendar.time).select_from(Teacher)\
        .join(Schedule).join(Calendar).filter(db.and_(Teacher.id==teacher_id, Schedule.is_avalible==True)).all()

    teacher_avalible_days = set([day.users_name for day in teacher_avalible_times])

    weekdays = Calendar.query.with_entities(Calendar.name, Calendar.users_name).distinct()


    return render_template('profile.html', teacher=teacher_info, teacher_goals=teacher_goals,
                           teacher_shedule=teacher_avalible_times, avalible_days=teacher_avalible_days, weekdays=weekdays)


@app.route('/goals/<goal>/')
def render_goals(goal):

    goals = [goal.name for goal in Goal.query.with_entities(Goal.name).distinct()]

    if goal in goals:
        teachers = [teacher for teacher in Teacher.query.join(goals_asso).join(Goal).filter(Goal.name == goal).all()]
        page_goal = Goal.query.filter(Goal.name == goal).first()
        return render_template('goal.html', goal=page_goal, teachers=teachers)
    else:
        return 'Нет такой цели'


@app.route('/request/')
def render_request():

    form = RequestForm()

    return render_template("request.html", form=form)

@app.route('/request_done/', methods=["POST", "GET"])
def render_request_done():

    form = RequestForm()

    if request.method == 'POST':

        form = RequestForm()

        request_goal = form.student_goal.data
        student_request_time = form.student_available_time.data
        student_name = form.student_name.data
        parsed_phone = phonenumbers.parse(form.student_phone.data, 'RU')
        formated_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        new_request_student = Student(name=student_name,
                                      phone=formated_phone)
        db.session.add(new_request_student)
        new_request_qoal = Goal.query.filter(Goal.name == request_goal).first()
        db.session.add(Request(
            frequency=student_request_time,
            students=new_request_student,
            goals=new_request_qoal
        )
        )
        db.session.commit()

    return render_template("request_done.html", form=form, request_times=student_request_time,
                           student_name=student_name, student_phone=formated_phone, request_goal=new_request_qoal)

@app.route('/booking/<int:teacher_id>/<week_day>/<time>/')
def render_booking(teacher_id, week_day, time):

    form = BookingForm(clientWeekday=week_day, clientTeacher=teacher_id, clientTime=time)

    teacher_info = Teacher.query.join(Schedule).join(Calendar).filter(Teacher.id == teacher_id).first_or_404()


    return render_template("booking.html", form=form, teacher=teacher_info)


@app.route('/booking_done/', methods=["POST", "GET"])
def render_booking_done():

    if request.method == 'POST':

        form = BookingForm()

        booking_student_name = form.student_name.data
        parsed_phone = phonenumbers.parse(form.student_phone.data, 'RU')
        formated_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        booking_info = Teacher.query.join(Schedule).join(Calendar).filter(db.and_(Teacher.name == form.clientTeacher.data,
                                                                                Calendar.users_name == form.clientWeekday,
                                                                                Calendar.time == form.clientTime)).first()

        new_booking_student = Student(name=booking_student_name, phone=formated_phone)


        with open("data/booking.json", "w") as f:
            json.dump([name, formated_phone, form.clientWeekday.data, form.clientTime.data], f)

        return render_template("booking_done.html", form=form, weekday_names=weekday_names, name=name, phone=formated_phone)


if __name__ == '__main__':

    # request_frequency()
    # import_calendar()
    # import_goals()
    # import_teachers()
    app.run(debug=True)

