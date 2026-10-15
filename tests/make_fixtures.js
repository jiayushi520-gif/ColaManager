const fs=require('fs'),C=require('../src/cola_core');
fs.mkdirSync('work/fixtures',{recursive:true});
const state=()=>({schema_version:1,started_at:'2026-01-05T00:00:00+08:00',updated_at:'2026-01-05T00:00:00+08:00',records:{},deadline_time:'02:00',deadline_next_day:1,reminder_time:'23:00'});
const base=()=>({record_id:'a',consumed_at:'2026-01-11T22:00:00+08:00',rinsed_at:'',brushed_at:'',brushing_deadline:'2026-01-12T02:00:00+08:00',week_start:'2026-01-05',status:'pending',violation_reason:''});
const fixtures=[];
function fixture(name,now,patch=null,started){const s=state();if(patch!==null)s.records.a={...base(),...patch};if(started)s.started_at=started;const a=C.analyze(s,new Date(now));const expected={count:a.count,banned:+a.banned,violations:a.violations,rinse_total:a.records.filter(r=>r.rinsed_at).length,brush_total:a.records.filter(r=>r.status==='compliant').length,total:a.total,pending_previous:+a.pendingPrevious,this_violation:+!!a.records.find(r=>r.week_start===a.week_start&&r.violation_reason),allowance:a.allowed,remaining:a.remaining,streak:a.streak,longest:a.longest,compliant_weeks:a.compliantWeeks,banned_weeks:a.bannedWeeks,week_start:a.week_start};fixtures.push({name,expected});fs.writeFileSync('work/fixtures/'+name+'.json',JSON.stringify({state:s,now}));}
fixture('empty','2026-01-06T00:00:00+08:00');
fixture('consumed','2026-01-11T23:00:00+08:00',{});
fixture('rinsed','2026-01-11T23:00:00+08:00',{rinsed_at:'2026-01-11T22:01:00+08:00'});
fixture('pending','2026-01-12T01:59:59+08:00',{});
fixture('banned','2026-01-12T02:00:00+08:00',{});
fixture('restored','2026-01-19T00:00:00+08:00',{});
fixture('overnight','2026-01-12T03:00:00+08:00',{brushed_at:'2026-01-12T01:00:00+08:00'});
fixture('exactdeadline','2026-01-12T03:00:00+08:00',{brushed_at:'2026-01-12T02:00:00+08:00'});
fixture('late','2026-01-12T03:00:00+08:00',{brushed_at:'2026-01-12T02:00:01+08:00'});
fixture('streak','2026-02-02T00:00:00+08:00');
fixture('year','2027-01-01T00:00:00+08:00',null,'2026-12-28T00:00:00+08:00');
fs.writeFileSync('work/fixtures/expected.json',JSON.stringify(fixtures,null,2));
