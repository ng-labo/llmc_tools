#!/usr/bin/env python3
from myid import GOOGLE_CSE_API_KEY as API_KEY
from myid import GOOGLE_CSE_ID as CSE_ID
SAFE = 'active' # 'off'
headers = {"Referer":"https://private.balus.xyz/my.html"}
# curl -H "Referer: https://private.balus.xyz/my.html" "https://www.googleapis.com/customsearch/v1?key=$API_KEY&cx=$CSE_ID&q=naoki86star" | jq .

import requests, urllib.parse
import json, sys, traceback
import llmc

def results(q, safe=SAFE):
    excludewords = ('販売', '公式', '通販', '副業', 'コミック', '採用情報', )
    excludesites = ('youtube.com', 'rakuten.co.jp', 'amazon.co.jp', 'store.shopping.yahoo.co.jp', 'www.weblio.jp', )
    EXCSITES = "+".join(["-site:" + s for s in excludesites])
    QUERY = "+".join(q)
    for s in excludewords:
        q.append("-" + s)
    #for s in excludesites:
    #    q.append("-site:" + s)

    # t['link'], t['title'], t['snippet']
    return json.loads(requests.get(f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CSE_ID}&c2coff=1&safe={safe}&hq={EXCSITES}&q=" + urllib.parse.quote(QUERY), headers=headers).text)
