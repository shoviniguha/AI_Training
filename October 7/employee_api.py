from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

#create FastAPI instance
app=FastAPI()

class Employee(BaseModel):
    id: int
    name: str
    department: str
    salary: float

employees=[
    {"id":1,"name":"Rahul","department":"Marketing","salary":40000},
    {"id":2,"name":"Neha","department":"Technology","salary":50000},
    {"id":3,"name":"Varun","department":"Tax","salary":38000}
]

@app.get("/employees")
def get_all_employees():
    return {"employees": employees}

@app.get("/employees/count")
def get_count():
    return {"number of employees": len(employees)}

@app.get("/employees/{id}")
def get_employee(id: int):
    for e in employees:
        if e["id"] == id:
            return e
    raise HTTPException(status_code=404, detail="employee not found")


@app.post("/employees",status_code=201)
def add_employee(employee: Employee):
    emp=employee.dict()
    ids=[e['id'] for e in employees]
    if emp["id"] not in ids:
        employees.append(emp)
        return {"message": "employee added succesfully", "employee": employee}
    else:
        return{"message":"duplicate id not allowed"}

@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, updated_employee: Employee):
    for i, e in enumerate(employees):
        if e["id"] == employee_id:
            employees[i] = updated_employee.dict()
            return{"message":"employee updated succesfully","employee":updated_employee}
    raise HTTPException(status_code=404, detail="employee not found")

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    for i, e in enumerate(employees):
        if e["id"] == employee_id:
            employees.pop(i)
            return {"message": "employee deleted succesfully"}
    raise HTTPException(status_code=404, detail="employee not found")