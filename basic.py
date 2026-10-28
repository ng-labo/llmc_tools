# llmc_tools.basic.py

import os, json
from datetime import datetime
import difflib
import subprocess

def _write(name: str, data: str):
    print("write", name, len(data))
    try:
        if os.path.dirname(name) and not os.path.exists(os.path.dirname(name)):
            os.mkdir(os.path.dirname(name))
        with open(name, 'w') as f:
            f.write(data)
            return f"wrote {len(data)} bytes"
    except Exception as e:
        print(f"failed to write. {e}")
        pass
    return f"failed to write"

def _read(name: str, offset: int=0, limit: int=0):
    print("read", name, offset, limit)
    if not os.path.exists(name):
        return ""
    try:
        with open(name, 'r') as f:
            if offset:
                f.seek(offset)
            return limit and f.read(limit) or f.read()
    except Exception as e:
        print(f"failed to read. {e}")
    return ""

def _read_line(name: str, offset: int = 0, limit: int = 200):
    print("read", name, offset, limit)

    if not os.path.isfile(name):
        return {
            "error": "file not found",
            "path": name,
        }

    try:
        lines = []

        with open(name, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                if lineno <= offset:
                    continue

                lines.append(f"{lineno:6d}| {line}")

                if limit and len(lines) >= limit:
                    break

        end_line = offset + len(lines)

        return {
            "path": name,
            "start_line": offset + 1 if lines else None,
            "end_line": end_line if lines else None,
            "next_offset": end_line if lines else None,
            "content": "".join(lines),
        }

    except Exception as e:
        return {
            "error": str(e),
            "path": name,
        }

def edit(name: str, old: str, new: str):
    print("edit", name)
    if not os.path.exists(name): return f"not found {name}"
    with open(name, "r") as f:
        data = f.read()

    count = data.count(old)

    if count == 0:
        return "old text not found"

    if count != 1:
        return f"ambiguous: {count} matches"

    org = [ o + '\n' for o in data.split('\n') ]

    data = data.replace(old, new, 1)

    dst = [ o + '\n' for o in data.split('\n') ]

    with open(name, "w") as f:
        f.write(data)

    diff = "".join(difflib.unified_diff(org, dst, fromfile="old", tofile="new"))

    return f"edited {name}\n===\n{diff}"

def ls():
    with os.scandir(".") as entries:
        a = []
        for entry in entries:
            if not entry.is_file(): continue
            s = entry.stat()
            r = {}
            r['size'] = s.st_size
            r['datetime'] = datetime.fromtimestamp(s.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            r['name'] = entry.name
            a.append(r)
        return json.dumps(a)
    return ""

LIST_AVAILABLE_CMD = ("ls", "gcc", "uname", "cat", "git", "ip", "as", "ld", "file", "strip", "curl", "sort", "uniq", "cut", "awk", "rg", "grep", "mkdir", )

def exec_cmd(command: str, args: list[str]):
    print("exec_cmd",command, args)
    if not command.startswith("./") and not command in LIST_AVAILABLE_CMD:
        return json.dumps({
            "error": "You cannot use it"
        }, ensure_ascii=False)
    try:
        r = subprocess.run(
            [command, *args],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return json.dumps({
            "returncode": r.returncode,
            "stdout": r.stdout,
            "stderr": r.stderr,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": str(e)
        }, ensure_ascii=False)


FUNCTIONS = {
    "write": _write,
    "read": _read_line,
    "edit": edit,
    "ls": ls,
    "exec_cmd": exec_cmd,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "ファイルを作成または上書きします。"
                           "ソースコードやテキストをファイルへ保存するときは必ずこの関数を使用してください。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "data": {"type": "string"},
                },
                "required": ["name", "data"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read a text file and return its contents with line numbers."
                           ""
                           "Use offset to specify the number of lines to skip from the beginning of the file."
                           "For example, offset=0 starts at line 1, and offset=100 starts at line 101."
                           ""
                           "Use limit to specify the maximum number of lines to return."
                           "If limit is 0, read all remaining lines."
                           ""
                           "Returned lines are prefixed with their original line numbers."
                           "Use these line numbers when referring to locations in the file or when requesting subsequent reads."
                           ""
                           "For large files, prefer reading small ranges incrementally rather than reading the entire file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "description": "Number of lines to skip before reading. offset=0 starts at line 1."
                    },
                    "limit": {
                        "type": "integer",
                        "default": 200,
                        "description": "Maximum number of lines to return. 0 means all remaining lines."
                    }
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": (
                "既存ファイルの一部分だけを置換して編集します。"
                "ファイル全体を書き直す必要がない変更では、writeではなくeditを優先してください。"
                "oldには置換対象となる既存の文字列を、前後の文脈を含めて正確に指定してください。"
                "oldがファイル内にちょうど1回だけ存在する場合に限り、その箇所をnewで置換します。"
                "oldが存在しない場合や複数箇所に一致する場合は編集に失敗します。"
                "複数箇所に一致する場合は、oldに周辺の行や文字列を追加して対象を一意にしてください。"
                "正規表現やsed形式の命令ではなく、実際にファイル内に存在する文字列をoldに指定してください。"
                "新しいファイルの作成やファイル全体の置換にはwriteを使用してください。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "編集する既存ファイル名"
                    },
                    "old": {
                        "type": "string",
                        "description": (
                            "現在ファイル内に存在する置換対象の文字列。"
                            "一意になるよう必要なら前後の文脈も含めて指定します。"
                        )
                    },
                    "new": {
                        "type": "string",
                        "description": (
                            "oldを置き換える新しい文字列。"
                            "空文字列を指定すると、その部分を削除します。"
                        )
                    },
                },
                "required": ["name", "old", "new"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ls",
            "description": "ファイルシステムからファイル一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exec_cmd",
            "description": "外部プログラム(LINUX)を実行します。"
                           f"現在利用可能なコマンド{LIST_AVAILABLE_CMD}です。"
                           "シェル機能は使用できません。"
                           "ファイルの作成・更新にはwriteを使用してください。"
                           "ファイル内容の読み取りにはreadを使用してください。"
                           "リダイレクト、パイプ、catによるファイル作成はできません。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "実行するコマンド名。例: gcc, as, ld"
                    },
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "コマンドライン引数"
                    }
                },
                "required": [
                    "command",
                    "args"
                ],
                "additionalProperties": False
            }
        }
    },
]
