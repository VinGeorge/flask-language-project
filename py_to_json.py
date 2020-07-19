import json
import data


goals = data.goals
teachers = data.teachers


with open('teachers.json', 'w', encoding='utf-8') as f:
    json.dump(teachers, f)

with open('goals.json', 'w', encoding='utf-8') as f:
    json.dump(goals, f)