# GITHUB_TOKENS: github 的 token，list
GITHUB_TOKENS = []

# GITEE_TOKENS: gitee 的 token，list
# GITEE_TOKENS = [
#     "",
# ]

# THREADS_NUM: 线程数，int
THREADS_NUM = 1

# TOKEN_FREQUENCY: 一个 token 最短请求间隔，秒，int
TOKEN_FREQUENCY = 1

# RETRY_TIME: 当一个仓库详情获取失败时，重试的次数，int
RETRY_TIME = 3

# LOG_FILE: 用来记录爬取进度等信息，str
LOG_FILE = "./.log"

# logging 相关配置，用来记录错误信息，object
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
    datefmt='%a %d %b %Y %H:%M:%S',
    filename='crawl_log.log',
)