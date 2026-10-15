"""Actual native write/read tests in a separate iCloud development folder only."""
import pathlib,subprocess,json,datetime,sys,shutil
root=pathlib.Path(__file__).resolve().parents[1]
folder=pathlib.Path.home()/'Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/ColaManager-Development/Release'
results=[]
(root/'work/commands').mkdir(parents=True,exist_ok=True)
for command in ['我要喝可乐','我已经漱口','我已经刷牙','查看统计报告']:(root/'work/commands'/f'{command}.txt').write_text(command)
def state():return json.loads((folder/'state.json').read_text())
def run(mode):
 r=subprocess.run(['shortcuts','run','可乐最终写入验收','--input-path',str(root/'work/commands'/f'{mode}.txt')],capture_output=True,text=True,timeout=180)
 if r.returncode:raise RuntimeError(r.stderr)
 return r.stdout
if '--reset' in sys.argv:
 backup=root/'work'/('mutation-backup-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S'));backup.mkdir(parents=True)
 for name in ['state.json','state.backup.json','state.pending.json']:
  p=folder/name
  if p.exists():shutil.copy2(p,backup/name);p.unlink()
 run('我要喝可乐')
before=state();assert len(before['records'])==1
r=next(iter(before['records'].values()));assert r['rinsed_at']=='' and r['brushed_at']==''
results.append({'case':'first native consumption and JSON readback','passed':True,'record_id':r['record_id']})
for mode,field in [('我要喝可乐',None),('我已经漱口','rinsed_at'),('我已经漱口',None),('我已经刷牙','brushed_at'),('我已经刷牙',None)]:
 old=state();output=run(mode);new=state();assert len(new['records'])==1
 record=next(iter(new['records'].values()))
 if field:assert record[field] and record['record_id']==r['record_id']
 else:assert old==new
 results.append({'case':mode+(' update' if field else ' duplicate'),'passed':True,'output':output});print(mode,'PASS',output,flush=True)
 (root/'work/mutation-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
assert json.loads((folder/'state.backup.json').read_text())
assert state()==json.loads((folder/'state.pending.json').read_text())
print('Backup and pending readback PASS')

assert next(iter(state()['records'].values()))['status']=='compliant'
print('Persisted compliance status PASS')
