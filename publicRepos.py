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
        resp = requests.get(url, headers=new_headers('github'))
        if resp.status_code != 200:
            with open(save_error_file, 'a', encoding='utf-8')as a:
                a.write(f"URL: {url}\tSTATUS CODE: {resp.status_code}\tRESPONSE DATA: {resp.text}\tINTACT ITEM: {json.dumps(item, ensure_ascii=False)}\n")
        else:
            with open(save_file, 'a', encoding='utf-8')as a:
                a.write(resp.text + '\n')
            repos = resp.json()
            if repos['id'] > repository_id:
                log_data[platform]['repository_id'] = repository_id = repos['id']
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

def parse_args():
    parser = argparse.ArgumentParser(
        description="获取 GitHub/Gitee 中所有用户的所有开源仓库信息"
    )
    parser.add_argument(
        '-p', '--platform',
        required=True,
        help='指定要爬取的平台，GitHub 或 Gitee'
    )
    parser.add_argument(
        '--new',
        default=False,
        action="store_true",
        help='是否完全从头零开始爬取所有信息, 默认为 False'
    )
    return parser.parse_args()

def new_headers(platform):
    global ak_idx
    if platform == 'github':
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
    global ak_idx, repository_id, github_tokenTime_dict
    ak_idx = random.randint(0, len(GITHUB_TOKENS)-1)  # 随机从某个 ak 开始循环使用
    repository_id = log_data[platform].get("repository_id", 0)
    github_tokenTime_dict = {token: 0 for token in GITHUB_TOKENS}
    url = "https://api.github.com/repositories"
    while True:
        params = {
            "since": repository_id,
        }
        resp = requests.get(url, headers=new_headers('github'), params=params) # 获取 100 个仓库的简要信息
        json_list = resp.json()
        queue = Queue()
        for item in json_list:
            if isinstance(item, dict) and "url" in item.keys():
                queue.put(item)

        for tid in range(THREADS_NUM):
            thread = CrawlThread(queue, github_repos_crawler, tid+1)
            thread.daemon = True
            thread.start()

        queue.join()

def gitee_run():
    print("骚瑞 ~ Gitee is not OK yet.")
    sys.exit(1)

def main():
    global platform, save_file, save_error_file, log_data
    args = parse_args()
    platform = args.platform.lower()
    from_new = args.new
    save_file = platform + "-repositories.txt"
    save_error_file = platform + "-error_repositories.txt"
    # log 文件不存在，代表重头开始爬取
    if not os.path.exists(LOG_FILE):
        log_data = {
            'github': dict(),
            'gitee': dict(),
        }
    else:
        with open(LOG_FILE,"r",encoding="utf-8")as r:
            log_data = json.loads(r.read())
        # 设定了 --new 参数，表示重头爬取（如果之前有数据，会将之前的数据删掉）
        if from_new is True:
            if os.path.exists(save_file): os.unlink(save_file)
            if os.path.exists(save_error_file): os.unlink(save_error_file)
            log_data[platform] = dict()
    if platform == 'github':
        github_run()
    elif platform == 'gitee':
        gitee_run()
    else:
        raise ValueError(f"没有找到 {platform} 对应的爬虫")

if __name__ == '__main__':
    main()