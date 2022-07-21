import datetime
import time
from config import config
import json

import requests
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup as Soup
import base64
import queue
import concurrent.futures
import flask_apscheduler


class Config(object):
    JOBS = [
        {
            'id': 'clk',
            'func': '__main__:screenshot_manager',
            'args': None,
            'trigger': 'interval',
            'seconds': 5,
        }
    ]


app = Flask(__name__)
app.config.from_object(Config())
now_running = False
page_queue = queue.Queue(maxsize=15)
max_worker = 15

DB = "http://" + ":".join(config.get("DBNode"))


@app.route("/shot/", methods=["POST"])
def set_shot():
    """
    Called by Scheduler.
    Set a screenshot task.
    :return: str:'""
    """
    t_url = json.loads(request.json)
    page_queue.put(t_url)
    return ""


def queue_iter():
    """
    Get a iterator ver of page_queue
    :return: iterator:page_queue
    """
    global page_queue
    while not page_queue.empty():
        yield page_queue.get()


def screenshot_manager():
    """
    Manage screenshot task and a ProcessPoolExecutor that includes many webdriver
    :return: None
    """
    print("[#]screenshot_manager called")
    global now_running
    if now_running:
        print("now running")
        return

    now_running = True
    while not page_queue.full():
        # fill page_queue
        resp = requests.get("http://" + ":".join(config.get("Scheduler")) + "/get-page-urls/" + str(
            max_worker - page_queue.qsize()) + "/")
        print(resp.json())
        for u in resp.json():
            page_queue.put(u)
    print("[*]building ProcessPoolExecutor")
    e = concurrent.futures.ProcessPoolExecutor(max_workers=max_worker)
    o = [e.submit(screenshot, u) for u in queue_iter()]
    concurrent.futures.wait(o, timeout=4)
    print("[#]wait finish")
    e.shutdown(wait=True)
    now_running = False


def screenshot(t_url):
    print("[#]start screenshot")
    s = Service(r"C:/Users/16173/Downloads/chromedriver_win32/chromedriver.exe")
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    print(t_url)

    wd = webdriver.Chrome(service=s, options=op)
    try:
        wd.get(t_url)
        wd.implicitly_wait(1)
        width = wd.execute_script("return document.documentElement.scrollWidth")
        height = wd.execute_script("return document.documentElement.scrollHeight")
        wd.set_window_size(width, height)

        # ret = "<img src="'data:image/png;base64,' + base64.b64encode(wd.get_screenshot_as_png()).decode(
        #     "UTF-8") + "></img>"
        img_urls = []
        soup = Soup(wd.page_source, 'lxml')
        # find all img labels
        for x in soup.find_all("img"):
            if x is None:
                continue
            url = x.get('src')
            # filter
            if (("png" not in url) and ("jpg" not in url) and ("jpeg" not in url)) and not url[-1] == "/":
                continue
            if url is None:
                continue

            if url.startswith("//"):
                url = "http:" + url
            elif url.startswith("/"):
                url = "/".join(t_url.split("/")[3]) + url

            img_urls.append(url)
        print(img_urls)
        if len(img_urls) == 0:
            wd.close()
            s.stop()
            return ""
        # feed data to database
        print("[#]feed_page_data resp", requests.post(DB + "/feed_page_data/",
                                                      json=json.dumps([
                                                          t_url,
                                                          base64.b64encode(wd.get_screenshot_as_png()).decode("UTF-8"),
                                                          str(str(datetime.datetime.now())),
                                                          img_urls, ]
                                                      )))
        print("[#]feed_task resp", requests.post(DB + "/feed_task/",
                                                 json=json.dumps([
                                                     t_url,
                                                     img_urls,
                                                 ])))
    except:
        pass
    wd.close()
    s.stop()
    return ""


@app.route("/get-stat/")
def get_stat():
    if page_queue.full():
        return "Full"
    return "Free"


if __name__ == "__main__":
    scheduler = flask_apscheduler.APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host=config.get("ScreenshotNode")[0], port=config.get("ScreenshotNode")[1])
