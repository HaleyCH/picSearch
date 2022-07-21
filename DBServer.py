from bson import ObjectId

from config import config
import logging
import time

import requests
from flask import Flask, request
import pymongo
import json
import numpy as np

import faiss

app = Flask(__name__)

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
myDB = my_client["DATA"]

url_to_shot = myDB["url_to_shot"]
task = myDB["task"]
all_URL = myDB["all_URL"]
page_data = myDB["page_data"]
img_data = myDB["img_data"]
img_feature = myDB["img_feature"]

faiss_db = faiss.IndexFlatL2(2048)
curr_features = None


@app.route("/feed_page_url/", methods=["POST"])
def feed_page_url():
    """
    feed page_url:
        Called by URLCrawlerNode after it finish its task.
        Feed single page_url to database
    :return: str""
    """
    selector = {"URL": json.loads(request.json)[0]}
    if all_URL.find_one(selector):
        return ""
    url_to_shot.insert_one(selector)
    all_URL.insert_one(selector)
    return ""


@app.route("/feed_page_urls/", methods=["POST"])
def feed_page_urls():
    """
    feed page_urls:
        Called by URLCrawlerNode after it finish its task.
        Feed all page_urls to database
    :return: str""
    """
    print(len([{"URL": v} for v in json.loads(request.json)[0]]))
    i = 0  # insert failed count
    j = 0  # insert success count
    for url in json.loads(request.json)[0]:
        selector = {"URL": url}
        if all_URL.find_one(selector):  # avoid duplicate
            i += 1
            continue
        url_to_shot.insert_one(selector)
        all_URL.insert_one(selector)
        j += 1
    print(i, j)
    return ""


@app.route("/get_page_url/")
def get_page_url():
    """
    get_page_url:
        Called by Scheduler or ScreenshotNode.
        Return a json.dumps()ed url
    :return: json.dumps(url)
    """
    print("[#]get_page_url called")
    u = url_to_shot.find_one()
    if u is None:
        return ""
    url = u.get("URL")
    print(url)
    url_to_shot.delete_one({"_id": u.get("_id")})
    return json.dumps(url)


@app.route("/get_page_urls/<int:n>/")
def get_page_urls(n):
    """
    get_page_urls:
        Called by Scheduler or ScreenshotNode.
        Return a json.dumps()ed list<str:url> with total length n.
    :param n: int the length of list<str:url> request by Scheduler or ScreenshotNode.
    :return: json.dumps(list<str:url>)
    """
    print("[#]get_page_urls called")
    ret = []
    for i in range(n):
        u = url_to_shot.find_one()
        if u is None:  # avoid the table is empty
            break
        url = u.get("URL")
        print(url)
        ret.append(url)
        url_to_shot.delete_one({"_id": u.get("_id")})
    return json.dumps(ret)


@app.route("/feed_task/", methods=["POST"])
def feed_task():
    """
    feed_task:
        Called by ScreenshotNode.
        Feed single task to database.
    :return: str()
    """
    p_task = json.loads(request.json)  # [page_URL, [img_URLs]]
    i_data = {"page_URL": p_task[0], "img_URLs": p_task[1], "state": 1}
    task.insert_one(i_data)
    return ""


@app.route("/get_task/")
def get_task():
    """
    get_task:
        Called by Scheduler.
        Return single task and set task state to int:0.
    :return: json.dumps(list<str>[page_url, img_urls])
    """
    t = task.find_one({"state": {"$gt": 0}})
    if t is None:
        return ""
    ret = [t.get("page_URL"), t.get("img_URLs")]
    selector = {"page_URL": t.get("page_URL")}
    task.update_one(selector, {"$set": {"state": 0}})
    print(ret)
    return json.dumps(ret)


@app.route("/task_ongoing/", methods=['GET', 'POST'])
def task_ongoing():
    """
    task_ongoing:
        Called by Scheduler.
        Set the state of task to int:-1.
        Return the state of the task now.
    :return: str(int:state)
    """
    p_task = json.loads(request.json)  # [page_url ]
    print(p_task)
    selector = {"page_URL": p_task[0]}
    t = task.find_one(selector)
    if t is None:  # task not exist
        return "None"
    if t.get("state") < 0:  # Already ongoing
        return ""
    task.update_one(selector, {"$set": {"state": (t.get("state") + 1) * -1}})
    t = task.find_one(selector)
    return str(t.get("state"))


@app.route("/task_success/", methods=["POST"])
def task_success():
    """
    task_success:
        Called by Scheduler.
        Delete the task from database.
    :return: str:""
    """
    print("[#]task_success called")
    p_task = json.loads(request.json)
    print(p_task)
    selector = {"page_URL": p_task}
    task.delete_one(selector)
    return ""


@app.route("/task_failed/")
def task_failed():
    """
    task_success:
        Called by Scheduler.
        Record its failed times while setting the state that making it can be get from /get_task/ again.
    :return: str:""
    """
    r_data = json.loads(request.json)
    selector = {"page_URL": r_data[0]}
    prev_t = task.find_one(selector)
    if prev_t.get("state") * -1 >= 5:
        task.delete_one(selector)
        return ""
    task.update_one(selector, {"$set": {"state": prev_t.get("state") * -1 + 1}})
    return ""


