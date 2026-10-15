const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
async function render({family='small',bookmark=true,raw,missing=false,downloadFails=false,dark=false}={}){
 const texts=[],links=[]; let presented=false;
 class Stack{addText(t){texts.push(t);return {}}addSpacer(){}addStack(){return new Stack()}layoutHorizontally(){}layoutVertically(){}setPadding(){}set url(x){links.push(x)}async presentSmall(){presented=true}async presentMedium(){presented=true}}
 class Color{constructor(s){this.hex=s}static dynamic(a,b){return dark?b:a}}
 const ctx={console,Date,JSON,Number,Map,Set,Error,Object,String,Math,RegExp,encodeURIComponent,FileManager:{iCloud:()=>({bookmarkExists:()=>bookmark,bookmarkedPath:()=>'/authorized/bookmark',joinPath:(a,b)=>a+'/'+b,fileExists:()=>!missing,downloadFileFromiCloud:async()=>{if(downloadFails)throw Error('iCloud下载失败')},readString:()=>raw,modificationDate:()=>new Date()})},ListWidget:Stack,Color,Font:{systemFont:()=>({}),boldSystemFont:()=>({})},config:{runsInWidget:true,widgetFamily:family},args:{},Script:{setWidget:w=>{},complete:()=>{}}};
 await vm.runInNewContext('(async()=>{'+fs.readFileSync('dist/ColaManager-Widget.js','utf8')+'})()',ctx);return {texts,links};
}
(async()=>{
 for(const args of [{bookmark:false},{missing:true},{raw:'{broken'},{raw:'{}'},{downloadFails:true}]){const r=await render(args);assert(r.texts.includes('数据不可用'));assert(!r.texts.some(t=>/^剩余 \d/.test(t)));console.log('PASS unavailable widget '+JSON.stringify(args))}
 const raw=JSON.stringify({schema_version:1,started_at:'2026-01-05T00:00:00+08:00',records:{}});
 for(const family of ['small','medium'])for(const dark of [false,true]){const r=await render({family,dark,raw});for(const t of ['剩余 1 瓶','本周已饮用 0 瓶','漱口：不适用','刷牙：不适用'])assert(r.texts.includes(t));assert(r.links.some(l=>l.includes(encodeURIComponent('我已经刷牙'))));console.log('PASS widget layout mock '+family+' '+(dark?'dark':'light'))}
})().catch(e=>{console.error(e);process.exitCode=1});
