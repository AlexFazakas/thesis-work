#!/usr/bin/env python3

import threading
import time
import requests
import uuid
from time import sleep
import click
import json

class Submitter(threading.Thread):
    def __init__(self, default_report, API, semaphore, repeats=1):
        threading.Thread.__init__(self)
        self.repeats = repeats
        self.report = default_report
        self.API = API
        self.semaphore = semaphore

    def run(self):
        for _ in range(self.repeats):
            self.semaphore.acquire()
            self.report['Date'] = uuid.uuid4()
            self.semaphore.release()
            r = requests.post(self.API, data=self.report)

@click.command()
@click.option('--num_threads', '-t', required=True, type=int, help='Number of threads making requests (equivalent to number of requests per second)')
@click.option('--num_repeats', '-r', required=True, type=int, help='Number of requests made by a thread')
def main(num_threads, num_repeats):
    threads = []
    report = {}
    semaphore = threading.Semaphore(1)
    with open('report.json', 'r') as f:
        report = json.load(f)
    for _ in range(num_threads):
        threads.append(Submitter(report, 'https://4uggmy4bxi.execute-api.eu-central-1.amazonaws.com/default/add_report', semaphore, num_repeats))
    for index in range(num_threads):
        threads[index].start()
    for index in range(num_threads):
        threads[index].join()

if __name__ == '__main__':
    main()