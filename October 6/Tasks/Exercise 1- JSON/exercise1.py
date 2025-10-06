import json
import logging

#configure logging
logging.basicConfig(filename="app.log",
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

#python dictionary
students=[
{"name": "Rahul", "age": 21, "course": "AI", "marks": 85},
{"name": "Priya", "age": 22, "course": "ML", "marks": 90}
]

#write to a json file
with open("students.json",'w') as f:
    json.dump(students,f, indent=4)
logging.info('students.json file created')
#read from json file
with open("students.json",'r+') as f:
    data = json.load(f)
    print(data)
    logging.info('students.json file read successfully')
    new_student={"name": "Arjun", "age": 20, "course": "Data Science", "marks": 78}
    data.append(new_student)
    f.seek(0)
    json.dump(data,f, indent=4)
    logging.info('students.json file updated')
#read from json file
with open("students.json",'r') as f:
    new_data = json.load(f)

print(new_data)
logging.info('students.json file read successfully')