@app.route("/feed_page_data/", methods=["POST"])
def feed_page_data():
    """
    Called by ScreenshotNode.
    Feed a page's data including [page_url, screenshot, shot_date, [img_URLs ]]
    :return: str:""
    """
    r_data = json.loads(request.json)  # [page_url, screenshot, shot_date, [img_URLs ]]
    i_data = {"page_url": r_data[0], "screenshot": r_data[1], "shot_date": r_data[2], "img_URLs": r_data[-1]}
    page_data.insert_one(i_data)
    return ""


@app.route("/get_page_data/")
def get_page_data():
    """
    Called by WebsiteApp.
    Return [str:page_url, str:base64:screenshot, str:shot_date]
    :return: list[str:page_url, str:base64:screenshot, str:shot_date]
    """
    r_data = json.loads(request.json)  # [page_url ]
    selector = {"page_url": r_data[0]}
    f = page_data.find_one(selector)
    return json.dumps([r_data[0], f.get("screenshot"), f.get("shot_date")])


@app.route("/feed_img_data/", methods=["POST"])
def feed_img_data():
    """
    Called by DownloadNode.
    Feed img data and return the image's id in database
    :return: json.dumps(str:id)
    """
    r_data = json.loads(request.json)  # [img_url, img, page_url]
    selector = {"img_url": r_data[0]}
    f = img_data.find_one(selector)
    if f is not None:
        url_l = f.get("page_url", [])
        url_l.append(r_data[2])
        img_data.update_one(selector, {"$set": {"page_url": url_l}})
        return json.dumps(str(f.get("_id")))
    else:
        i_data = {"img_url": r_data[0], "b64": r_data[1], "page_url": [r_data[2]]}
        o = img_data.insert_one(i_data)
        return json.dumps(str(o.inserted_id))


@app.route("/get_img_data/")
def get_img_data():
    """
    Find img data by id.
    :return: json.dumps([str:img_url, str:base64:img data])
    """
    r_data = json.loads(request.json)  # [img_id ]
    selector = {"_id": ObjectId(r_data[0])}
    f = img_data.find_one(selector)
    return json.dumps([f.get("img_url"), f.get("b64")])


@app.route("/feed_img_feature/", methods=["POST"])
def feed_img_feature():
    """
    Called by ImgFeatureServer.
    Feed [str:img_id, list<list<float64>>:feature_vector] to database
    :return: str:""
    """
    r_data = json.loads(request.json)  # [img_id, feature_vec]
    i_data = {"img_id": r_data[0], "feature_vec": r_data[1], "state": 0}
    selector = {"img_id": r_data[0]}
    if img_feature.find_one(selector):
        return ""
    img_feature.insert_one(i_data)
    return ""


@app.route("/get_img_feature/")
def get_img_feature():
    """
    Select img_feature by img_id.
    :return:  json.dumps(list<list<<float64>>:feature_vec)
    """
    r_data = json.loads(request.json)  # [img_id ]
    selector = {"_id": ObjectId(r_data[0])}
    f = img_data.find_one(selector)
    return json.dumps(f.get("feature_vec"))


@app.route("/img_exist/")
def img_exist():
    """
    Called by DownloadNode.
    Check whether the img is exist in database.
    :return: str
    """
    selector = {"img_id": json.loads(request.json)[0]}
    if img_feature.find_one(selector):
        return "1"
    return ""


def refresh_faiss_db():
    """
    Reload faiss database to adapt new img_data
    :return: None
    """
    global curr_features
    curr_features = []
    img_feature.update_many({}, {"$set": {"state": 0}})
    for x in img_feature.find({"state": 0}, {"feature_vec": 1}):
        curr_features.append(x.get("feature_vec")[0])
    arr = np.array(curr_features).astype('float32')
    faiss_db.add(arr)


@app.route("/search/<int:n>/")
def search(n):
    """
    Called by
    :param n: int, number to fetch
    :return: json.dumps([img_url, b64, [page_urls], [screenshot, shot_date]])
    """
    if n < 0:
        n = 1
    if n > 5:
        n = 5
    print(request.json)
    a = json.loads(request.json)
    a = np.array(a).astype('float32')

    global curr_features
    if curr_features is None:  # loading faiss_db
        refresh_faiss_db()

    d, idx = faiss_db.search(a, n)  # get index
    ret = []
    for i in range(n):
        _id = curr_features[int(idx.tolist()[0][i])]
        selector = {"feature_vec": [curr_features[int(idx.tolist()[0][i])]]}
        _id = img_feature.find_one(selector).get("img_id")
        if _id is None:
            continue
        selector = {"_id": ObjectId(_id)}
        data = img_data.find_one(selector, {"_id": 0})

        # pass empty data
        if data is None:
            continue
        ret_data = [data.get("img_url"), data.get("b64"), data.get("page_url")]

        for p in data.get("page_url"):
            selector = {"page_url": p}
            screenshot = page_data.find_one(selector)
            if not screenshot:
                continue
            ret_data.append([screenshot.get("screenshot"), screenshot.get("shot_date")])
            break

        ret.append(ret_data)
    return json.dumps(ret)


if __name__ == "__main__":
    app.run(debug=True, host=config["DBNode"][0], port=config["DBNode"][1])
