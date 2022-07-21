from PIL import Image
import os
import random

a = 0
path = r"./img_raw"
for root, dirs, files in os.walk(path):
    for f in files:
        im = Image.open(os.path.join(root, f))
        o = im.resize((128, 128))  # 大小
        outfile = o.rotate(random.randint(-100, 100)).resize((256, 256))  # 偏转角度
        a = a + 1
        outfile.save(r"./img_p/" + str(a) + ".jpg", "JPEG")
