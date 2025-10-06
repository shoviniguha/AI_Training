from pydantic import BaseModel
class Student(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool = True

#valid data
data={"name":"Ali","age":20,"email":"ali@example.com"}
student=Student(**data)

print(student)

#invalid data
invalid_data={"name":"Alisha","age":"twenty","email":"alisha@example.com"}
student1=Student(**invalid_data)

print(student1)