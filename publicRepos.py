import os
import sys
import json
import time
import random
import requests
import argparse
import threading

from queue import Queue

from constant import *

class CrawlThread(threading.Thread):
    def __init__(self, queue, crawler, tid):
        threading.Thread.__init__(self)
        self.queue = queue
        self.crawler = crawler
        self.name = f"Thread Number: {tid:02d}"

    def run(self):
        while True:
            item = self.queue.get()
            self.crawler(item, self.name)
            self.queue.task_done()

def find_range(num):
    # 以 100万为单位，找当前从仓库在那个范围
    size = 1000000
    start = num // size * size
    end = start + size
    return f"{start}-{end}"

def github_repos_crawler(item, thread_name, retry_times=0):
    global repository_id, ak_idx
    if retry_times > RETRY_TIME:
        logging.error(
            f"超过{RETRY_TIME}次请求仍未成功\n"
            f"\tURL: {item['url']}\n"
        )
        return
    try:
        url = item['url']
        resp = requests.get(url, headers=new_headers())
        if resp.status_code != 200:
            with open(find_range(repository_id)+'_error', 'a', encoding='utf-8')as a:
                a.write(f"URL: {url}\tSTATUS CODE: {resp.status_code}\tRESPONSE DATA: {resp.text}\tINTACT ITEM: {json.dumps(item, ensure_ascii=False)}\n")
        else:
            with open(find_range(repository_id), 'a', encoding='utf-8')as a:
                a.write(resp.text + '\n')
            repos = resp.json()
            if repos['id'] > repository_id:
                log_data[find_range(repository_id)] = repos['id']
                repository_id = repos['id']
                with open(LOG_FILE, 'w', encoding='utf-8')as w:
                    w.write(json.dumps(log_data, ensure_ascii=False))
            print(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} Crawled a repository by {thread_name}:\n"
                f"\tID: {repos['id']}\n"
                f"\tREPOSITORY NAME: {repos['name']}\n"
                f"\tOWNER: {repos['owner'].get('login', '')}\n"
                f"\tTOKEN USED: number {ak_idx}"
            )
    except Exception as e:
        print(e)
        github_repos_crawler(item, thread_name, retry_times=retry_times+1)

def new_headers():
    global ak_idx
    while True:
        ak_idx = (ak_idx + 1) % len(GITHUB_TOKENS)
        token = GITHUB_TOKENS[ak_idx]
        if time.time() - github_tokenTime_dict[token] > TOKEN_FREQUENCY:
            github_tokenTime_dict[token] = time.time()
            break
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return headers

def github_run():
    global ak_idx, repository_id, github_tokenTime_dict, log_data

    # log 文件不存在，代表重头开始爬取
    if not os.path.exists(LOG_FILE):
        log_data = dict()
    else:
        with open(LOG_FILE,"r",encoding="utf-8")as r:
            log_data = json.loads(r.read())

    ak_idx = random.randint(0, len(GITHUB_TOKENS)-1)  # 随机从某个 ak 开始循环使用
    repository_id = log_data.get(find_range(START), START)  # 看该区间爬到哪儿了
    github_tokenTime_dict = {token: 0 for token in GITHUB_TOKENS}
    url = "https://api.github.com/repositories"
    print("GitHub Spider is Running...")
    while True:
        if repository_id >= END:
            print(f"已经爬取到{repository_id}，自动结束")
            sys.exit(0)
        params = {
            "since": repository_id,
        }
        resp = requests.get(url, headers=new_headers(), params=params) # 获取 100 个仓库的简要信息
        json_list = resp.json()
        if not isinstance(json_list, list):
            print("="*50)
            print(json_list)
            print("="*50)
            print("获取失败")
            sys.exit(1)
        queue = Queue()
        for item in json_list:
            if isinstance(item, dict) and "url" in item.keys():
                iid = item['id']
                if log_data[find_range(iid)] > iid: continue# 说明该区间已经爬取过该 id
                queue.put(item)

        for tid in range(THREADS_NUM):
            thread = CrawlThread(queue, github_repos_crawler, tid+1)
            thread.daemon = True
            thread.start()

        queue.join()

def main():
    github_run()

if __name__ == '__main__':
    main()