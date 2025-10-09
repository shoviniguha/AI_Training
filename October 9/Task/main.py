from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel

#create FastAPI instance
app=FastAPI()

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html on root
@app.get("/")
def read_index():
    return FileResponse(os.path.join("static", "index.html"))

class Student(BaseModel):
    id: int
    name: str
    age: int
    course: str

students=[
    {"id":1,"name":"Rahul","age": 21,"course":"Python Basics"},
    {"id":2,"name":"Neha","age": 22,"course":"Machine Learning Basics"},
    {"id":3,"name":"Varun","age": 20,"course":"Python Advanced"},
    {"id":4,"name":"Amit","age": 22,"course":"Data Science Basics"},
    {"id":5,"name":"Sima","age": 21,"course":"Machine Learning Advanced"}
]

@app.get("/students")
def get_all_students():
    return {"students": students}