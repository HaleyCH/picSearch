import base64

from config import config
import logging
import json
import queue
import random

import requests
from flask import Flask, request
import flask_apscheduler
import time
from crawler.sohu import SohuDownloader
import concurrent.futures

import my_fake_useragent

DB = "http://" + ":".join(config.get("DBNode"))


class Config(object):
    JOBS = [
        {
            'id': 'clock',
            'func': '__main__:task_manager',
            'args': None,
            'trigger': 'interval',
            'seconds': 5,
        }
    ]


max_worker = 5
now_running = False
task_queue = queue.Queue(maxsize=30)
app = Flask(__name__)
app.config.from_object(Config())

ua = my_fake_useragent.UserAgent()

now_running = False


def get_proxy():
    # resp = requests.get("http://" + ":".join(config.get("ProxyPool")))
    # if resp.text == "":
    #     return None
    # return resp.json()
    return None


def task_manager():
    """
    Manage task_queue and a ProcessPoolExecutor that includes many downloader.
    :return: None
    """
    if task_queue.empty():
        return
    if now_running:
        return

    e = concurrent.futures.ProcessPoolExecutor(max_workers=max_worker)
    while not task_queue.empty():
        task = task_queue.get()
        e.submit(downloader, task)
    e.shutdown(wait=True)


def downloader(task):
    """
    Download task.
    Manage a ProcessPoolExecutor that including many download process.
    :param task: [page_url, [img_urls]]
    :return: None
    """
    print("[#]downloading...")
    t_url = task[0]
    img_urls = task[1]
    print(img_urls)
    e = concurrent.futures.ProcessPoolExecutor(max_workers=max_worker)
    records = {e.submit(download, url): url for url in img_urls}
    print("[#]wait finish")
    e.shutdown(wait=True)
    for f in records.keys():
        if f.result() is not None and type(f.result()) != str:
            b64_img = base64.b64encode(f.result()).decode("UTF-8")
            resp = requests.post(DB + "/feed_img_data/",
                                 json=json.dumps([records[f], b64_img, t_url]))
            print("db resp", resp)
            id = resp.json()
            print(json.dumps([id]))
            print("ImgFeatureServer resp",
                  requests.post("http://" + ":".join(config.get("ImgFeatureServer")) + "/",
                                json=json.dumps([id, b64_img])))
            # requests.post("http://127.0.0.1:5111" + "/",
            #               json=json.dumps([id, b64_img])))

            print("[#]finish")


def download(url):
    """
    Download img.
    :param url: str, target
    :return: bytes
    """
    print("download", url)
    if requests.get(DB + "/img_exist/", json=json.dumps([url])).text != "":
        return None
    headers = {"User-Agent": ua.random()}
    proxy = get_proxy()
    # check whether using proxy
    if proxy is not None:
        resp = requests.get(url, headers=headers, proxies=proxy)
    else:
        resp = requests.get(url, headers=headers)
    print(resp)
    return resp.content


@app.route("/set-task/", methods=["POST"])
def set_task():
    """
    Called by Scheduler.
    Set a task to task_queue.
    :return: str:"Success" or "Failed"
    """
    print("[#]set_task called")
    task = json.loads(request.json)
    if task_queue.full():
        return "Failed"
    task_queue.put(task)
    return "Success"


@app.route("/get-stat/")
def return_state():
    """
    Called by Scheduler.
    Return DownloadNode's state.
    :return: str:"Full" or "Free"
    """
    if task_queue.full():
        return "Full"
    return "Free"


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    scheduler = flask_apscheduler.APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host=config["DownloadNodes"][0][0], port=config["DownloadNodes"][0][1])
