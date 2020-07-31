from flask import Flask
import flask_sqlalchemy
import flask_migrate
import json

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
app = Flask(__name__)
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

import_calendar()
import_goals()
import_teachers()