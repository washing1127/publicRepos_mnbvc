# GITHUB_TOKENS: github 的 token，list
GITHUB_TOKENS = [
    "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",
]

# 爬取的仓库 id 区间，[START, END)
START = 999900
END =  1000100

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
    level=logging.ERROR,
    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
    datefmt='%a %d %b %Y %H:%M:%S',
    filename='err_log.log',
)