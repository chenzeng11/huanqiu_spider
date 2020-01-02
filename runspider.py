from HQWDownParser import HQWDownParser
import time
from random import randint

if __name__ == "__main__":
    classifies = {
        "https://mil.huanqiu.com/world": "军情动态",
        "https://bigdata.huanqiu.com/information": "大数据",
        "https://smart.huanqiu.com/ai": "人工智能",
        "https://uav.huanqiu.com/hyg": "无人机",
        "https://china.huanqiu.com/gangao": "港澳"
    }

    while 1:
        try:
            for item in classifies:
                with HQWDownParser() as dp:
                    dp.download(item, classifies[item])
                    dp.savebeforeexit()
                    time.sleep(randint(50, 80))
        finally:
            time.sleep(randint(500, 1200))
