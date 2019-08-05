#!/usr/bin/env python3

from http_server import web
from http_server import notify
from multiprocessing import Process

def main():
    son_process_http = Process(target=web.http_task)
    son_process_timer= Process(target=notify.timer_task)

    # start
    son_process_http.start()
    son_process_timer.start()

    # join
    son_process_http.join()
    son_process_timer.join()

if __name__ == '__main__':
    main()