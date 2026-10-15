"""Apple official signing only; development helpers are not distribution files."""
from pathlib import Path
import json
import subprocess
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'dist/v2'
DEST.mkdir(parents=True, exist_ok=True)
NAMES = ['ColaManager','我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计',
         '可乐每周报告','可乐截止检查','可乐睡前提醒','ColaManager-Test']

def main():
    results = []
    for name in NAMES:
        target = DEST/('ColaManager-v2.0.0.shortcut' if name == 'ColaManager' else name+'.shortcut')
        for attempt in range(3):
            result = subprocess.run(['shortcuts','sign','--mode','anyone','--input',
                                 str(ROOT/'work/v2'/(name+'.shortcut')),'--output',str(target)],
                                capture_output=True, text=True, timeout=120)
            if result.returncode == 0 or 'NSURLErrorDomain' not in result.stderr:
                break
        entry = dict(name=name, exit_code=result.returncode, filename=target.name)
        if result.returncode:
            entry['error'] = result.stderr[-2000:]
        elif target.exists():
            entry['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            entry['source_sha256'] = hashlib.sha256((ROOT/'work/v2'/(name+'.shortcut')).read_bytes()).hexdigest()
            entry['signed_container'] = target.read_bytes().startswith(b'AEA1')
        results.append(entry)
        (ROOT/'work/v2/sign-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
        print(name, result.returncode, flush=True)
        if result.returncode: raise SystemExit(1)

if __name__ == '__main__': main()
