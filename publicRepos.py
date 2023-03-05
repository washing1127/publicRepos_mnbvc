import os
import sys
import json
import time
import requests
import argparse
import traceback

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

def crawl_github(params):
    url = "https://api.github.com/repositories"
    headers = {
        "Accept": "application/vnd.github+json",
        # "Authorization": "Bearer " + GITHUB_AK,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.get(url, params=params, headers=headers)
    

def github_run():
    repository_id = log_data[platform].get("repository_id", 0)
    url = "https://api.github.com/repositories"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + GITHUB_AK,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    while True:
        params = {
            "since": repository_id,
        }
        resp = requests.get(url, headers=headers, params=params) # 获取 100 个仓库的简要信息
        json_list = resp.json()
        idx = 0
        err_counter = 0 # 设定 error_counter，当一个仓库请求失败时，会至多 3 次重复请求该仓库，超过 3 次则跳过该仓库。
        while idx < len(json_list):
            item = json_list[idx]
            try:
                if "url" in item.keys():
                    repos_url = item['url']
                    resp2 = requests.get(repos_url, headers=headers) # 请求 1 个仓库详细信息
                    if resp2.status_code != 200:
                        with open(save_error_file, 'a', encoding='utf-8')as a:
                            a.write(f"URL: {repos_url}\tSTATUS CODE: {resp2.status_code}\tRESPONSE DATA: {resp2.text}\tINTACT ITEM: {json.dumps(item, ensure_ascii=False)}\n")
                    else:
                        repos = resp2.json()
                        with open(save_file, "a", encoding="utf-8")as a:
                            a.write(resp2.text + "\n")
                        log_data[platform]['repository_id'] = repository_id = max(repos['id'], repository_id)
                        with open(log_file,'w',encoding='utf-8')as w:
                            w.write(json.dumps(log_data, ensure_ascii=False))
                        print(
                            "Crawled a repository:\n"
                            f"\tID: {repos['id']}\n"
                            f"\tREPOSITORY NAME: {repos['name']}\n"
                            f"\tOWNER: {repos['owner'].get('login', '')}"
                        )
                idx += 1
                err_counter = 0
            except :
                print("===========================")
                traceback.print_exc()
                print("===========================")
                print(item)
                err_counter += 1
                if err_counter > 3:
                    idx += 1
                else:
                    time.sleep(2)
                # sys.exit(2)
        # time.sleep(2)

def gitee_run():
    # page_num = log_data[platform].get("page_num", 1)
    # url = "https://gitee.com/api/v5/user/repos"
    # headers = {
    #     "Content-Type": "application/json",
    #     "charset": "UTF-8",
    # }
    # while True:
    #     params = {
    #         "access_token": GITEE_AK,
    #         "visibility": "public",  # 只爬取公开的仓库
    #         "sort": "created",       # 按照创建时间排序
    #         "direction": "asc",      # 增序，及越早越靠前
    #         "page": page_num,
    #         "per_page": 100,
    #     }
    #     resp = requests.get(url, headers=headers, params=params)
    #     json_list = resp.json()
    print("Gitee is not OK yet.")
    sys.exit(1)
        


def main():
    global platform, save_file, save_error_file, log_data
    args = parse_args()
    platform = args.platform.lower()
    from_new = args.new
    save_file = platform + "-repositories.txt"
    save_error_file = platform + "-error_repositories.txt"
    # log 文件不存在，代表重头开始爬取
    if not os.path.exists(log_file):
        log_data = {
            'github': dict(),
            'gitee': dict(),
        }
    else:
        with open(log_file,"r",encoding="utf-8")as r:
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
    global GITEE_AK, GITHUB_AK
    global log_file
    GITHUB_AK = ""
    GITEE_AK = ""
    log_file = "./.log"
    main()