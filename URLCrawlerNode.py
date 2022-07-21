import json
import queue
import random
import logging

import requests
from config import config
from flask import Flask, request
import flask_apscheduler
import time
from crawler.sohu import SohuURLCrawler, SohuAPICrawler
import concurrent.futures
import threading

now_crawling = False
app = Flask(__name__)

DB = "http://" + ":".join(config.get("DBNode"))


def save_to_db(l):
    DB_SERVER = "localhost:5000"
    for i in range(int(len(l) / 1000)):
        print(requests.post(DB + "/feed_page_urls/", json=json.dumps([l[i * 1000:(i + 1) * 1000]])))
    print(requests.post(DB + "/feed_page_urls/",
                        json=json.dumps([l[int(1000 * (len(l) / 1000)):-1]])))


def start_crawling():
    global now_crawling
    if now_crawling:
        return
    now_crawling = True
    crawlers = [  # SohuURLCrawler(),
        SohuAPICrawler()]
    e = concurrent.futures.ProcessPoolExecutor(max_workers=len(crawlers))
    future_to_crawler = {e.submit(c.get_page_URL): c for c in crawlers}
    for future in concurrent.futures.as_completed(future_to_crawler):
        print(type(future.result()))
        print(len(future.result()))
        save_to_db(future.result())
    now_crawling = False


@app.route("/awake/")
def awake():
    print("[#]awake called")
    if now_crawling:
        print("running")
        return ""
    print("[*]start")
    t = threading.Thread(target=start_crawling)
    t.start()
    return ""


if __name__ == "__main__":
    app.run(debug=True, host=config.get("UrlCrawlerNode")[0], port=config.get("UrlCrawlerNode")[1])
