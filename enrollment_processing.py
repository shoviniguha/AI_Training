import pandas as pd

students=pd.read_csv("students.csv")
courses = pd.read_csv("courses.csv")
enrollments = pd.read_csv("enrollments.csv")
students_enrollments = pd.merge(students, enrollments, on='StudentID', how='inner')
df=pd.merge(courses, students_enrollments, on='CourseID', how='inner')
df['EnrollDate'] = pd.to_datetime(df['EnrollDate'])
df["EnrollMonth"]=df["EnrollDate"].dt.month
df["CompletionStatus"]=df['Progress'].apply(lambda x: 'Completed' if x >= 80 else 'In Progress')
df.to_csv("processed_enrollments.csv", index=False)