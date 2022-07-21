import base64

from flask import Flask, request, render_template, redirect, render_template_string
import requests
from config import config

app = Flask(__name__)

index_page = ""
with open("./index.html", "r") as f_obj:
    index_page = f_obj.read()

result_page_a = """
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/html">
<head>
    <meta charset="UTF-8">
    <title>result@pic_search</title>
    <style>
        * {
            padding: 0;
            margin: 0;
            word-break: break-all;
        }

        li {
            list-style: none;
        }
        
        body {
            background-color: wheat;
        }

        .result-box-container {
            width: 400px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px #888888;
            transition: 0.6s;
            margin: 15px;
            float: left;
            overflow: hidden;
        }

        .result-box-container:hover {
            box-shadow: 0 0 20px #888888
        }

        .top-decoration {
            width: 100%;
            height: 30px;
            background-color: green;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            margin-bottom: 10px;
        }
        
        .origin-img{
            margin-left:30px;
            margin-top:30px;
            margin-bottom:30px;
            width:300px;
            border-radius:10px;
        }

        .top-decoration p {
            padding-top: 3px;
            padding-left: 7px;
            color: white;
        }

        .left-img-group {
            width: 180px;
            float: left;
            padding: 10px;
        }

        .left-img-group img {
            width: 100%;
            padding-top: 10px;
            border-radius: 4px;
        }

        .right-info-group {
            width: 200px;
            float: left;
        }

        .bottom-decoration {
            height: 20px;
        }
    </style>
</head>
<body>
<img class="origin-img" src="data:image/png;base64,
"""

result_page_b = """
" alt="origin">
<div class="result-container">
"""

result_page_c = """
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return index_page


@app.route("/result-page/", methods=["POST"])
def result_page():
    raw_img = request.files["file"]
    img = raw_img.stream.read()
    vec = requests.post("http://" + ":".join(config.get("ImgFeatureServer")) + "/get-vec/",
                        files={"file": img})
    data = requests.get("http://" + ":".join(config.get("DBNode")) + "/search/5/", json=vec.text).json()
    result_boxes = []
    for d in data:
        result_boxes.append(generate_result_box(d))
    ret = ""
    ret += result_page_a
    ret += base64.b64encode(img).decode("UTF-8")
    ret += result_page_b
    for i in result_boxes:
        ret += i
    ret += result_page_c
    return ret


def generate_result_box(data):  # [img_url, b64, [page_urls], [screenshot, shot_date]]
    raw = """
        <div class="result-box-container">
            <div class="top-decoration"><p>[result@pic_search~]#</p></div>
            <div class="result-container">
                <div class="left-img-group">
                    <img class="result-img" src="data:image/png;base64,{{data[1]}}" alt="result">
                    <img class="screenshot" src="data:image/png;base64,{{data[-1][0]}}" alt="screenshot">
                </div>
                <div class="right-info-group">
                    <p>img url:<br><a href="{{data[0]}}">{{data[0]}}</a></p>
                    <p>shot date:<br>{{data[-1][-1]}}</p>
                    <p>page contain this img:</p>
                    <ul>
                        {% for u in data[-2]%}
                            <li><a href="{{u}}">{{u[:30]}}</a></li>
                        {% endfor %}
                    </ul>
                </div>
                <div style="clear:both"></div>
            </div>
            <div class="bottom-decoration"></div>
        </div>
        """

    return render_template_string(raw, data=data)


app.run(debug=True, host=config.get("Website")[0], port=config.get("Website")[1])
