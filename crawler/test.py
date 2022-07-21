import time

from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common import by
from io import BytesIO
import PIL.Image
import base64

app = Flask(__name__)


@app.route("/")
def screenshot():
    if request.method=="GET":
        t_url = request.args.get('url')
        s = Service(r"C:/Users/16173/Downloads/chromedriver_win32/chromedriver.exe")
        op = webdriver.ChromeOptions()
        op.add_argument('headless')
        print(t_url)

        wd = webdriver.Chrome(service=s, options=op)
        wd.get(t_url)
        wd.implicitly_wait(1)
        width = wd.execute_script("return document.documentElement.scrollWidth")
        height = wd.execute_script("return document.documentElement.scrollHeight")
        wd.set_window_size(width, height)

        ret = "<img src="'data:image/png;base64,' + base64.b64encode(wd.get_screenshot_as_png()).decode(
            "UTF-8") + "></img>"
        wd.close()
        s.stop()
        return ret


app.run(debug=True)
