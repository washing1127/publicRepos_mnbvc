# logging 相关配置，用来记录错误信息，object
import logging
import json
import os
import random
import sys
import threading
import time
from queue import Queue
import argparse
import requests
import jsonlines
import time

# TOKEN_FREQUENCY: 一个 token 最短请求间隔，秒，int
TOKEN_FREQUENCY = 1

# RETRY_TIME: 当一个仓库详情获取失败时，重试的次数，int
RETRY_TIME = 10

# GITHUB_TOKENS: github 的 token，list
GITHUB_TOKENS = []


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
            with open(find_range(repository_id) + '_error', 'a', encoding='utf-8')as a:
                a.write(
                    f"URL: {url}\tSTATUS CODE: {resp.status_code}\tRESPONSE DATA: {resp.text}\tINTACT ITEM: {json.dumps(item, ensure_ascii=False)}\n")
        else:
            with jsonlines.open(find_range(repository_id) + '.jsonl', mode='a') as repo_meta_file:
                repo_meta_file.write(resp.text)
            repos = resp.json()
            if repos['id'] > repository_id:
                log_data[find_range(repository_id)] = repos['id']
                repository_id = repos['id']
            logging.info(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} Crawled a repository by {thread_name}:\n"
                f"\tID: {repos['id']}\n"
                f"\tREPOSITORY NAME: {repos['name']}\n"
                f"\tOWNER: {repos['owner'].get('login', '')}\n"
                f"\tTOKEN USED: number {ak_idx}"
            )
    except Exception as e:
        print(e)
        github_repos_crawler(item, thread_name, retry_times=retry_times + 1)


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


def github_run(start, end, threads_num):
    logging.info("start now")
    global ak_idx, repository_id, github_tokenTime_dict, log_data

    log_data = dict()

    ak_idx = random.randint(0, len(GITHUB_TOKENS) - 1)  # 随机从某个 ak 开始循环使用
    repository_id = log_data.get(find_range(start), start)  # 看该区间爬到哪儿了
    github_tokenTime_dict = {token: 0 for token in GITHUB_TOKENS}
    url = "https://api.github.com/repositories"
    print("GitHub Spider is Running...")

    while True:
        if repository_id >= end:
            print(f"已经爬取到{repository_id}，自动结束")
            sys.exit(0)
        params = {
            "since": repository_id,
        }
        resp = requests.get(url, headers=new_headers(), params=params)  # 获取 100 个仓库的简要信息
        json_list = resp.json()
        if not isinstance(json_list, list):
            print("=" * 50)
            print(json_list)
            print("=" * 50)
            print("获取失败")
            time.sleep(60)
        else:
            queue = Queue()
            for item in json_list:
                if isinstance(item, dict) and "url" in item.keys():
                    iid = item['id']
                    queue.put(item)
            for tid in range(threads_num):
                thread = CrawlThread(queue, github_repos_crawler, tid + 1)
                thread.daemon = True
                thread.start()
            queue.join()


def gitee_run():
    print("骚瑞 ~ Gitee is not OK yet.")


def main(platform, github_tokens_file, start, end, threads_num, log_file):
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)s %(levelname)s %(message)s',
        datefmt='%a %d %b %Y %H:%M:%S',
        filename=log_file
    )

    # 判断获取github还是gitee的数据
    if platform == 'github':
        if not os.path.exists(github_tokens_file):
            print("存放github上token的文件不存在：" + github_tokens_file)
        else:
            # 打开文件
            with open(github_tokens_file, "r") as file:
                # 逐行读取数据
                for line in file:
                    # 去掉行末的换行符，并将数据添加到列表中
                    GITHUB_TOKENS.append(line.strip())
            github_run(start, end, threads_num)
    if platform == 'gitee':
        gitee_run()


if __name__ == '__main__':
    # 设置参数解析器
    parser = argparse.ArgumentParser()
    # 添加可选参数，指定指定要爬取的平台，github 或 gitee
    parser.add_argument('-p', '--platform', type=str, default="github", help="指定指定要爬取的平台，github或gitee,默认为github")
    # 添加可选参数，指定包含github token的文件，文件内一行一个token，默认为github_tokens.txt
    parser.add_argument('--github_tokens_file', type=str, default="./github_tokens.txt",
                        help="包含github token的文件，文件内一行一个token，默认为github_tokens.txt")
    # 添加可选参数，指定爬取的仓库id开始位置，默认为1
    parser.add_argument('--start', type=int, default=1, help="爬取的仓库id区间，[start, end)，start默认为1")
    # 添加可选参数，指定爬取的仓库id结束位置，默认为1000000
    parser.add_argument('--end', type=int, default=1000000, help="爬取的仓库id区间，[start, end)，end默认为一百万")
    # 添加可选参数，指定线程数，默认为1
    parser.add_argument('--threads_num', type=int, default=1, help="线程数，默认为1")
    # 添加可选参数，指定用来记录爬取进度等信息的log地址，默认为publicRepos.log
    parser.add_argument('--log_file', type=str, default="./publicRepos.log",
                        help="指定用来记录爬取进度等信息的log地址，默认为publicRepos.log")
    # 解析参数
    args = parser.parse_args()
    # 调用main函数

    main(args.platform, args.github_tokens_file, args.start, args.end, args.threads_num, args.log_file)
