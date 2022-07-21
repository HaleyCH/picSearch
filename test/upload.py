import os
import requests
from time import perf_counter

upload_url = "http://127.0.0.1:5007/result-page/"
path = r"./img_raw"
fileList = []
for root, dirs, files in os.walk(path):
    for f in files:
        fileList.append(os.path.join(root, f))
print(fileList)

for i in fileList:
    file = {"file": open(i, "rb")}
    start = perf_counter()
    print("上传图片时刻:" + str(start))
    upload_res = requests.post(url=upload_url, files=file)
    end = perf_counter()
    print("返回结果时刻：" + str(end))
    print("历时：" + str(end - start) + "\n")
