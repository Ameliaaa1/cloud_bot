const scene=document.getElementById('scene'),statusLine=document.getElementById('status'),outputs=document.getElementById('outputs');
const buttons=[...document.querySelectorAll('#controls button')];
const names={sunny:'晴天',cloudy:'阴天',rainy:'雨天'},icons={sunny:'🌤️',cloudy:'☁️',rainy:'🌧️'};
let busy=false,connected=false;
function render(s){
  if(s.version!==2||!names[s.weather]||!['auto','manual'].includes(s.control))throw Error('请更新 ESP32 固件');
  scene.dataset.weather=s.weather;scene.textContent=icons[s.weather];scene.setAttribute('aria-label',names[s.weather]);
  buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.control?s.control==='auto':s.control==='manual'&&b.dataset.weather===s.weather)));
  statusLine.textContent='设备已连接 · '+(s.control==='auto'?'自动':'手动')+' · '+names[s.weather]+(s.auto_online?' · 识别程序在线':' · 识别程序未连接');
  outputs.textContent='灯效：'+names[s.outputs.light]+'；喷雾模拟：'+(s.outputs.mist_simulated?'短脉冲':'关闭');
}
async function request(path='/state',data=null){
  if(busy)return;busy=true;buttons.forEach(b=>b.disabled=true);
  const abort=new AbortController(),timeout=setTimeout(()=>abort.abort(),2500);
  try{
    const r=await fetch(path,{method:data?'POST':'GET',body:data?new URLSearchParams(data):undefined,signal:abort.signal,cache:'no-store'});
    if(!r.ok)throw Error('设备返回 '+r.status);render(await r.json());connected=true;
  }catch(e){connected=false;statusLine.textContent='连接中断，正在自动重连。确认电脑连接 cloud_bot Wi-Fi。 '+(e.message||'');}
  finally{clearTimeout(timeout);busy=false;buttons.forEach(b=>b.disabled=false);}
}
buttons.forEach(b=>b.onclick=()=>b.dataset.control?request('/control',{mode:'auto'}):request('/weather',{mode:b.dataset.weather,source:'manual'}));
let preview=false,timer;const photo=document.getElementById('photo'),cameraButton=document.getElementById('camera'),cameraStatus=document.getElementById('cameraStatus');
function capture(){if(preview)photo.src='/capture?t='+Date.now();}
function schedule(){clearTimeout(timer);if(preview)timer=setTimeout(capture,1500);}
photo.onload=()=>{if(preview){cameraStatus.textContent='设备取景中';schedule();}};
photo.onerror=()=>{if(preview){cameraStatus.textContent='取景失败，正在重试';schedule();}};
cameraButton.onclick=()=>{preview=!preview;clearTimeout(timer);photo.hidden=!preview;cameraButton.textContent=preview?'停止预览':'开启预览';cameraButton.setAttribute('aria-pressed',String(preview));cameraStatus.textContent=preview?'正在取景…':'预览已停止';if(preview)capture();else photo.removeAttribute('src');};
request();setInterval(()=>request(),1000);
