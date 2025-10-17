import pandas as pd
import os

students=pd.read_csv("students.csv")
courses = pd.read_csv("courses.csv")
enrollments = pd.read_csv("enrollments.csv")
students_enrollments = pd.merge(students, enrollments, on='StudentID', how='inner')
df=pd.merge(courses, students_enrollments, on='CourseID', how='inner')

df['EnrollDate'] = pd.to_datetime(df['EnrollDate'], errors='coerce')

df['CompletionStatus'] = df['Progress'].apply(lambda x: 'Completed' if x >= 80 else 'In Progress')

df['EnrollMonth'] = df['EnrollDate'].dt.to_period('M')

# --- 1. Completion rate per course ---
completion_counts = df.groupby('Title')['CompletionStatus'].value_counts().unstack(fill_value=0)
completion_counts['CompletionRate (%)'] = (
    completion_counts.get('Completed', 0) / completion_counts.sum(axis=1) * 100
).round(2)
completion_counts.reset_index(inplace=True)

completion_counts.to_csv('reports/completion_rate_per_course.csv', index=False)

# --- 2. Total students per category ---
students_per_category = df.groupby('Category')['StudentID'].nunique().reset_index()
students_per_category.columns = ['Category', 'TotalStudents']

students_per_category.to_csv('reports/total_students_per_category.csv', index=False)

# --- 3. Country-wise enrollments ---
country_enrollments = df['Country'].value_counts().reset_index()
country_enrollments.columns = ['Country', 'Enrollments']

country_enrollments.to_csv('reports/country_enrollments.csv', index=False)

# --- 4. Monthly enrollment trends ---
monthly_trends = df.groupby('EnrollMonth')['StudentID'].count().reset_index()
monthly_trends.columns = ['Month', 'Enrollments']
monthly_trends.to_csv('reports/monthly_enrollment_trends.csv', index=False)

