import multiprocessing
import time

def consumer_program(q):
    while True:
        message = q.get()
        if message == "STOP":
            print("Consumer received STOP signal. Exiting.")
            break
        print(f"Consumer got: {message}")
        time.sleep(1) # Simulate some work