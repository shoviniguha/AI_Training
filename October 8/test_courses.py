from fastapi.testclient import TestClient
from courses_api import app
import pytest

client=TestClient(app)

def test_add_employee():
    new_course={
        "id": 2,
        "title": "Machine Learning Basics",
        "duration": "90",
        "fee": 4500,
        "is_active": True
    }
    response = client.post("/courses", json=new_course)
    assert response.status_code == 201
    assert response.json()["title"] == "Machine Learning Basics"

@pytest.mark.parametrize("duplicate_id", [1,1])
def test_duplicate_course_id_handling(duplicate_id):
    new_course={
        "id": duplicate_id,
        "title": "Machine Learning Intermediate",
        "duration": "90",
        "fee": 5500,
        "is_active": True
    }
    response = client.post("/courses", json=new_course)
    assert response.status_code == 400
    assert response.json()["detail"] == "Course ID already exists"

def test_validation():
    new_course = {
        "id": 2,
        "title": "Machine Learning Intermediate",
        "duration": 0,
        "fee": -1909,
        "is_active": True
    }
    response = client.post("/courses", json=new_course)
    assert response.status_code == 422
    error_text = response.text
    assert "Input should be greater than 0" in error_text

def test_response():
    response = client.get("/courses")
    data = response.json()
    assert isinstance(data, list)
    assert all("id" in course for course in data)
    assert all("title" in course for course in data)
    assert all("duration" in course for course in data)
    assert all("fee" in course for course in data)
    assert all("is_active" in course for course in data)
