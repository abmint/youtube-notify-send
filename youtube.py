#!/usr/bin/python3

import os
import re
import ast
import time
import subprocess
import urllib.request

FAVORITE = """
# HikakinTV
https://www.youtube.com/channel/UCZf__ehlCEBPop-_sldpBUQ
# はじめしゃちょー
https://www.youtube.com/channel/UCgMPP6RRjktV7krOfyUewqw
# KADOKAWAanime
https://www.youtube.com/channel/UCY5fcqgSrQItPAX_Z5Frmwg
# ABEMAニュース
https://www.youtube.com/channel/UCk5a240pQsTVT9CWPnTyIJw
"""

TMP_DICT = os.path.join(os.path.dirname(__file__), f"{os.path.splitext(os.path.basename(__file__))[0]}_old.txt")

if os.path.exists(TMP_DICT):
    with open(TMP_DICT, mode="r") as f:
        DICT_OLD = ast.literal_eval(f.read())
else:
    DICT_OLD = None

def html_notify(list_detail):
    text = "\n\n".join([f"{x['url']}" for x in list_detail]) + "\n\n" + "\n\n".join([f"{x['title']}" for x in list_detail])
    if len(list_detail) == 1:
        subprocess.run(f"notify-send '{list_detail[0]['author']}' '{text}'", shell=True)
    else:
        subprocess.run(f"notify-send '{list_detail[0]['author']} 更新が{len(list_detail)}件あります' '{text}'", shell=True)

def html_scraping(subscribe_id, response):
    list_entry = re.findall("<entry>[\s\S]*?</entry>", response)

    list_detail = []
    for x in list_entry:
        author = re.search('<name>(.*?)</name>', x).group(1)
        title = re.search('<title>(.*?)</title>', x).group(1)
        url = re.search('<link rel="alternate" href="(.*?)"/>', x).group(1)
        list_detail.append(dict(author=author,title=title,url=url))

    if DICT_OLD is not None and DICT_OLD.get(subscribe_id):
        past_index = (lambda x:1 if x[0] == 0 else x[0])([list_detail.index(x) for x in list_detail if all([DICT_OLD[subscribe_id]['title'] == x['title'], DICT_OLD[subscribe_id]['url'] == x['url']])] or [1])

        if list_detail[0] != DICT_OLD.get(subscribe_id):
            html_notify(list_detail[:past_index])
    else:
        html_notify(list_detail[:1])

    return list_detail[0]

def url_convert(favorite):
    list_favorite, list_id, list_url = [], [], []

    for x in re.findall("https://www.youtube.com/.+", favorite):
        list_favorite.append(re.search("(https://www.youtube.com/channel/[a-zA-Z0-9-_%]+)/?", x).group(1))

    for x in sorted(set(list_favorite), reverse=False):
        temp_a = re.search("https://www.youtube.com/channel/([a-zA-Z0-9-_%]+)", x).group(1)
        temp_b = f"https://www.youtube.com/feeds/videos.xml?channel_id={temp_a}"
        list_id.append(temp_a)
        list_url.append(temp_b)

    return zip(list_id, list_url)

def connection_status(subscribe_id, url):
    for x in range(3):                           # ループの回数
        try:
            response = urllib.request.urlopen(url)
            response_html = response.read().decode("utf-8")
            response_status = response.getcode()
            response.close()
        except:
            response = None                      # ネットワークが無効だった場合は、変数responseの値をNoneにする
        else:
            break                                # ネットワークが有効だった場合はbreakでループを抜ける
        finally:
            time.sleep(5)                        # ループの間隔
    else:
        subprocess.run(f"notify-send 'YouTubeに接続できませんでした' '{url}'", shell=True)

    if response is None:                         # ネットワークが無効だった場合
        return None                              # 辞書の値をNoneにする
    elif response_status == 200:                 # ネットワークが有効かつ、ステータスコードが200だった場合
        return html_scraping(subscribe_id, response_html)
    elif response_status != 200:                 # ネットワークが有効かつ、ステータスコードが200以外だった場合
        subprocess.run(f"notify-send 'ステータスコードが{response_status}でした' '{url}'", shell=True)
        return None                              # 辞書の値をNoneにする

DICT_NEW = {list_id:connection_status(list_id, list_url) for list_id, list_url in url_convert(FAVORITE)}

[DICT_NEW.update(zip([x],[DICT_OLD.get(x)])) for x in DICT_NEW.keys() if DICT_NEW[x] is None and DICT_OLD is not None]

with open(TMP_DICT, mode="w") as f:
    f.write(str(DICT_NEW))
