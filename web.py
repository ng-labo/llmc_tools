# llmc_tools.web.py

import requests
import io, os, time
import requests
#from ddgs import DDGS
import llmc_tools.googlecs as googlecs
import trafilatura
from pypdf import PdfReader

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"

def web_search(query: str, max_results: int = 5) -> dict:
    """DuckDuckGoでキーワード検索"""
    print(f"🔍 検索中: 「{query}」")
    results_list = []
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            for r in results:
                results_list.append({
                    "title": r.get("title"),
                    "url": r.get("href")
                })
    """
    try:
        for t in googlecs.results([x for x in query.split() if x])['items']:
            results_list.append({"title": t['title'], "url": t['link']}) 
    except Exception as e:
        #print(f"❌ 検索エラー: {e}")
        return {"result": f"failed by {e}"}
    return {"result":"success", "output": results_list}

def web_fetch(url: str, max_chars=2000) -> dict:
    """URLにアクセスし、HTMLまたはPDFから本文テキストを抽出"""
    headers = {
        "User-Agent": UA
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()

        # PDFファイルの判定と抽出
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            print(f"📄 PDFを検知・解析中...")
            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
            extracted_text = ""
            for page in reader.pages:
                extracted_text += (page.extract_text() or "") + "\n"
            return {"result": "success", "content": extracted_text.strip()[:max_chars]}

        # 通常のHTMLページの解析 (trafilaturaでヘッダー・フッター等のノイズを除去)
        else:
            print(f"🌐 Webページを解析中...")
            extracted_text = trafilatura.extract(response.text)
            return {"result": "success", "content": extracted_text and extracted_text.strip()[:max_chars] or ""}

    except Exception as e:
        return {"result": f"{url} failed by {e}"}

from myid import FIRECRAWL_API_KEY

def web_fetch_firecrawl(url: str, max_char=2000) -> dict:
    """
    curl -X POST 'https://api.firecrawl.dev/v2/scrape' \
    -H 'Authorization: Bearer '$FIRECRAWL_API_KEY \
    -H 'Content-Type: application/json' \
    -d '{"url": "https://lavender.5ch.net/test/read.cgi/history/1762405370/l50"}'
    """
    headers = {
        "User-Agent": UA,
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
    }
    try:
        response = requests.post('https://api.firecrawl.dev/v2/scrape', headers=headers, data={"url": url})
        response.raise_for_status()
        j = response.json()
        return {
            "result": "success",
            "content": j["data"]["markdown"][:max_char]
        }

    except Exception as e:
        return {"result": f"{url} failed by {e}"}


FUNCTIONS = {
    "web_search": web_search,
    "web_fetch": web_fetch,
}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Webを検索して、関連する検索結果を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索クエリ"
                    },
                    "max_results": {
                       "type": "integer",
                       "description": "最大件数"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "指定されたWebページを取得し、本文をテキストとして返します。"
                           ".html, .pdfまで対応。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "取得するWebページのURL"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "返す本文の最大文字数"
                    }
                },
                "required": ["url"],
                "additionalProperties": False
            }
        }
    },
]
