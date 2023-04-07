# logging 相关配置，用来记录错误信息，object
import logging
import json
import os
import random
import sys
import traceback
import time
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

# FILE_SIZE: 一个文件保存多少个仓库，默认为 100w
FILE_SIZE = 1000000

def find_range(num):
    # 以 100万为单位，找当前从仓库在那个范围
    size = FILE_SIZE
    start = num // size * size
    end = start + size
    return f"{start}-{end}"

def done(iid):
    # 记录爬取成功的仓库 id
    DONE_SET.add(iid)
    with open(find_range(iid)+'_done', 'a', encoding='utf-8')as a:
        a.write(f"{iid}\n")

def github_repos_crawler(item, retry_times=0):
    global ak_idx, github_tokenTime_dict
    try:
        url = item['url']
        iid = item['id']
        if retry_times > RETRY_TIME:
            logging.error(
                f"超过{RETRY_TIME}次请求仍未成功\n"
                f"\tID: {iid}"
                f"\tURL: {url}"
            )
            return
        resp = requests.get(url, headers=new_headers(), timeout=30)
        repos = resp.json()
        if resp.status_code == 401:  # 401 是暂时未找到，尝试再找
            github_repos_crawler(item, retry_times=retry_times+1)
        elif resp.status_code == 403 or resp.status_code == 451:
            if "Repository access blocked" in repos['message']: # 仓库被封锁，无法访问，同 404 一样处理
                logging.warning(
                    f"Repository access blocked:\n"
                    f"\tID: {iid}"
                    f"\tURL: {url}"
                )
                done(iid)
            elif "API rate limit" in repos["message"]: # API rate limit，调整一下 token 的时间，休息 1h
                token = GITHUB_TOKENS[ak_idx]
                github_tokenTime_dict[token] += 3600
                logging.warning(
                    f"Caught an api limit:\n"
                    f"\tLIMITED TOKEN: {token}"
                )
                github_repos_crawler(item, retry_times=retry_times)  # 因为 token 的问题而爬取失败，不增加 retry times
        elif resp.status_code == 404:  # 仓库找不到了，也算记录为已爬取
            logging.warning(
                f"Not found:\n"
                f"\tID: {iid}"
                f"\tURL: {url}"
            )
            done(iid)
        elif resp.status_code != 200:  # 其他错误响应码情况，记录到 error 里
            with open(find_range(iid) + '_error', 'a', encoding='utf-8')as a:
                a.write(
                    f"URL: {url}\tSTATUS CODE: {resp.status_code}\tRESPONSE DATA: {resp.text}\tINTACT ITEM: {json.dumps(item, ensure_ascii=False)}\n")
        else:
            with jsonlines.open(find_range(iid) + '.jsonl', mode='a') as repo_meta_file:
                repo_meta_file.write(resp.text)
            done(iid)

            logging.info(
                f"Crawled a repository:\n"
                f"\tID: {repos['id']}"
                f"\tREPOSITORY NAME: {repos['name']}"
                f"\tOWNER: {repos['owner'].get('login', '')}"
                f"\tTOKEN USED: number {ak_idx}"
            )
    except Exception as e:
        print(e)
        traceback.print_exc()
        github_repos_crawler(item, retry_times=retry_times + 1)

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

def github_run(start, end):    
    # 加载已经成功爬取过的仓库 id，防止重复爬取
    global DONE_SET
    DONE_SET = set()
    for num in range(start, end+FILE_SIZE, FILE_SIZE):
        file_name = find_range(num) + '_done'
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8')as r:
                DONE_SET.update([int(i) for i in r.readlines() if i.strip().isdigit()])
    logging.info("start now")
    global ak_idx, repository_id, github_tokenTime_dict
    repository_id = start
    ak_idx = random.randint(0, len(GITHUB_TOKENS) - 1)  # 随机从某个 ak 开始循环使用
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
        try:
            resp = requests.get(url, headers=new_headers(), params=params, timeout=30)  # 获取 100 个仓库的简要信息
            json_list = resp.json()
            if not isinstance(json_list, list):
                print("=" * 50)
                print(json_list)
                print("=" * 50)
                print("仓库列表获取失败")
                time.sleep(60)
            else:
                for item in json_list:
                    if isinstance(item, dict) and "url" in item.keys() and "id" in item.keys():
                        iid = item['id']
                        repository_id = max(repository_id, iid)
                        if iid not in DONE_SET:
                            github_repos_crawler(item)
        except Exception as e:
            print(e)
            time.sleep(600)


def gitee_run():
    print("骚瑞 ~ Gitee is not OK yet.")


def main(platform, github_tokens_file, start, end, log_file):
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(filename)s %(levelname)s\n%(message)s',
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
            github_run(start, end)
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
    # 添加可选参数，指定用来记录爬取进度等信息的log地址，默认为publicRepos.log
    parser.add_argument('--log_file', type=str, default="./publicRepos.log",
                        help="指定用来记录爬取进度等信息的log地址，默认为publicRepos.log")
    # 解析参数
    args = parser.parse_args()
    # 调用main函数
    main(args.platform, args.github_tokens_file, args.start, args.end, args.log_file)
