FUNCTIONS = {}
TOOLS = []

def register(module_name: str):
    """指定されたサブモジュールを動的に読み込み、FUNCTIONS/TOOLSを登録する。
    モジュールが存在しなくてもエラーにならない（オプションimport対応）。
    """
    try:
        mod = __import__(f"llmc_tools.{module_name}", fromlist=["FUNCTIONS", "TOOLS"])
        FUNCTIONS.update(getattr(mod, "FUNCTIONS", {}))
        TOOLS.extend(getattr(mod, "TOOLS", []))
        print(f"llmc_tools: registered {module_name}")
    except ImportError as e:
        # llmc_toolsディレクトリがなくてもllmc.pyが動作するよう、静かにスキップ
        pass
    except Exception as e:
        print(f"llmc_tools: error in {module_name}: {e}")


# 登録するモジュール一覧（有効化したいものだけここに追加）
register("basic")
# register("life")           # weather ツール（生活関連） - basicと同等に常に有効
# register("web")          # web_search / web_fetch は現在無効（コメントアウト）
# register("knowledge")
register("self_test")           # llmc-test （REQUEST.mdで指定された単純テストツール）

def get_functions():
    """ツール関数辞書を返す（llmc.pyから使用）"""
    return FUNCTIONS

def get_tools():
    """OpenAIツール記述リストを返す（llmc.pyから使用）"""
    return TOOLS
