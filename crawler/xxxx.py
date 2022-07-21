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


class XxxURLCrawler:
    def __init__(self, use_proxy=False):
        self.use_proxy = use_proxy

    def get_page_URL(self):
        """迭代器 一次返回一个page_url"""
        page_url = "XXX"
        yield page_url

    def run(self):
        """先不实现"""


class XxxImgDownloader:
    def __init__(self, use_proxy=False):
        self.use_proxy = use_proxy

    def download(self, img_url):
        img = ""
        return (img_url, img)

