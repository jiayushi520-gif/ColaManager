"""Package signed artifacts, source and auditable test evidence."""
from pathlib import Path
import json,hashlib,shutil,zipfile
root=Path(__file__).resolve().parents[1];dist=root/'dist';out=root/'outputs';out.mkdir(exist_ok=True)
expected={'ColaManager','ColaManager-Test','我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计','可乐每周报告','可乐截止检查','可乐睡前提醒'}
assert {p.stem for p in dist.glob('*.shortcut')}==expected
for p in dist.glob('*.shortcut'):assert p.read_bytes().startswith(b'AEA1'),p
manifest={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(dist.iterdir()) if p.is_file() and p.name!='SHA256SUMS.json'}
(dist/'SHA256SUMS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
shutil.copytree(dist,out/'dist',dirs_exist_ok=True)
evidence=out/'evidence';evidence.mkdir(exist_ok=True)
for name in ['native-results.json','mutation-results.json','entry-results.json','final-query.json','file-performance.json','release-sign-results.json','final-code-tests.txt','final-dst-tests.txt','final-structure-tests.txt']:
 p=root/'work'/name
 if p.exists():shutil.copy2(p,evidence/name)
archive=out/'ColaManager-完整交付.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for folder in ['dist','src','tests']:
  for p in (root/folder).rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(root)))
 for p in evidence.iterdir():z.write(p,'evidence/'+p.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive);print('Signed shortcuts:',len(expected));print('Archive bytes:',archive.stat().st_size)
