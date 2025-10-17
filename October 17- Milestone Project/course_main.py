from fastapi import FastAPI, HTTPException
import pandas as pd
from pydantic import BaseModel
class Course(BaseModel):
    CourseID: str
    Title: str
    Category: str
    Duration: int

#create FastAPI instance
app=FastAPI()

courses=pd.read_csv('courses.csv')
courses = courses.to_dict(orient="records")
@app.get("/courses")
def get_all_courses():
    return {"courses": courses}

@app.post("/courses",status_code=201)
def add_course(course: Course):
    courses.append(course.dict())
    return {"message":"course added succesfully","course":course}

@app.put("/courses/{course_id}")
def update_course(course_id: str, updated_course: Course):
    for i, c in enumerate(courses):
        if c["CourseID"] == course_id:
            courses[i] = updated_course.dict()
            return{"message":"course updated succesfully","course":updated_course}
    raise HTTPException(status_code=404, detail="course not found")

@app.delete("/courses/{course_id}")
def delete_course(course_id: str):
    for i, c in enumerate(courses):
        if c["CourseID"] == course_id:
            courses.pop(i)
            return {"message": "course deleted succesfully"}
    raise HTTPException(status_code=404, detail="course not found")