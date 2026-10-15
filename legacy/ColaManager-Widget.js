/* Shared read-only rule engine. Device local calendar arithmetic, instant deadlines. */
'use strict';
const Cola = (() => {
  const date = s => { if(typeof s!=='string' || !/(Z|[+-]\d\d:\d\d)$/.test(s) || !Number.isFinite(Date.parse(s))) throw Error('时间戳缺失或无时区'); return new Date(s); };
  const key = d => [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
  const add = (d,n) => {let x=new Date(d); x.setDate(x.getDate()+n); return x;};
  const monday = d => {let x=new Date(d);x.setHours(0,0,0,0);x.setDate(x.getDate()-(x.getDay()+6)%7);return x;};
  function validate(s) {
    if(!s || Number(s.schema_version)!==1 || !s.records || typeof s.records!=='object' || Array.isArray(s.records)) throw Error('数据结构无效');
    date(s.started_at); if(s.updated_at) date(s.updated_at);
    for(const [id,r] of Object.entries(s.records)) {
      if(!r || r.record_id!==id) throw Error('记录ID不匹配');
      const c=date(r.consumed_at),d=date(r.brushing_deadline);
      if(d<c || d-c>48*3600000) throw Error('刷牙截止时间无效');
      for(const field of ['rinsed_at','brushed_at']) if(r[field]) {if(date(r[field])<c)throw Error('打卡早于饮用');}
      if(typeof r.week_start!=='string' || !('status' in r) || !('violation_reason' in r)) throw Error('记录字段缺失');
    }
    return s;
  }
  function analyze(s,now=new Date()) {
    validate(s);const current=monday(now),wk=key(current),first=monday(date(s.started_at));
    if(first>now)throw Error('初始化时间晚于当前时间');
    const rows=Object.values(s.records).map(r=>{
      const c=date(r.consumed_at),d=date(r.brushing_deadline),b=r.brushed_at?date(r.brushed_at):null;
      if(c>now || (b&&b>now) || (r.rinsed_at&&date(r.rinsed_at)>now))throw Error('记录包含未来时间');
      const status=b?(b<=d?'compliant':'late'):(now>=d?'missed':'pending');
      return {...r,week_start:key(monday(c)),status,violation_reason:['late','missed'].includes(status)?'未按时完成刷牙打卡':'',penalty_week:key(add(monday(c),7))};
    });
    const byWeek=new Map(),bans=new Set();
    for(const r of rows){if(byWeek.has(r.week_start))throw Error('同周多条记录：请解决同步冲突');byWeek.set(r.week_start,r);if(r.violation_reason)bans.add(r.penalty_week);}
    let streak=0,longest=0,compliantWeeks=0;const weeks=[];
    for(let d=first;d<=current;d=add(d,7)){
      if(weeks.length>20000)throw Error('历史范围异常');
      const k=key(d),r=byWeek.get(k),status=r?r.status:'compliant',bad=!!(r&&r.violation_reason),closed=d<current;
      if(closed && status!=='pending'){if(bad)streak=0;else{streak++;compliantWeeks++;}longest=Math.max(longest,streak);}
      weeks.push({week_start:k,week_end:key(add(d,7)),count:r?1:0,rinsed:r?!!r.rinsed_at:null,brushed:r?status==='compliant':null,status,violation_reason:r?r.violation_reason:'',banned:bans.has(k),closed});
    }
    const thisRecord=byWeek.get(wk),count=thisRecord?1:0,banned=bans.has(wk),pendingPrevious=rows.some(r=>r.penalty_week===wk&&r.status==='pending');
    const rin=rows.filter(r=>r.rinsed_at).length,brush=rows.filter(r=>r.status==='compliant').length;
    return {week_start:wk,week_end:key(add(current,7)),allowed:banned?0:1,remaining:Math.max(0,(banned?0:1)-count),count,banned,pendingPrevious,
      rinsed:thisRecord?!!thisRecord.rinsed_at:null,brushed:thisRecord?thisRecord.status==='compliant':null,brushingStatus:thisRecord?thisRecord.status:'not_applicable',
      streak,longest,compliantWeeks,total:rows.length,rinseRate:rows.length?rin/rows.length:null,brushRate:rows.length?brush/rows.length:null,
      violations:rows.filter(r=>r.violation_reason).length,bannedWeeks:weeks.filter(w=>w.banned).length,nextAllowed:bans.has(key(add(current,7)))?0:1,
      records:rows,weeks,trend:weeks.slice(-12),updated_at:s.updated_at||s.started_at};
  }
  return {analyze,validate,monday,key,add,date};
})();
if(typeof module!=='undefined')module.exports=Cola;

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
