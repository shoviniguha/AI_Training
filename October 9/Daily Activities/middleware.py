from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import time
import traceback

app = FastAPI()

# ---------------- SETUP STRUCTURED LOGGING ----------------
logging.basicConfig(
    filename="app.log",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

# ---------------- REQUEST LOGGING MIDDLEWARE ----------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        duration = round(time.time() - start, 3)
        logging.error(
            f"Exception in {request.method} {request.url.path}: {str(e)}\n{traceback.format_exc()}"
        )
        raise e
    duration = round(time.time() - start, 3)
    logging.info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | Duration: {duration}s"
    )
    return response

# ---------------- ROUTES ----------------
students = [{"id": 1, "name": "Rahul"}, {"id": 2, "name": "Neha"}]

@app.get("/students")
def get_students():
    logging.info("Fetching all students from database...")
    return students

@app.get("/error-demo")
def error_demo():
    raise ValueError("Simulated error for testing logs")

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
