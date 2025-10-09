from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import time
import traceback

app = FastAPI()

@app.middleware("http")
async def execution_time(request: Request, call_next):
    start=time.perf_counter()
    response = await call_next(request)
    end=time.perf_counter()
    execution_time=end-start
    response.headers["execution_time"] = str(execution_time)
    return response

# ---------------- ROUTES ----------------
students = [{"id": 1, "name": "Rahul"}, {"id": 2, "name": "Neha"}]

@app.get("/students")
def get_students():
    return students

# ---------------- GLOBAL EXCEPTION HANDLER ----------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(
        f"Unhandled error in {request.url.path}: {str(exc)}\n{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )
