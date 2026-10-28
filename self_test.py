FUNCTIONS = {}
TOOLS = []

import json, subprocess
def _llmc_test():
    print("_llmc_test()")
    command = 'python3'
    parameters = (
        ('ollama with tools',('-c', 'import llmc;print(llmc.perform({"model":"gemma4:31b","content":"川崎の天気は？"}))')),
        ('openai with tools',('-c', 'import llmc;print(llmc.perform({"model":"x-ai/grok-4.20","content":"川崎の天気は？"}))')),
    )
    ret = []
    for test, args in parameters:
        try:
            r = subprocess.run(
                [command, *args],
                capture_output=True,
                text=True,
                timeout=30,
            )
            ret.append({
                "test" : test,
                "input": f"python3 {' '.join(args)}",
                "returncode": r.returncode,
                "stdout": r.stdout,
                "stderr": r.stderr,
            })

        except Exception as e:
            ret.append({ "test": test, "result": "failed", "error": str(e) })

    return json.dumps(ret, ensure_ascii=False)

FUNCTIONS.update({"llmc-test": _llmc_test})
