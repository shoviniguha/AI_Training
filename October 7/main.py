from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

#create FastAPI instance
app=FastAPI()

class Student(BaseModel):
    id: int
    name: str
    age: int
    course: str

students=[
    {"id":1,"name":"Rahul","age":21,"course":"AI"},
    {"id":2,"name":"Priya","age":22,"course":"ML"},
]
@app.get("/students")
def get_all_students():
    return {"students": students}

@app.get("/students/{id}")
def get_student(id: int):
    for student in students:
        if student["id"] == id:
            return student
    raise HTTPException(status_code=404, detail="student not found")

@app.post("/students",status_code=201)
def add_student(student: Student):
    students.append(student.dict())
    return {"message":"student added succesfully","student":student}

@app.put("/students/{student_id}")
def update_student(student_id: int, updated_student: Student):
    for i, s in enumerate(students):
        if s["id"] == student_id:
            students[i] = updated_student.dict()
            return{"message":"student updated succesfully","student":updated_student}
    raise HTTPException(status_code=404, detail="student not found")

@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for i, s in enumerate(students):
        if s["id"] == student_id:
            students.pop(i)
            return {"message": "student deleted succesfully"}
    raise HTTPException(status_code=404, detail="student not found")

#uvicorn main:app --reload