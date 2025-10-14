import multiprocessing
from producer import producer_program
from consumer import consumer_program

if __name__ == "__main__":
    shared_queue = multiprocessing.Queue()

    # Create producer and consumer processes
    producer_process = multiprocessing.Process(target=producer_program, args=(shared_queue,))
    consumer_process = multiprocessing.Process(target=consumer_program, args=(shared_queue,))

    # Start the processes
    producer_process.start()
    consumer_process.start()

    # Wait for both processes to finish
    producer_process.join()
    consumer_process.join()

    print("Both producer and consumer processes finished.")