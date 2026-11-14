const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
function element(dataset={}){return {dataset,attrs:{},textContent:'',hidden:true,disabled:false,setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this[k]}};}
const els=Object.fromEntries(['scene','status','outputs','photo','camera','cameraStatus'].map(k=>[k,element()]));
const buttons=[element({control:'auto'}),...['sunny','cloudy','rainy'].map(weather=>element({weather}))];
let response={version:2,weather:'cloudy',control:'auto',auto_online:true,outputs:{light:'cloudy',mist_simulated:false}},fails=false,calls=[];
const ctx={document:{getElementById:id=>els[id],querySelectorAll:()=>buttons},AbortController,URLSearchParams,Date,setTimeout,clearTimeout,setInterval:()=>{},fetch:async(path,opts)=>{calls.push([path,opts]);if(fails)throw Error('offline');return {ok:true,json:async()=>response}}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('firmware/cloud_bot_existing_parts/app.js','utf8'),ctx);
(async()=>{
 await new Promise(setImmediate);
 assert.match(els.status.textContent,/自动/);assert.equal(buttons[0].attrs['aria-pressed'],'true');
 response={...response,weather:'rainy',control:'manual',outputs:{light:'rainy',mist_simulated:true}};
 await buttons[3].onclick();assert.equal(calls.at(-1)[0],'/weather');assert.equal(calls.at(-1)[1].body.get('source'),'manual');assert.match(els.status.textContent,/手动/);assert.equal(buttons[3].attrs['aria-pressed'],'true');
 await buttons[0].onclick();assert.equal(calls.at(-1)[0],'/control');assert.equal(calls.at(-1)[1].body.get('mode'),'auto');
 fails=true;await vm.runInContext('request()',ctx);assert.match(els.status.textContent,/自动重连/);assert(buttons.every(b=>!b.disabled));
 fails=false;await vm.runInContext('request()',ctx);assert.match(els.status.textContent,/设备已连接/);
 response={weather:'cloudy'};await vm.runInContext('request()',ctx);assert.match(els.status.textContent,/更新/);
 console.log('6 web UI behavior checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
