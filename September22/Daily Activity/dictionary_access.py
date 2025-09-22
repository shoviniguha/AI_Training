student={
    "name":"Shovini",
    "age":22,
    "course":"AI-ML"
}
print(student['name'])
print(student.get('age'))

student['grade']='A'#adding new k-v pair
student['age']=19 #updating k-v pair
print(student)

student.pop('course')  #removing by key
del student['grade']   #delete key
print(student)

for key,value in student.items():
    print(key,':',value)