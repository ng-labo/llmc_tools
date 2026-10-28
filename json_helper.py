import subprocess
from pathlib import Path

def json_query(filename: str, query: str, max_chars: int = 12000):
    print("json_query", filename, query, max_chars)
    path = Path(filename).resolve()

    if not path.is_file() or path.suffix.lower() != ".json":
        return {"result": "failed", "error": "Invalid JSON file"}

    try:
        with path.open("rb") as f:
            proc = subprocess.run(
                ["jq", "-c", query],
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )

        if proc.returncode != 0:
            return {
                "result": "failed",
                "error": proc.stderr.decode("utf-8", errors="replace")[:2000],
            }

        output = proc.stdout.decode("utf-8", errors="replace")

        return {
            "result": "success",
            "output": output[:max_chars],
            "truncated": len(output) > max_chars,
        }

    except Exception as e:
        return {"result": "failed", "error": str(e)}

FUNCTIONS = {
    "json_query": json_query,
}

TOOLS = [
    {
      "type": "function",
      "function": {
        "name": "json_query",
        "description": "JSONファイルをjq式で検索、抽出、集計する。ファイル全体をLLMに読み込ませず、必要な結果だけ取得できる。",
        "parameters": {
          "type": "object",
          "properties": {
            "filename": {
              "type": "string",
              "description": "対象JSONファイル"
            },
            "query": {
              "type": "string",
              "description": "実行するjqフィルタ式"
            }
          },
          "required": ["filename", "query"],
          "additionalProperties": False
        }
      }
    },
]
