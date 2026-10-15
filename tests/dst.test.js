const assert=require('node:assert/strict'), C=require('../src/cola_core');
for(const [day,next,expected] of [['2026-03-02T00:00:00-05:00','2026-03-09',167],['2026-10-26T00:00:00-04:00','2026-11-02',169]]){const d=new Date(day),n=C.add(d,7);assert.equal(C.key(n),next);assert.equal((n-d)/3600000,expected);console.log('PASS DST calendar week '+day+' '+expected+'h')}
const s={schema_version:1,started_at:'2026-03-02T00:00:00-05:00',records:{a:{record_id:'a',consumed_at:'2026-03-08T23:00:00-04:00',brushing_deadline:'2026-03-09T02:00:00-04:00',brushed_at:'2026-03-09T01:30:00-04:00',rinsed_at:'',status:'pending',week_start:'2026-03-02',violation_reason:''}}};
assert.equal(C.analyze(s,new Date('2026-03-09T03:00:00-04:00')).banned,false);console.log('PASS DST overnight brushing');
