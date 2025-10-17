from fastapi import FastAPI, HTTPException
import pandas as pd
from pydantic import BaseModel
class student(BaseModel):
    StudentID: str
    Name: str
    Email: str
    Country: str

#create FastAPI instance
app=FastAPI()

students=pd.read_csv('students.csv')
students = students.to_dict(orient="records")
@app.get("/students")
def get_all_students():
    return {"students": students}

@app.post("/students",status_code=201)
def add_student(student: student):
    students.append(student.dict())
    return {"message":"student added succesfully","student":student}

@app.put("/students/{student_id}")
def update_student(student_id: str, updated_student: student):
    for i, c in enumerate(students):
        if c["StudentID"] == student_id:
            students[i] = updated_student.dict()
            return{"message":"student updated succesfully","student":updated_student}
    raise HTTPException(status_code=404, detail="student not found")

@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    for i, c in enumerate(students):
        if c["StudentID"] == student_id:
            students.pop(i)
            return {"message": "student deleted succesfully"}
    raise HTTPException(status_code=404, detail="student not found")
