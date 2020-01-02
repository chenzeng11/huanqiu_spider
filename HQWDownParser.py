# -*- coding:utf-8 -*-
# @Date    : 2019-09-15
# @Author  : Chen Zeng

import os
import time
from random import randint
# from io import StringIO
# from lxml import etree
import platform
# from datetime import datetime
from pyvirtualdisplay import Display
from selenium import webdriver
from collections import deque
import pickle

# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler("log.txt")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
## 控制台handler
chhandler = logging.StreamHandler()
chhandler.setFormatter(formatter)
logger.addHandler(chhandler)
from pybloom_live import ScalableBloomFilter

blommfilter_file = "bloomfilter.suffix"
titlefilter_file = "titlefilter.suffix"
deque_file = "sites.pkl"
try:
    sbf = ScalableBloomFilter.fromfile(open(blommfilter_file, "rb"))
    sbf_title = ScalableBloomFilter.fromfile(open(titlefilter_file, "rb"))
    with open(deque_file,'rb') as f:
        sites_deque = pickle.load(f)
except:
    # logger.warning('去重文件不存在')
    sbf = ScalableBloomFilter(
        initial_capacity=5000,
        error_rate=0.001,
        mode=ScalableBloomFilter.LARGE_SET_GROWTH,
    )
    sbf_title = ScalableBloomFilter(
        initial_capacity=5000,
        error_rate=0.001,
        mode=ScalableBloomFilter.LARGE_SET_GROWTH,
    )
    sites_deque = deque(maxlen=500)


