from flask import Flask, render_template  # сперва подключим модуль
import json

app = Flask(__name__)  # объявим экземпляр фласка


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

# Создаем страницы


@app.route('/')
def main():

    return


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
            main_goals = goals
            schedule = teacher['free']


    return render_template('profile.html', name=teacher_name, about=teacher_about, rating=teacher_rating,
                           picture=teacher_picture, price=teacher_price, teacher_goals=teacher_goals,
                           main_goals=main_goals, schedule=schedule, weekday_names=weekday_names)

@app.route('/goals/<goal>/')
def render_goals(goal):
    return

@app.route('/request/')
def render_request():
    return

@app.route('/request_done/')
def render_request_done():
    return

@app.route('/booking/<int:teacher_id>/<week_day>/<time>/')
def render_booking(teacher_id, week_day, time):

    return

@app.route('/booking_done/')
def render_booking_done():
    return


if __name__ == '__main__':
    app.run(debug=True)  # запустим сервер
