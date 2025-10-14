import multiprocessing
import time

def producer_program(q):
    for i in range(5):
        message = f"Message {i} from Producer"
        print(f"Producer putting: {message}")
        q.put(message)
        time.sleep(0.5) # Simulate some work
    q.put("STOP") # Signal to the consumer to stop