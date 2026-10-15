"""Produce a reviewable candidate archive, never upload or publish it."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent/'ColaManager-v2.0.0-candidate.zip'
NAMES = {'ColaManager-v2.0.0.shortcut','我要喝可乐.shortcut','我已经漱口.shortcut',
         '我已经刷牙.shortcut','查看可乐统计.shortcut','可乐每周报告.shortcut',
         '可乐截止检查.shortcut','可乐睡前提醒.shortcut','ColaManager-Test.shortcut'}

def main():
    signed = ROOT/'dist/v2'
    paths = {p.name:p for p in signed.glob('*.shortcut')}
    if set(paths) != NAMES:
        raise RuntimeError('unexpected or missing signed artifacts')
    results = json.loads((ROOT/'work/v2/sign-results.json').read_text())
    if len(results) != len(NAMES) or any(r['exit_code'] for r in results):
        raise RuntimeError('complete successful signing report required')
    for result in results:
        source = ROOT/'work/v2'/(result['name']+'.shortcut')
        if hashlib.sha256(source.read_bytes()).hexdigest() != result.get('source_sha256'):
            raise RuntimeError('unsigned source changed after signing')
        if hashlib.sha256(paths[result['filename']].read_bytes()).hexdigest() != result['sha256']:
            raise RuntimeError('signed output changed after signing')
    for path in paths.values():
        if not path.read_bytes().startswith(b'AEA1'):
            raise RuntimeError('missing Apple signed container: '+path.name)
    entries = {}
    for name in ['README.md','README_EN.md','CHANGELOG.md','.gitignore','LICENSE']:
        p = ROOT/name
        if p.exists(): entries[name] = p.read_bytes()
    for directory in ['src','tests','docs','.github','screenshots']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.swp'):
                entries[p.relative_to(ROOT).as_posix()] = p.read_bytes()
    for name, path in paths.items(): entries['dist/'+name] = path.read_bytes()
    entries['docs/sign-results.json'] = json.dumps(results,ensure_ascii=False,indent=2).encode()
    native_report = ROOT/'work/native-v2-results.json'
    if native_report.exists():
        entries['docs/native-v2-results.json'] = native_report.read_bytes()
    # Preserve legacy widget source without implying it is part of native installation.
    entries['legacy/ColaManager-Widget.js'] = (ROOT/'dist/ColaManager-Widget.js').read_bytes()
    entries['legacy/README.txt'] = '旧版可选 Scriptable 组件，需要第三方 App 和 iCloud，不用于v2原生安装。源码保留，未声称功能等价。\n'.encode()
    checksums = {name:hashlib.sha256(data).hexdigest() for name,data in sorted(entries.items())}
    entries['SHA256SUMS.json'] = json.dumps(checksums,ensure_ascii=False,indent=2).encode()
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(entries.items()): archive.writestr(name, data)
    with zipfile.ZipFile(OUT) as archive:
        if archive.testzip() is not None: raise RuntimeError('archive validation failed')
        assert not any(name.startswith(('work/','evidence/')) for name in archive.namelist())
    print(OUT.name, len(entries), 'files;', len(paths), 'Apple-signed shortcuts')

if __name__ == '__main__': main()
