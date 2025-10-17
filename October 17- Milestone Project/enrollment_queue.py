import threading
import queue
import csv
import time
import logging
import os
import pandas as pd
import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Initialize queue
enrollment_queue = queue.Queue()

# File to save processed data
processed_file = 'processed_enrollments.csv'

# Load new enrollments from CSV
try:
    new_enrollments_df = pd.read_csv("enrollments.csv")
except FileNotFoundError:
    logging.error("enrollments.csv not found!")
    exit(1)

# Convert DataFrame to list of dicts
new_enrollments = new_enrollments_df.to_dict(orient="records")

# Producer: adds records to queue
def producer():
    for record in new_enrollments:
        enrollment_queue.put(record)
        logging.info(f"Produced: {record}")
        time.sleep(0.1)  # simulate delay

# Consumer: processes records from queue
def consumer():
    start_time = datetime.datetime.now()
    logging.info(f"ETL started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    processed_records = []
    while not enrollment_queue.empty():
        record = enrollment_queue.get()

        # ETL step: Add CompletionStatus
        progress = record.get('progress', 0)
        record['CompletionStatus'] = 'Completed' if progress >= 80 else 'In Progress'
        record['EnrollDate'] = pd.to_datetime(record['EnrollDate'])  # Converts string to datetime
        record['EnrollMonth'] = record['EnrollDate'].month  # Extracts month from datetime
        processed_records.append(record)
        logging.info(f"Consumed & Processed: {record}")

        enrollment_queue.task_done()
        time.sleep(0.1)  # simulate processing time

    # Save to CSV
    if processed_records:
        file_exists = os.path.isfile(processed_file)
        with open(processed_file, 'a', newline='') as csvfile:
            fieldnames = ["EnrollmentID","StudentID","CourseID","EnrollDate","Progress","EnrollMonth","CompletionStatus"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerows(processed_records)
        end_time = datetime.datetime.now()
        runtime = (end_time - start_time).total_seconds()
        logging.info(f"ETL completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"ETL runtime: {runtime:.2f} seconds")
        logging.info(f"Total records processed and saved: {len(processed_records)}")

# Run threads
producer_thread = threading.Thread(target=producer)
consumer_thread = threading.Thread(target=consumer)

producer_thread.start()
producer_thread.join()  # Wait for producer

consumer_thread.start()
consumer_thread.join()  # Wait for consumer
