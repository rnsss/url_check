# -*- coding: utf-8 -*-
from threading import Thread  # 多线程库
from queue import Queue  # 队列库
import requests
import re  # 正则库
from openpyxl import Workbook  # 操作xlsx文件的库
import time
import cchardet  # 用来检测网页编码的库


class UrlCheck(Thread):
    def __init__(self, url_queue, list_result):
        super().__init__()
        self.url_queue = url_queue  # 要探测的url队列
        self.list_result = list_result  # 结果数组
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Baiduspider-render/2.0; +http://www.baidu.com/search/spider.html)'  # 百度爬虫的ua，可能绕过一些反爬
        }

    def run(self):
        while True:
            try:
                url = self.url_queue.get()
                if 'http' not in url:
                    url = "http://" + url
                req = self.download(url)
                if req:
                    title = re.search(r'<title>(.*?)</title>', req.text, re.I | re.S)
                    if title:
                        title = title.group(1)
                    else:
                        title = ""
                    list_result2 = [url, req.status_code, title]
                    self.list_result.append(list_result2)
                    print(url, '状态码：', req.status_code, '标题：', title)
            finally:
                self.url_queue.task_done()

    def download(self, url, retries=3):
        requests.packages.urllib3.disable_warnings()
        try:
            req = requests.get(url, headers=self.headers, timeout=3, verify=False)
        except requests.Timeout:
            req = None
            if retries > 0:
                return self.download(url, retries - 1)
        except requests.RequestException as err:
            req = None
            print(f"fetching {url} error: {err}")
        else:
            encoding = cchardet.detect(req.content)['encoding']
            req.encoding = encoding
        return req

if __name__ == '__main__':
    u_queue = Queue()
    checker = [k.strip() for k in open('urls.txt', encoding='utf-8')]
    list_result = []
    for url in checker:
        u_queue.put(url)
    print("开始探测：")
    for i in range(100):
        bdm = UrlCheck(u_queue, list_result)
        bdm.daemon = True
        bdm.start()

    u_queue.join()

    wb = Workbook()
    ws = wb.active
    ws.append(['url', '状态码', '标题'])
    for list1 in list_result:
        ws.append(list1)
    wb.save(time.strftime("%Y%m%d%H%M%S", time.localtime())+'.xlsx')

    print('done!')
