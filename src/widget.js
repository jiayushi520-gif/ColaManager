// Read-only Scriptable widget. Requires an explicitly granted folder bookmark.
// Never synthesizes a state, and never falls back to an unlabelled cache.
const fm=FileManager.iCloud();
const w=new ListWidget();
w.backgroundColor=Color.dynamic(new Color('#FAF7F0'),new Color('#171C24'));
const foreground=Color.dynamic(new Color('#1E293B'),new Color('#F1F5F9'));
const muted=Color.dynamic(new Color('#526277'),new Color('#AAB9CC'));
w.setPadding(12,12,12,12);
const link=name=>'shortcuts://run-shortcut?name='+encodeURIComponent(name);
w.url=link('ColaManager');
const line=(parent,text,size=12,color=foreground)=>{const t=parent.addText(text);t.font=Font.systemFont(size);t.textColor=color;t.minimumScaleFactor=0.65;t.lineLimit=2;return t;};
try {
  if(!fm.bookmarkExists('ColaManager'))throw Error('请先授权 ColaManager 文件夹书签');
  const folder=fm.bookmarkedPath('ColaManager');
  const path=fm.joinPath(folder,'state.json');
  if(!fm.fileExists(path))throw Error('找不到 state.json；请先运行主快捷指令并等待 iCloud 同步');
  await fm.downloadFileFromiCloud(path);
  const raw=fm.readString(path); // Actual file contents, no sample data.
  const s=JSON.parse(raw); const a=Cola.analyze(s,new Date());
  const title=line(w,'🥤 可乐管理',14);title.font=Font.boldSystemFont(14);w.addSpacer(5);
  const body=w.addStack();body.layoutHorizontally();
  const left=body.addStack();left.layoutVertically();
  const quota=line(left,`剩余 ${a.remaining} 瓶`,25,a.banned?new Color('#DC5769'):foreground);quota.font=Font.boldSystemFont(25);left.url=link('我要喝可乐');
  line(left,`本周已饮用 ${a.count} 瓶`,11,muted);
  line(left,`禁喝：${a.banned?'是':'否'}${a.pendingPrevious?' · 待结算':''}`,11,a.banned?new Color('#DC5769'):muted);
  const status=(b)=>b===null?'不适用':b?'已打卡':'未打卡';
  const small=config.widgetFamily!=='medium';
  let right=left;
  if(!small){body.addSpacer(20);right=body.addStack();right.layoutVertically();}
  const rline=right.addStack();rline.url=link('我已经漱口');line(rline,`漱口：${status(a.rinsed)}`,small?10:13);
  const bline=right.addStack();bline.url=link('我已经刷牙');line(bline,`刷牙：${a.brushingStatus==='late'?'超时打卡':status(a.brushed)}`,small?10:13);
  const stats=right.addStack();stats.url=link('查看可乐统计');line(stats,`连续合规 ${a.streak} 周`,small?10:13);
  w.addSpacer();
  const modified=fm.modificationDate(path);
  line(w,`文件 ${modified?modified.toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}):'时间未知'}`,9,muted);
  if(!small)line(w,'基于当前已同步文件 · 系统调度刷新 · 连续周数仅含已结算周',9,muted);
  w.refreshAfterDate=new Date(Date.now()+30*60*1000);
} catch(e) {
  line(w,'🥤 可乐管理',16);w.addSpacer(8);
  line(w,'数据不可用',18,new Color('#DC5769'));
  line(w,String(e.message||e),11,muted);w.addSpacer();line(w,'点此打开主快捷指令；不会显示推测额度',9,muted);
  w.refreshAfterDate=new Date(Date.now()+30*60*1000);
}
if(config.runsInWidget)Script.setWidget(w);
else if(args.widgetParameter==='medium')await w.presentMedium();
else await w.presentSmall();
Script.complete();
