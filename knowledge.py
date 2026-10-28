# llmc_tools.knowledge.py

import requests

import subprocess
from collections import defaultdict
from pathlib import Path


def news() -> dict:
    try:
        res = requests.get('https://private.balus.xyz/news/kanaloco.json')
        if res.status_code != 200:
            res = requests.get('http://192.168.1.201/news/kanaloco.json')
            if res.status_code != 200:
                return {"result": "failed...server error"}
        lst = res.json()[-20:]
        for d in lst:
            d['href'] = f"https://kanaloco.jp{d['href']}"
        lst.reverse()
        return {"result": "success", "data": lst}
    except Exception as e:
        return {"result": f"failed{e}"}


def retrieve_rg(keyword: str, max_results: int = 10, path: str = ".") -> dict:
    """
    ripgrepで検索し、ファイル単位で結果を返す。

    content: そのファイルで最初にヒットした行
    source: ファイル名
    score: ヒット行数 / ファイル全行数
    """

    try:
        proc = subprocess.run(
            [
                "rg",
                "--line-number",
                "--no-heading",
                "--with-filename",
                keyword,
                path,
            ],
            capture_output=True,
            text=True,
        )
    except Exception:
        return {"result": "failed", "results": []}

    # rgは「マッチなし」でreturncode=1になるので、これはエラー扱いしない
    if proc.returncode not in (0, 1):
        return {
            "result": "failed",
            "error": proc.stderr.strip(),
            "results": [],
        }

    matches = defaultdict(list)

    for line in proc.stdout.splitlines():
        # filename:line-number:content
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue

        filename, lineno, content = parts

        try:
            lineno = int(lineno)
        except ValueError:
            continue

        matches[filename].append({
            "line": lineno,
            "content": content.strip(),
        })

    results = []

    for filename, hits in matches.items():
        try:
            with open(filename, "r", encoding="utf-8", errors="replace") as f:
                total_lines = sum(1 for _ in f)
        except OSError:
            continue

        if total_lines == 0:
            continue

        matched_lines = len({
            hit["line"]
            for hit in hits
        })

        score = matched_lines / total_lines

        first_hit = min(hits, key=lambda x: x["line"])

        results.append({
            "content": first_hit["content"],
            "source": filename,
            "line": first_hit["line"],
            "score": score,
            "matches": matched_lines,
            "total_lines": total_lines,
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    return {
        "result": "success",
        "results": results[:max_results],
    }

FUNCTIONS = {
    "news": news,
    "retrieve_rg": retrieve_rg,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "news",
            "description": "プライベートにスクレイピングしている共同通信記事２０件",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_rg",
            "description": "ripgrepで検索し、ファイル単位で結果を返す。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "rgに渡すキーワード"
                    },
                    "max_result": {
                        "type": "integer",
                        "description": "返す最大件数"
                    },
                    "path": {
                        "type": "string",
                        "description": "対象ディレクトリ"
                    },
                },
                "required": ["keyword",],
                "additionalProperties": False
            }
        }
    },
]
