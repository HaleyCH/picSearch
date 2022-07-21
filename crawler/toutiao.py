import requests
import urllib.parse
from my_fake_useragent import UserAgent
from bs4 import BeautifulSoup as Soup
import time
import random
import json
import hashtable
import execjs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common import by


class ToutiaoURLCrawler:
    base_url = "https://www.toutiao.com/"
    API_url = "https://www.toutiao.com/api/pc/list/feed?"

    def __init__(self):
        self.headers = {"User-Agent": "", }
        self.use_proxy = False
        self.proxy = None
        self.page_urls = []
        self.crawled = hashtable.HashTable(32767)
        self.signature = ""
        self.cookies = None
        self.channel_ids = ["0", "94349549395"]
        self.channel_ids += ["318939" + str(8959 + i) for i in range(50)]
        self.webdriver = ""

        self.refresh_signature()

    def refresh_signature(self):  # 后期封装到 utils_app.py 中 利用flask
        resp = requests.get(self.base_url, headers=self.headers, proxies=self.proxy)
        self.cookies = resp.cookies
        s = Service(r"C:/Users/16173/Downloads/chromedriver_win32/chromedriver.exe")
        op = webdriver.ChromeOptions()
        op.add_argument('headless')
        self.webdriver = webdriver.Chrome(service=s, options=op)
        self.webdriver.get("https://www.toutiao.com/")
        time.sleep(5)
        self.signature = self.webdriver.execute_script(
            "return window.byted_acrawler.sign(\"\",\"" + self.cookies.get("__ac_nonce") + "\");")
        self.webdriver.close()
        s.stop()
        return self

    def get_page_URL(self):
        for channel_id in self.channel_ids:
            feed_string = f"offset=0&channel_id={channel_id}&max_behot_time=1&category=pc_profile_channel&disable_raw_data=true&aid=24&app_name=toutiao_web&_signature={self.signature}"
            resp = requests.get(self.API_url + feed_string,
                                headers=self.headers,
                                proxies=self.proxy
                                )
            time.sleep(random.random() * 2)
            for i in range(len(resp.json()['data'])):
                if "Abstract" in resp.json()['data'][i].keys():
                    if resp.json()['data'][i].get("article_url", None) is not None:
                        yield resp.json()['data'][i].get("article_url", None)
                        self.page_urls.append(resp.json()['data'][i].get("article_url", None))




tc = ToutiaoURLCrawler()
for url in tc.get_page_URL():
    print(url)
