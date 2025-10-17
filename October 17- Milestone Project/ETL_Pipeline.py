import pandas as pd
from datetime import datetime
import os

def run_pipeline():
    today = pd.to_datetime(datetime.today().date())
    students = pd.read_csv("students.csv")
    courses = pd.read_csv("courses.csv")
    enrollments = pd.read_csv("enrollments.csv")
    students_enrollments = pd.merge(students, enrollments, on='StudentID', how='inner')
    df = pd.merge(courses, students_enrollments, on='CourseID', how='inner')
    # Ensure EnrollDate is datetime
    df['EnrollDate'] = pd.to_datetime(df['EnrollDate'], errors='coerce')

    # Add CompletionStatus if not already
    df['CompletionStatus'] = df['Progress'].apply(lambda x: 'Completed' if x >= 80 else 'In Progress')

    # Build the daily summary DataFrame
    summary = {
        'TotalEnrollments': [len(df)],
        'UniqueStudents': [df['StudentID'].nunique()],
        'CoursesEnrolled': [df['Title'].nunique()],
        'AvgProgress': [round(df['Progress'].mean(), 2) if not df.empty else 0],
        'CompletionRate (%)': [
            round((df['CompletionStatus'] == 'Completed').mean() * 100, 2) if not df.empty else 0
        ]
    }

    daily_report = pd.DataFrame(summary)

    # File name
    report_filename = f"daily_enrollment_report_{today.strftime('%Y%m%d')}.csv"
    report_path = os.path.join('reports', report_filename)

    # Ensure reports directory exists
    os.makedirs('reports', exist_ok=True)

    # Save the report
    daily_report.to_csv(report_path, index=False)

    print(f"✅ Daily enrollment report saved: {report_path}")

    print(f"Pipeline completed at {datetime.now()}")

if __name__=="__main__":
    run_pipeline()