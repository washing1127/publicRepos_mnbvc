# publicRepos_mnbvc 

## 项目描述

本项目主要用于获取 GitHub 中的所有（或者后续新增）开源仓库信息，为后续的开源代码获取做准备。

## 前期准备

### AK获取

```mermaid
graph LR;
A[Settings] --> B[Developer Settings];
B[Developer Settings] --> C[Personal access tokens];
C[Personal access tokens] --> D[Generate new token];
```

### 依赖安装

```shell
pip install requests
```

## 运行爬虫

### 参数介绍

- `-p/--platform`: 指定要爬取的平台，GitHub 或 Gitee（Gitee 暂未完成）
- `--new`: 是否完全从头开始爬取所有信息，默认为 `False`

### 爬取逻辑

**接口地址：** `https://api.github.com/repositories`

1. 指定 `since=id` 参数，请求该 id 后的 100 个仓库简要信息
2. 依次请求仓库简要信息中的详情链接，获取仓库详细信息并保存

### 输出介绍

- `num1-num2`
    - github 的仓库信息，以行为单位，每一行是一个仓库，json 格式
    - 文件名是其中包含的仓库的最小 id 和最大 id
- `num1-num2_error`
    - 请求无法获取正确范围的仓库，以行为单位，由 `\t` 连接。分别为
        1. 仓库信息 API 地址（url）
        2. 请求得到的响应的状态码（number）
        3. 请求得到的相应数据（json）
        4. 请求来源的 item 信息（json）

### 运行代码

1. 将获取到的 AK 填入 `constant.py` 文件对应位置
2. 将要爬取的范围填入 `constant.py`，若其中有区间此前爬过，但未爬完，会选择续爬此前的记录，防止有遗漏
3. 运行代码： `python publicRepos.py`
