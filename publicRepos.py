import requests
import argparse

GITHUB_AK = ""
GITEE_AK = ""

def parse_args():
    parser = argparse.ArgumentParser(
        description="根据参数，获取GitHub/Gitee的所有/某个时间段/今天的所有开源仓库信息"
    )
    parser.add_argument(
        '-p', '--platform',
        required=True,
        help='指定要爬取的平台，GitHub（github）或者Gitee（gitee）'
    )
    parser.add_argument(
        '-s', '--starttime',
        help='指定要爬取的仓库的最早创建时间范围，比如（20000101）'
    )
    parser.add_argument(
        '-e', '--endtime',
        help='指定要爬取的仓库的最晚创建时间范围，比如（20220202）'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=0,
        help='限制爬取的页数，默认为0，表示不限制'
    )

    return parser.parse_args()

class GitSpider():
    def __init__(self) -> None:
        self.base_url = ""
        self.crawl_url = ""
        self.ak = ""
        self.param = {}
        self.page_limit = 0

    def save_repos(self, repo_list=None):
        if not repo_list: repo_list = list()
        for repo in repo_list:
            print(repo['name'], repo['created_at'])
        print(repo.keys())

    def get_one_page(self):
        resp = requests.get(self.crawl_url, params=self.param)
        repo_list = resp.json()
        self.save_repos(repo_list)
        if 'next' in resp.links:
            self.crawl_url = resp['next']['url']
            return True
        return False

    def run(self):
        while self.page_limit != 0:
            self.page_limit = max(0, self.page_limit-1)
            has_more = self.get_one_page()
            if not has_more: break

class GitHub(GitSpider):
    def __init__(self, st, et) -> None:
        super().__init__()
        self.url = 'https://api.github.com/repositories'
        self.param['per_page'] = 100
        if st: self.param['']
                



class Gitee(GitSpider):
    pass

if __name__ == "__main__":
    args = parse_args()
    platform = args.platform
    start_time = args.starttime
    end_time = args.endtime
    page_limit = args.limit
    print(platform)
    print(start_time)
    print(end_time)
    print(page_limit)




# # Set the API endpoint
# url = 'https://api.github.com/repositories'

# # Set the headers for the request
# headers = {'Authorization': 'Bearer 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'}

# params = {"per_page": 100}
# repos = []

# while True:
#     response = requests.get(url, params=params)
#     if response.status_code == 200:
#         repos.extend(response.json())
#         # Check if there are more pages to retrieve
#         if "next" in response.links:
#             url = response.links["next"]["url"]
#         else:
#             break
#     else:
#         print("Failed to retrieve public repositories. Status code:", response.status_code)
#         break
#     break

# for repo in repos:
#     print(repo["name"])


# if __name__ == "__main__":
