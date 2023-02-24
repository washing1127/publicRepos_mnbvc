import os
import json
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
        resp = requests.get(url, headers=headers, params=params)
        json_list = resp.json()
        for item in json_list:
            try:
                if "url" in item.keys():
                    url = item['url']
                    resp2 = requests.get(url, headers=headers)
                    repos = resp2.json()
                    with open(save_file, "a", encoding="utf-8")as a:
                        a.write(resp2.text + "\n")
                    log_data[platform]['repository_id'] = max(repos['id'], repository_id)
                    with open(log_file,'w',encoding='utf-8')as w:
                        w.write(json.dumps(log_data, ensure_ascii=False))
                    print(
                        "Crawled a repository:\n"
                        f"\tID: {repos['id']}\n"
                        f"\tREPOSITORY NAME: {repos['name']}\n"
                        f"\tOWNER: {repos['owner'].get('login', '')}"
                    )
            except :
                print("===========================")
                traceback.print_exc()
                print("===========================")
                print(type(item))
                print("===========================")
                print(item)

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
        


def main():
    global platform, save_file, log_data
    args = parse_args()
    platform = args.platform.lower()
    from_new = args.new
    save_file = platform + "-repositories.txt"
    if not os.path.exists(log_file):
        log_data = {
            'github': dict(),
            'gitee': dict(),
        }
    else:
        with open(log_file,"r",encoding="utf-8")as r:
            log_data = json.loads(r.read())
        if from_new is True:
            os.unlink(save_file)
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
    GITHUB_AK = "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"
    GITEE_AK = "4dfd733af8dd6138e59728fa4f33ff55"
    log_file = "./.log"
    main()