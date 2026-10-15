"""Build Apple's native binary-plist workflow format; sign with Apple's CLI.
No runtime Python, shell, JavaScript or third-party actions in native workflows.
"""
import plistlib, uuid, pathlib, json, contextlib, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
WORK=ROOT/'work'; DIST=ROOT/'dist'
def uid(): return str(uuid.uuid4()).upper()
def var(n): return {'Value':{'Type':'Variable','VariableName':n},'WFSerializationType':'WFTextTokenAttachment'}
def token(*parts):
    s=''; att={}
    for p in parts:
        if isinstance(p,dict):
            att['{%d, 1}'%(len(s.encode('utf-16-le'))//2)]=p['Value']; s+='\ufffc'
        else: s+=str(p)
    return {'Value':{'string':s,'attachmentsByRange':att},'WFSerializationType':'WFTextTokenString'}
class Flow:
    def __init__(self): self.actions=[]
    def a(self,kind,**p):
        if kind=='text.replace' and isinstance(p.get('WFInput'),dict) and p['WFInput'].get('WFSerializationType')=='WFTextTokenAttachment': p['WFInput']=token(p['WFInput'])
        u=uid(); p['UUID']=u
        self.actions.append({'WFWorkflowActionIdentifier':'is.workflow.actions.'+kind,'WFWorkflowActionParameters':p})
        return {'Value':{'Type':'ActionOutput','OutputUUID':u,'OutputName':'Result'},'WFSerializationType':'WFTextTokenAttachment'}
    def set(self,n,v): self.a('setvariable',WFVariableName=n,WFInput=v); return var(n)
    def text(self,n,*p): return self.set(n,self.a('gettext',WFTextActionText=token(*p)))
    def num(self,n,x): return self.set(n,self.a('number',WFNumberActionNumber=x))
    def math(self,n,a,op,b): return self.set(n,self.a('math',WFInput=a,WFMathOperation=op,WFMathOperand=token(b) if isinstance(b,dict) else b))
    def get(self,n,d,k): return self.set(n,self.a('getvalueforkey',WFInput=d,WFDictionaryKey=k))
    def put(self,d,k,v): return self.set(d,self.a('setvalueforkey',WFDictionary=var(d),WFDictionaryKey=k,WFDictionaryValue=token(v) if isinstance(v,dict) else v))
    def fmt(self,n,d,fmt): return self.set(n,self.a('format.date',WFDate=token(d),WFDateFormatStyle='Custom',WFDateFormat=fmt,WFDateFormatString=fmt,WFDateFormatLocale='en_GB',WFTimeFormatStyle='None'))
    def date(self,n,s): return self.set(n,self.a('date',WFDateActionMode='Specified Date',WFDateActionDate=s))
    def adjust(self,n,d,amount=0,unit='days',op='Add'):
        return self.set(n,self.a('adjustdate',WFDate=token(d),WFAdjustOperation=op,WFDuration={'Value':{'Magnitude':token(amount) if isinstance(amount,dict) else amount,'Unit':unit},'WFSerializationType':'WFQuantityFieldValue'}))
    def diff(self,n,start,end): return self.set(n,self.a('gettimebetweendates',WFInput=token(end),WFTimeUntilFromDate=token(start),WFTimeUntilUnit='Seconds'))
    def week(self,n,d):
        # Unicode g is the local Julian day, independent of first weekday.
        self.fmt(n+'mjd',d,'g'); self.math(n+'sum',var(n+'mjd'),'+',0)
        self.math(n+'q',var(n+'sum'),'÷',7)
        self.set(n+'floor',self.a('round',WFInput=var(n+'q'),WFRoundTo='Integer',WFRoundMode='Always Round Down'))
        self.math(n+'base',var(n+'floor'),'×',7); self.math(n+'offset',var(n+'sum'),'-',var(n+'base'))
        for offset in range(7):
            branch=self.iff(var(n+'offset'),4,offset)
            self.adjust(n+'date',d,offset,op='Subtract'); self.end(branch)
        self.fmt(n,var(n+'date'),'yyyy-MM-dd')
        return var(n)
    def iff(self,v,op,x=None):
        v=copy.deepcopy(v)
        if x is not None:
            v['Value']['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFNumberContentItem' if isinstance(x,(int,float)) else 'WFStringContentItem'}]
        g=uid(); p={'WFInput':{'Type':'Variable','Variable':v},'WFCondition':op,'WFControlFlowMode':0,'GroupingIdentifier':g}
        if x is not None:
            p['WFNumberValue' if isinstance(x,(int,float)) else 'WFConditionalActionString']=x
        self.a('conditional',**p); return g
    def otherwise(self,g): self.a('conditional',GroupingIdentifier=g,WFControlFlowMode=1)
    def end(self,g,kind='conditional'): self.a(kind,GroupingIdentifier=g,WFControlFlowMode=2)
    def repeat(self,v):
        g=uid(); self.a('repeat.each',WFInput=v,GroupingIdentifier=g,WFControlFlowMode=0); return g
    def show(self,*p): self.a('showresult',Text=token(*p))
    def stop(self,*p):
        if p:
            self.show(*p)
            self.a('output',WFOutput=token(*p))
        else:self.a('exit')
    def save(self,v,path,ask=False):
        basename=path.rsplit('/',1)[-1] if isinstance(path,str) else 'report.txt'
        named=self.a('setitemname',WFInput=v,WFName=basename)
        return self.a('documentpicker.save',WFInput=named,WFFileDestination='iCloud Drive',WFAskWhereToSave=ask,WFFileDestinationPath=path,WFSaveFileOverwrite=True)
    def load(self,n,path): return self.set(n,self.a('documentpicker.open',WFFileStorageService='iCloud Drive',WFShowFilePicker=False,WFGetFilePath=path,WFFileErrorIfNotFound=False))
    def output(self,name):
        wf={'WFWorkflowName':name,'WFWorkflowClientVersion':'3036.0.4','WFWorkflowMinimumClientVersion':900,'WFWorkflowIcon':{'WFWorkflowIconStartColor':4282601983,'WFWorkflowIconGlyphNumber':59511},'WFWorkflowTypes':['NCWidget'],'WFWorkflowInputContentItemClasses':['WFStringContentItem'],'WFWorkflowActions':self.actions,'WFWorkflowImportQuestions':[]}
        (WORK/(name+'.shortcut')).write_bytes(plistlib.dumps(wf,fmt=plistlib.FMT_BINARY))
        (WORK/(name+'.json')).write_text(json.dumps(wf,ensure_ascii=False,indent=2))
        print(name,len(self.actions))

def probe():
    f=Flow(); f.set('now',f.a('date',WFDateActionMode='Current Date')); f.week('week',var('now'))
    f.date('past','2026-01-01T00:00:00+08:00'); f.date('later','2026-01-02T00:00:00+08:00'); f.diff('delta',var('past'),var('later'))
    f.text('raw','{"schema_version":1,"records":{}}'); f.set('state',f.a('detect.dictionary',WFInput=var('raw'))); f.put('state','week',var('week'))
    f.show('周一=',var('week'),'；秒差=',var('delta'),'；JSON=',var('state'))
    f.output('可乐开发探针3')
if __name__=='__main__': probe()
