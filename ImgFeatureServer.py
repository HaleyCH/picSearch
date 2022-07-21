# -*- coding: utf-8 -*-
import base64

from config import config
import logging
import json
from flask import Flask, request
from tensorflow import keras as keras
import numpy as np
import PIL.Image
import requests
from io import BytesIO

app = Flask(__name__)

net50 = keras.applications.ResNet50()
net50.summary()
sub_net50 = keras.Model(net50.input, net50.get_layer("avg_pool").output)
DB = "http://" + ":".join(config.get("DBNode"))


@app.route("/", methods=["POST"])
def feature():
    """
    Called by DownloadNode.
    Calculate img_feature and feed it to database.
    :return:
    """
    id, img = json.loads(request.json)
    img = base64.b64decode(img)

    img = PIL.Image.open(BytesIO(img), mode="r")
    img.load()
    img = img.convert("RGB")
    img = img.resize((224, 224))
    img = np.array(img)
    img = img.reshape([1, 224, 224, 3])
    print(requests.post(DB + "/feed_img_feature/", json=json.dumps([id, sub_net50.predict(img).tolist()])))
    return ""


@app.route("/get-vec/", methods=["POST"])
def get_feature():
    """
    Called by WebsiteApp.
    Calculate img_feature and return it.
    :return: json.dumps(np.array(shape=(1,2048)))
    """
    img = request.files['file']
    img = PIL.Image.open(BytesIO(img.stream.read()), mode="r")
    img.load()
    img = img.convert("RGB")
    img = img.resize((224, 224))
    img = np.array(img)
    img = img.reshape([1, 224, 224, 3])
    return json.dumps(sub_net50.predict(img).tolist())


app.run(debug=True, host=config.get("ImgFeatureServer")[0], port=config.get("ImgFeatureServer")[1])
