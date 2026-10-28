"""OpenAI-style Python function tool, executing untrusted code inside Docker."""
import json
import subprocess

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "python",
            "description": (
                "Execute Python code for numerical experiments and visualization. "
                "NumPy, SciPy, and Matplotlib are available. "
                "Print important numeric results; Matplotlib figures are returned as PNG base64. "
                "The environment has no network access and is reset for every call."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Complete, executable Python source code."
                    }
                },
                "required": ["code"],
                "additionalProperties": False,
            },
        },
    }
]

# Runs *inside* the container. The code arrives on stdin, not in a shell command.
_RUNNER = r'''
import sys, json, io, base64, traceback, contextlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

code = sys.stdin.read()
output = io.StringIO()
result = {"stdout": "", "images": [], "error": None}
try:
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        exec(compile(code, '<agent-python>', 'exec'), {"__name__": "__main__"})
except BaseException:
    result["error"] = traceback.format_exc()[-6000:]
result["stdout"] = output.getvalue()[-12000:]
for num in plt.get_fignums()[:3]:
    fig = plt.figure(num)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=90)
    if buf.tell() <= 750_000:
        result["images"].append(base64.b64encode(buf.getvalue()).decode('ascii'))
    else:
        result["error"] = (result["error"] or '') + '\nFigure omitted: PNG too large.'
print(json.dumps(result, ensure_ascii=False))
'''


def python(code):
    """Accept JSON arguments (str or dict) and return a JSON tool-response string."""
    args = {"code": code}
    print("python", args)
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError as exc:
            return json.dumps({"error": f"Invalid JSON arguments: {exc}"})
    if not isinstance(args, dict) or not isinstance(args.get('code'), str):
        return json.dumps({"error": "Argument 'code' must be a string."})
    code = args['code']
    if len(code) > 30000:
        return json.dumps({"error": "Code too long (max 30000 characters)."})

    command = [
        'docker', 'run', '--rm', '-i',
        '--network', 'none', '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--pids-limit', '64', '--memory', '2048m', '--cpus', '4',
        '--user', '65534:65534',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
        '-e', 'MPLCONFIGDIR=/tmp/mpl',
        '-e', 'OPENBLAS_NUM_THREADS=1',
        '-e', 'OMP_NUM_THREADS=1',
        'sandbox-python:latest',
        'python', '-I', '-c', _RUNNER,
    ]
    try:
        proc = subprocess.run(
            command, input=code, text=True, capture_output=True,
            timeout=25, check=False,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Execution timed out after 25 seconds."})
    except OSError as exc:
        return json.dumps({"error": f"Could not launch Docker: {exc}"})

    if proc.returncode != 0:
        return json.dumps({
            "error": f"Container exited with code {proc.returncode}",
            "stderr": proc.stderr[-4000:],
        }, ensure_ascii=False)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Invalid container response",
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
        }, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)

FUNCTIONS = {"python": python}


if __name__ == '__main__':
    code = 'import numpy as np\nimport matplotlib.pyplot as plt\nx=np.linspace(0,10,100)\nplt.plot(x,np.sin(x))\nprint(np.mean(np.sin(x)))'
    print(python(code))
