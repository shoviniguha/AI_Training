import pandas as pd

courses=pd.read_csv('courses.csv')
students= pd.read_csv('students.csv')

#add a new course
courses.loc[len(courses)] =['C105','Basic AI','AI',60]

#update a course duration- changing duration of first course
courses.iloc[0,3]=45

#delete a student- dropping Arjun
students=students.drop(1)

#print students from India
students_india=students[students['Country']=='India']

print(courses)
print(students)
print(students_india)