class HQWDownParser(object):
    def __init__(self, proxy=None):
        self.proxy = proxy

    def __enter__(self):
        # 打开界面
        self.display = self.get_display()
        #  打开浏览器
        self.browser = self.get_browser(self.proxy)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 关闭浏览器
        try:
            if self.browser:
                self.browser.delete_all_cookies()
                self.browser.quit()
        except Exception as e:
            logger.exception(e)
        # 关闭界面
        try:
            # 关闭浏览器,关闭窗口
            self.display and self.display.stop()
        except Exception as e:
            logger.exception(e)
        self.savebeforeexit()

    def savebeforeexit(self):
        if sbf:
            sbf.tofile(open(blommfilter_file, "wb"))
        if sbf_title:
            sbf_title.tofile(open(titlefilter_file, "wb"))
        if sites_deque:
            with open(deque_file, 'wb') as f:
                pickle.dump(sites_deque, f)

    def get_display(self):
        """ 获取操作系统桌面窗口 """
        if (platform.system() != "Darwin") and (platform.system() != "Windows"):
            # 不是mac系统, 启动窗口
            display = Display(visible=0, size=(1024, 768))
            display.start()
        else:
            display = None
        return display

    def get_browser(self, proxy):
        """ 启动并返回浏览器，使用chrome """
        # 启动浏览器
        # firefox_profile = webdriver.FirefoxProfile()
        # 禁止加载image
        # firefox_profile.set_preference('permissions.default.stylesheet', 2)
        # firefox_profile.set_preference('permissions.default.image', 2)
        # firefox_profile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        # 代理
        from selenium.webdriver.chrome.options import Options

        if proxy:
            myProxy = "%s:%s" % (proxy.host, proxy.port)
            ff_proxy = Proxy(
                {
                    "proxyType": ProxyType.MANUAL,
                    "httpProxy": myProxy,
                    "ftpProxy": myProxy,
                    "sslProxy": myProxy,
                    "noProxy": "",
                }
            )

            browser = webdriver.Chrome(
                "chromedriver.exe"
            )  # proxy=ff_proxy
        else:
            chrome_options = Options()
            if os.path.exists('head.config'):
                with open('head.config', 'r') as hf:
                    head_flag = int(hf.readline())
            else:
                head_flag = 1
                with open('head.config', 'w') as hf:
                    hf.write('1')
            if head_flag:
                chrome_options.add_argument("--headless")
            browser = webdriver.Chrome(
                r"chromedriver.exe",
                options=chrome_options,
            )

        return browser

    @staticmethod
    def download_onehref(browser, url="", path_name=""):
        # logger.info('开始下载链接：%s' % url)
        if url:
            browser.get(url)

        js = """ return document.documentElement.innerHTML; """
        element_t = browser.find_element_by_xpath(
            '//div[@class="all-con"]/div[@class="container"]'
        )
        metadata = element_t.find_element_by_xpath('.//div[@class="t-container"]')
        title = meta_src_href = meta_src_name = meta_time = ""
        try:
            if metadata:
                title = metadata.find_element_by_xpath(
                    './/div[@class="t-container-title"]/h3'
                ).text.strip()
                meta_info = metadata.find_element_by_xpath(
                    './/div[@class="t-container-metadata"]/div[@class="metadata-info"]'
                )
                try:
                    meta_src = meta_info.find_element_by_xpath(
                        './/span[@class="source"]/a'
                    )
                except:
                    meta_src = meta_info.find_element_by_xpath(
                        './/span[@class="source"]'
                    )
                try:
                    meta_src_href = meta_src.get_attribute("href")
                except:
                    pass
                meta_src_name = meta_src.text.strip()
                meta_time = meta_info.find_element_by_xpath(
                    './/p[@class="time"]'
                ).text.strip()
            else:
                logger.info("url不存在meta数据。href:%s" % browser.current_url)
        except:
            logger.info("meta数据下载失败，继续尝试下载文本。href:%s" % browser.current_url)
            # meta_author = meta_info[0].find_element_by_xpath('.//span[@class="author"]/a')
        try:
            text_container = element_t.find_element_by_xpath(
                './/div[@class="b-container"]/div[@class="l-container"]//section[@data-type="rtext"]'
            )
            text_list = [
                item.text.strip()
                for item in text_container.find_elements_by_xpath(".//p")
                if item.text and item.text.strip()
            ]
        except:
            logger.info("文本数据下载失败，停止此次下载。href:%s" % browser.current_url)
            return
        cont_sbf = title + meta_time
        if cont_sbf in sbf_title:
            logger.info('相同标题、相同时间的新闻已下载过！')
            return False
        # if meta_src_href in sites_deque:
        #     logger.info('相同地址的文章已下载过！')
        #     return False
        file_name = str(int(time.time() * 1000)) + ".txt"
        path_ = r"../spider_result/%s" % path_name
        if not os.path.exists(path_):
            os.makedirs(path_)
        file_path = os.path.join(path_, file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("标题：%s\n" % title)
                f.write("类型：%s\n" % path_name)
                f.write("类别：涉我动态\n")
                # f.write("来源链接：%s\n" % meta_src_href)
                if meta_src_name.startswith('来源'):
                    meta_src_name = meta_src_name[3:]
                f.write("来源：%s\n" % meta_src_name)
                f.write("发文时间：%s\n\n" % meta_time)
                for elem in text_list:
                    f.write("  " + elem + "\n")
                f.write('【数据室搜集】')
            sbf_title.add(cont_sbf)
            # sites_deque.append(meta_src_href)
        except UnicodeError as ue:
            logger.error(ue)
            logger.info("url下载失败。href:%s" % browser.current_url)

    def download(self, url, path_name=""):
        browser = self.browser
        try:
            browser.get(url)
        except:
            logger.error('获取当前url失败')
            browser.quit()
            return
        # js = """ return document.documentElement.innerHTML; """
        # body = browser.execute_script(js)
        # htmlparser = etree.HTMLParser()
        # tree = etree.parse(StringIO(body), htmlparser)
        time.sleep(randint(5, 8))
        element = browser.find_elements_by_xpath('//div[@class="m-recommend"]//li/a')
        if len(element) == 0:
            logger.error("error! can't find m-recommend in %s" % url)
            browser.quit()
            return []
        try:
            href_title = [
                (
                    item.get_attribute("href"),
                    item.find_element_by_xpath(".//h4").text.strip(),
                )
                for item in element
            ]
            # titles = [item.find_element_by_xpath('.//h4').text.strip() for item in element]
            # sources = [item.find_element_by_xpath('.//span[@class="original"]').text.strip() for item in element]
            # times = [item.find_element_by_xpath('.//span[@class="time"]').text.strip() for item in element]
        except:
            logger.error("解析href和title失败")
            # print("解析href和title失败")
        time.sleep(randint(5, 10))
        # logger.info("打开第一个窗口")
        # logger.info("开始下载啦啦啦啦。。。")
        for iter_, item in enumerate(element[:10]):
            try:
                if len(browser.window_handles) > 0:
                    browser.switch_to.window(browser.window_handles[0])
                else:
                    try:
                        browser.delete_all_cookies()
                        browser.quit()
                    except:
                        logger.error("window has closed!")
                    browser = self.browser
                    browser.get(url)
            except:
                try:
                    browser.delete_all_cookies()
                    browser.quit()
                except:
                    logger.error("window has closed!")
                browser = self.browser
                browser.get(url)
            # print("切换到主窗口")
            try:
                item.click()
            except:
                logger.error('click 出错')
                continue
            new_handler = browser.window_handles[-1]
            browser.switch_to.window(new_handler)
            # print("切换到新窗口")
            time.sleep(randint(6, 15))
            # print(browser.current_url)
            # try:
            #     url_sbf = browser.current_url
            # except:
            #     try:
            #         browser.delete_all_cookies()
            #         browser.quit()
            #     except:
            #         logger.info("window has closed!")
            #     finally:
            #         return False
            if browser.current_url in sbf:
                logger.info('%s 已下载，关闭窗口' % browser.current_url)
                # print('%s 已下载，关闭窗口' % browser.current_url)
                browser.close()

            else:
                try:
                    sbf.add(browser.current_url)
                    sites_deque.append(browser.current_url)
                    HQWDownParser.download_onehref(browser, "", path_name)
                except:
                    logger.error(
                        "Download error. title:%s"
                        % item.find_element_by_xpath(".//h4").text.strip()
                    )
                # print('关闭当前窗口')
                browser.close()
                time.sleep(randint(10, 15))
        browser.quit()

        # hrefs = [item for item in tree.xpath('//div[@class="m-recommend"]//li/a/@href')]
        #
        # times = [item for item in tree.xpath('//div[@class="m-recommend"]//li/a//span')]


if __name__ == "__main__":

    with HQWDownParser() as dp:
        dp.download("https://uav.huanqiu.com/hyg")
        # dp.__exit__()
