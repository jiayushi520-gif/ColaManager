"""Run the real imported Apple workflow against fixed fixtures. No production writes."""
import subprocess,pathlib,json,time,sys,os
root=pathlib.Path(__file__).resolve().parents[1]
workflow=os.environ.get('COLA_TEST_WORKFLOW','可乐规则验收')
report='native-v2-results.json' if workflow=='ColaManager-v2-Rules-Test-signed' else 'native-results.json'
results=[];folder=root/'work'/('native-run-'+str(int(time.time())));folder.mkdir()
for case in json.loads((root/'work/fixtures/expected.json').read_text()):
 name=case['name'];out=folder/(name+'.json');start=time.time()
 if len(sys.argv)>1 and name not in sys.argv[1:]:continue
 try:
  r=subprocess.run(['shortcuts','run',workflow,'--input-path',str(root/'work/fixtures'/f'{name}.json'),'--output-path',str(out)],capture_output=True,text=True,timeout=120)
  content=out.read_text() if out.is_file() else '\n'.join(p.read_text() for p in out.glob('*')) if out.is_dir() else r.stdout
  if r.returncode: raise RuntimeError(r.stderr or r.stdout or 'Native execution failed')
  actual=json.loads(content);passed=actual==case['expected'];error=r.stderr
 except Exception as e:actual={};passed=False;error=str(e)
 results.append({'case':name,'passed':passed,'error':error,'elapsed':round(time.time()-start,1),'expected':case['expected'],'actual':actual});print(name,'PASS' if passed else 'FAIL',error,flush=True)
 (root/'work'/report).write_text(json.dumps(results,ensure_ascii=False,indent=2))
 if not passed:print(json.dumps(results[-1],ensure_ascii=False),flush=True)
print('Passed',sum(x['passed'] for x in results),'/',len(results),flush=True)

if not all(x["passed"] for x in results):raise SystemExit(1)
