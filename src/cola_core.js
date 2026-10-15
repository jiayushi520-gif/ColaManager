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
