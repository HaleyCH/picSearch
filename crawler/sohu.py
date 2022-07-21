import json

from bs4 import BeautifulSoup as Soup
import requests
import demjson


class SohuURLCrawler:
    def __init__(self, use_proxy=False):
        self.headers = {}
        self.use_proxy = use_proxy
        self.target_list = ["https://news.sohu.com/",
                            "https://www.sohu.com/c/8/1460/",
                            "https://www.sohu.com/c/8/1461/",
                            "https://mil.sohu.com/",
                            "http://police.news.sohu.com/",
                            "https://gongyi.sohu.com/",
                            ]
        self.page_URLs = []

    def get_page_URL(self):
        for t_url in self.target_list:
            resp = requests.get(t_url)
            soup = Soup(resp.content, 'lxml')

            links = soup.find_all("a")
            for result in links:
                try:
                    if "/a/" in result['href'] and "#" not in result['href']:
                        if "sohu" not in result['href']:
                            self.page_URLs.append("http://www.sohu.com" + result['href'])
                        elif "http" in result['href']:
                            self.page_URLs.append(result['href'])
                        else:
                            self.page_URLs.append("http:" + result['href'])
                except:
                    pass


class SohuAPICrawler():
    def __init__(self, use_proxy=False):
        self.headers = {}
        self.use_proxy = use_proxy
        self.page_URLs = []

    def get_page_URL(self):
        results = []
        for i in range(50):
            for j in range(10):
                url = "https://v2.sohu.com/public-api/feed?scene=CATEGORY&sceneId=146" + str(
                    j) + "&size=20&page=" + str(i)
                results.append(requests.get(url).json())
        for r in results:
            for s in r:
                url = s.get("originalSource")
                if url and url not in self.page_URLs:
                    if url.startswith("//"):
                        url = "http:" + url
                    self.page_URLs.append(url)
        for y in range(17, 18):
            for m in range(1, 13):
                for d in range(1, 2):
                    t_url = "https://news.sohu.com/_scroll_newslist/20{}{}{}/news.inc".format(str(y).zfill(2),
                                                                                              str(m).zfill(2),
                                                                                              str(d).zfill(2))
                    try:
                        resp = requests.get(t_url)
                        text = resp.text
                        t = text.replace("var newsJason =", "").strip()
                        j = demjson.decode(t)
                        for u in [j['item'][k][-2] for k in range(len(j['item']))]:
                            self.page_URLs.append(u)
                    except:
                        continue
        return self.page_URLs


class SohuDownloader:

    def download(self, url):
        pass


if __name__ == "__main__":
    sc = SohuAPICrawler()
    sc.get_page_URL()
    # print(set(sc.page_URLs))
    print(len(set(sc.page_URLs)))
    from config import config

    DB = "http://" + ":".join(config.get("DBNode"))
    # print(sc.page_URLs)

    for i in range(int(len(sc.page_URLs) / 1000)):
        print(requests.post(DB + "/feed_page_urls/", json=json.dumps([sc.page_URLs[i * 1000:(i + 1) * 1000]])))
    print(requests.post(DB + "/feed_page_urls/",
                        json=json.dumps([sc.page_URLs[int(1000 * (len(sc.page_URLs) / 1000)):-1]])))
