# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     proxy_pool
   Description :   proxy pool 启动入口
   Author :        JHao
   date：          2020/6/19
-------------------------------------------------
   Change Activity:
                   2020/6/19:
-------------------------------------------------
"""
__author__ = 'JHao'

import json
import random

import click
import redis

from helper.launcher import startServer, startScheduler
from flask import Flask, request
from setting import BANNER, VERSION

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=VERSION)
def cli():
    """ProxyPool cli工具"""


@cli.command(name="schedule")
def schedule():
    """ 启动调度程序 """
    click.echo(BANNER)
    startScheduler()


@cli.command(name="server")
def server():
    """ 启动api服务 """
    click.echo(BANNER)
    startServer()


import requests


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


# your spider code

def getHtml():
    # ....
    retry_count = 5
    proxy = get_proxy().get("proxy")
    while retry_count > 0:
        try:
            # 使用代理访问
            html = requests.get('http://www.baidu.com', proxies={"http": "http://{}".format(proxy)})
            return html
        except Exception:
            retry_count -= 1
            # 删除代理池中代理
            delete_proxy(proxy)
    return None


app = Flask(__name__)


@app.route('/')
def index():
    r = redis.StrictRedis(host="127.0.0.1", port=6379, db=0)
    result = r.hgetall('use_proxy')
    proxys_list=[]
    proxy_http_list = []
    proxy_https_list = []
    for k,y in result.items():
        y = y.decode('utf-8')
        if y.__contains__('"https": false'):
            proxy_http_list.append(y)
        else:
            proxy_https_list.append(y)
    proxy_http = random.choice(proxy_http_list).split(':')
    proxys_list.append('http:'+proxy_http[1].replace(' "', '')+':'+proxy_http[2].replace('", "https"', ''))
    proxy_https = random.choice(proxy_https_list).split(':')
    proxys_list.append('https:'+proxy_https[1].replace(' "', '')+':'+proxy_https[2].replace('", "https"', ''))
    return json.dumps(proxys_list)


if __name__ == '__main__':
    #使用前先运行schedule
    app.run()
    # schedule()
