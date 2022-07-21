from config import config
import logging
import time

from flask import Flask, request
import flask_apscheduler
import requests
import json


class Config(object):
    JOBS = [
        {
            'id': 'clk',
            'func': '__main__:clock',
            'args': None,
            'trigger': 'interval',
            'seconds': 5,
        }
    ]


app = Flask(__name__)
app.config.from_object(Config())

DB_HOST = "http://localhost:5003"

available_download_nodes = ["http://" + ":".join(config.get("DownloadNodes")[i]) for i in
                            range(len(config.get("DownloadNodes")))]

# available_download_nodes = []

available_screenshot_nodes = ["http://" + ":".join(config.get("ScreenshotNode"))]
# available_screenshot_nodes = []
URLCrawlerNode = "http://" + ":".join(config.get("UrlCrawlerNode"))


def clock():
    """
    Timer
    :return: None
    """
    print("[#]clock called")
    hand_out_screenshot()
    hand_out_task()


def hand_out_screenshot():
    """
    Hand out page_url to available screenshot nodes and record state.
    :return: ""
    """
    print("[#]hand_out_screenshot called")
    global available_screenshot_nodes
    for node in available_screenshot_nodes:
        if requests.get(node + "/get-stat/").text == "Free":
            page_url = get_page_url_from_db()
            if page_url == "":
                print("[#]calling awake")
                requests.get(URLCrawlerNode + "/awake/")
                return
            requests.post(node + "/shot/", json=json.dumps(page_url))


def get_page_url_from_db():
    """
    Get page url from database.
    :return: resp.json()
    """
    print("[*]Get page_URL")
    resp = requests.get(DB_HOST + "/get_page_url/")
    if resp.text == "":
        return ""
    return resp.json()


def get_page_urls_from_db(n):
    """
    Get page urls from database.
    :return: resp.json()
    """
    print("[*]Get page_URLs")
    resp = requests.get(DB_HOST + "/get_page_urls/"+str(n)+"/")
    if resp.text == "":
        return ""
    print(resp.text)
    return resp.json()


def get_task_from_db():
    """
    Get task from database.
    :return: resp.json()
    """
    print("[*]Get task")
    resp = requests.get(DB_HOST + "/get_task/")
    if resp.text == "":
        return ""
    return resp.json()


def set_task_ongoing(task):
    """
    Set task state.
    :param task: list
    :return: None
    """
    print("[*]Set task ongoing", task)
    print("[*]Ongoing state", requests.post(DB_HOST + "/task_ongoing/", json=json.dumps([task[0]])).text)


def hand_out_task():
    """
    Hand out task to available download nodes and record state.
    :return: ""
    """
    print("[#]hand_out_task called")
    global available_download_nodes
    for node in available_download_nodes:
        if requests.get(node + "/get-stat/").text == "Free":
            task = get_task_from_db()
            while len(task) == 0:
                time.sleep(5)
                task = get_task_from_db()
            if requests.post(node + "/set-task/", json=json.dumps(task)).text == "Success":
                set_task_ongoing(task)


@app.route("/finished/", methods=["POST"])
def task_finished():
    """
    Set task state to finished.
    :return: str:""
    """
    print("[#]task_finished called")
    r_data = json.loads(request.json)  # [task, self_url]
    print(r_data)
    print(requests.post(DB_HOST + "/task_success/", json=json.dumps(r_data[0])))
    task = get_task_from_db()
    if task:
        if requests.get(r_data[1] + "/set-task/").text == "Success":
            set_task_ongoing(task)
    return ""


@app.route("/unfinished/")
def task_unfinished():
    """
    Set task state to unfinished.
    :return: str:""
    """
    r_data = json.loads(request.json)  # [task, self_url]
    requests.post(DB_HOST + "/task_failed/", json.dumps(r_data[0]))
    task = get_task_from_db()
    if task:
        if requests.get(r_data[1] + "/set-task/").text == "Success":
            set_task_ongoing(task)


@app.route("/get-task/")
def sent_task():
    """
    Return single task.
    :return: json.dumps(task)
    """
    task = get_task_from_db()
    if task:
        set_task_ongoing(task)
    return json.dumps(task)


@app.route("/get-page-url/")
def get_page_url():
    """
    Return single page_url.
    :return: json.dumps(str:page_url)
    """
    page = get_page_url_from_db()
    return json.dumps(page)


@app.route("/get-page-urls/<int:n>/")
def get_page_urls(n):
    """
    Return n page_urls.
    :return: json.dumps(str:page_url)
    """
    pages = get_page_urls_from_db(n)
    return json.dumps(pages)


if __name__ == "__main__":
    scheduler = flask_apscheduler.APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host=config["Scheduler"][0], port=config["Scheduler"][1])
    # hand_out_screenshot()
    # hand_out_task()
