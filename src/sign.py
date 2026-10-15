import pathlib,subprocess,json,sys
root=pathlib.Path(__file__).resolve().parents[1]
names=sys.argv[1:] or ['ColaManager','ColaManager-Test','我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计','可乐每周报告','可乐截止检查','可乐睡前提醒']
results=[]
for name in names:
 r=subprocess.run(['shortcuts','sign','--mode','anyone','--input',str(root/'work'/f'{name}.shortcut'),'--output',str(root/'dist'/f'{name}.shortcut')],capture_output=True,text=True)
 results.append({'name':name,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(name,r.returncode,flush=True)
(root/'work/sign-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
if any(r['exit_code'] for r in results):raise SystemExit(1)
