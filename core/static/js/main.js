function csrf(){const el=document.querySelector('[name=csrfmiddlewaretoken]');if(el&&el.value)return el.value;const m=document.cookie.match(/csrftoken=([^;]+)/);return m?m[1]:'';}
function post(url,data,isJson){
  const opts={method:'POST',headers:{'X-CSRFToken':csrf()}};
  if(isJson){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data||{});}
  else{const fd=new FormData();for(const k in (data||{}))fd.append(k,data[k]);opts.body=fd;}
  return fetch(url,opts).then(r=>r.json());
}
function notify(msg){if(!('Notification'in window))return;if(Notification.permission==='granted')new Notification('Planner',{body:msg});else if(Notification.permission!=='denied')Notification.requestPermission();}
if('Notification'in window&&Notification.permission==='default')Notification.requestPermission();

// Bottom nav is CSS-only; no sidebar toggle needed

// Jalali date via Intl
try{const el=document.getElementById('jalaliDate');if(el){const d=new Date();el.textContent=new Intl.DateTimeFormat('fa-IR',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(d);}}catch(e){}

// Daily tabs
document.querySelectorAll('#dailyTabs .tab').forEach(t=>{t.onclick=()=>{
  document.querySelectorAll('#dailyTabs .tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');
  const k=t.dataset.tab;
  ['Tip','Fact','Quote','Challenge'].forEach(n=>document.getElementById('daily'+n).classList.add('hidden'));
  document.getElementById('daily'+k.charAt(0).toUpperCase()+k.slice(1)).classList.remove('hidden');
};});

// Task actions
document.addEventListener('click',e=>{
  const tg=e.target.closest('[data-toggle]');if(tg){post('/api/tasks/'+tg.dataset.toggle+'/toggle/',{}).then(()=>location.reload());return;}
  const del=e.target.closest('[data-del]');if(del){post('/api/tasks/'+del.dataset.del+'/delete/',{}).then(()=>location.reload());return;}
  const mm=e.target.closest('[data-makemain]');if(mm){post('/api/tasks/'+mm.dataset.makemain+'/make-main/',{}).then(r=>{if(r.error)alert(r.error);location.reload();});return;}
  const ht=e.target.closest('[data-htoggle]');if(ht){post('/api/habits/'+ht.dataset.htoggle+'/toggle/',{}).then(()=>location.reload());return;}
  const hd=e.target.closest('[data-hdel]');if(hd){post('/api/habits/'+hd.dataset.hdel+'/delete/',{}).then(()=>location.reload());return;}
  const gt=e.target.closest('[data-gtoggle]');if(gt){post('/api/goals/'+gt.dataset.gtoggle+'/toggle/',{}).then(()=>location.reload());return;}
  const gd=e.target.closest('[data-gdel]');if(gd){post('/api/goals/'+gd.dataset.gdel+'/delete/',{}).then(()=>location.reload());return;}
  const ed=e.target.closest('[data-edel]');if(ed){post('/api/events/'+ed.dataset.edel+'/delete/',{}).then(()=>location.reload());return;}
  const wt=e.target.closest('[data-wtoggle]');if(wt){toggleWidget(wt);return;}
});
function bindForm(id,url){const f=document.getElementById(id);if(!f)return;f.onsubmit=ev=>{ev.preventDefault();const fd=new FormData(f);fetch(url,{method:'POST',headers:{'X-CSRFToken':csrf()},body:fd}).then(r=>r.json()).then(r=>{if(r.error)alert(r.error);else location.reload();});};}
bindForm('taskForm','/api/tasks/create/');bindForm('habitForm','/api/habits/create/');bindForm('goalForm','/api/goals/create/');bindForm('eventForm','/api/events/create/');

// Customize + drag & drop (robust)
const cust=document.getElementById('customizeBtn'),wset=document.getElementById('widgetSettings'),grid=document.getElementById('widgetGrid'),resetBtn=document.getElementById('resetLayoutBtn');
let customizeOn=false;
function setCustomize(on){customizeOn=on;
  if(wset)wset.classList.toggle('hidden',!on);
  if(resetBtn)resetBtn.classList.toggle('hidden',!on);
  if(cust)cust.textContent=on?'اتمام شخصی‌سازی':'شخصی‌سازی';
  if(grid)grid.querySelectorAll('.widget').forEach(w=>{w.draggable=on;w.classList.toggle('draggable',on);});
}
if(cust)cust.onclick=()=>setCustomize(!customizeOn);
if(resetBtn)resetBtn.onclick=()=>{var fd=new FormData();fetch('/api/widgets/reset/',{method:'POST',headers:{'X-CSRFToken':csrf()},body:fd}).then(function(r){return r.json();}).then(function(r){if(r.success){toast('داشبورد به حالت پیش‌فرض برگشت');setTimeout(function(){location.reload();},600);}else toast('خطا در بازنشانی');}).catch(function(){toast('خطا در ارتباط');});};
function toggleWidget(btn){
  var type=btn.dataset.wtoggle;
  btn.disabled=true;
  var fd=new FormData();fd.append('widget_type',type);
  fetch('/api/widgets/toggle/',{method:'POST',headers:{'X-CSRFToken':csrf()},body:fd}).then(function(r){return r.json();}).then(function(r){
    btn.disabled=false;
    if(typeof r.is_visible==='undefined'){toast('خطا در ذخیره');return;}
    btn.textContent=r.is_visible?'مخفی کن':'نمایش بده';
    btn.closest('.switch-row').querySelector('span').style.opacity=r.is_visible?'1':'.45';
    var w=grid?grid.querySelector('[data-widget="'+type+'"]'):null;
    if(w&&!r.is_visible){w.style.transition='opacity .2s';w.style.opacity='0';setTimeout(function(){w.remove();},200);}
    toast(r.is_visible?'ویجت نمایش داده شد':'ویجت مخفی شد');
    if(r.is_visible)setTimeout(function(){location.reload();},500);
  }).catch(function(){btn.disabled=false;toast('خطا در ارتباط');});
}
function toast(msg){if(window.AppForms&&window.AppForms.toast)window.AppForms.toast(msg);else alert(msg);}
function saveOrder(){if(!grid)return;const orders=[...grid.querySelectorAll('.widget')].map((w,i)=>({widget_type:w.dataset.widget,order:i}));fetch('/api/widgets/reorder/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify({orders})});}
if(grid){let dragEl=null;
  grid.addEventListener('dragstart',e=>{if(!customizeOn){e.preventDefault();return;}dragEl=e.target.closest('.widget');if(dragEl){dragEl.classList.add('dragging');e.dataTransfer.effectAllowed='move';}});
  grid.addEventListener('dragend',()=>{if(dragEl)dragEl.classList.remove('dragging');dragEl=null;grid.querySelectorAll('.widget').forEach(w=>w.classList.remove('drop-before','drop-after'));});
  grid.addEventListener('dragover',e=>{if(!customizeOn||!dragEl)return;e.preventDefault();const t=e.target.closest('.widget');if(!t||t===dragEl)return;
    const r=t.getBoundingClientRect();const after=(e.clientY-r.top)>r.height/2;
    grid.querySelectorAll('.widget').forEach(w=>w.classList.remove('drop-before','drop-after'));
    t.classList.add(after?'drop-after':'drop-before');
    if(after)grid.insertBefore(dragEl,t.nextSibling);else grid.insertBefore(dragEl,t);});
  grid.addEventListener('drop',e=>{e.preventDefault();grid.querySelectorAll('.widget').forEach(w=>w.classList.remove('drop-before','drop-after'));saveOrder();});
}

// Pomodoro (detect by element, not by flag set after load)
if(document.getElementById('pomoStart')){(function(){const pdEl=document.getElementById('pomoData');if(!pdEl)return;const pd=JSON.parse(pdEl.textContent);
let mode='focus',secs=pd.focus*60,timer=null,count=0;
const disp=document.getElementById('timerDisplay'),modeEl=document.getElementById('timerMode'),cnt=document.getElementById('pomoCount');
function fmt(s){return String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');}
function render(){disp.textContent=fmt(secs);cnt.textContent=count;modeEl.textContent=mode==='focus'?'تمرکز':mode==='short'?'استراحت کوتاه':'استراحت بلند';
const total=mode==='focus'?pd.focus*60:mode==='short'?pd.short*60:pd.long*60;
const ring=document.getElementById('ringFg');if(ring){const C=628;ring.style.strokeDashoffset=String(C*(1-secs/Math.max(1,total)));}
const tt=document.getElementById('timerTask');if(tt){const sel=document.getElementById('pomoTask');tt.textContent=sel&&sel.selectedOptions.length?sel.selectedOptions[0].textContent:'';}}
function saveSession(type,dur){const sel=document.getElementById('pomoTask');const tid=sel.value||null;fetch('/api/pomodoro/save/',{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify({task_id:tid,duration:dur,session_type:type})}).then(r=>r.json()).then(r=>{if(type==='focus')toast(r.task?('ثبت شد: '+r.task):'ثبت شد (بدون کار — دفعه بعد یک کار انتخاب کن)');});}
// --- Sound: Web Audio chime, no files needed ---
let audioCtx=null,soundOn=localStorage.getItem('pomoSound')!=='off';
function ensureAudio(){try{if(!audioCtx)audioCtx=new (window.AudioContext||window.webkitAudioContext)();if(audioCtx.state==='suspended')audioCtx.resume();}catch(e){}}
function beep(freq,at,dur){const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type='sine';o.frequency.value=freq;o.connect(g);g.connect(audioCtx.destination);const t=audioCtx.currentTime+at;g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(0.5,t+0.03);g.gain.exponentialRampToValueAtTime(0.0001,t+dur);o.start(t);o.stop(t+dur+0.05);}
function playChime(kind){if(!soundOn)return;ensureAudio();if(!audioCtx)return;
 if(kind==='focus'){[523,659,784].forEach((f,i)=>beep(f,i*0.18,0.5));}
 else{[784,659,523].forEach((f,i)=>beep(f,i*0.18,0.5));}}
function tick(){secs--;if(secs<=0){clearInterval(timer);timer=null;
 if(mode==='focus'){saveSession('focus',pd.focus);count++;notify('پومودورو تمام شد!');playChime('focus');mode=(count%pd.untilLong===0)?'long':'short';secs=(mode==='long'?pd.long:pd.short)*60;}
 else{playChime('break');notify('استراحت تمام شد!');mode='focus';secs=pd.focus*60;}document.getElementById('pomoStart').textContent='شروع';render();}else render();}
render();
document.getElementById('pomoStart').onclick=ev=>{ensureAudio();if(timer){clearInterval(timer);timer=null;ev.target.textContent='شروع';}else{timer=setInterval(tick,1000);ev.target.textContent='توقف';}};
const sndBtn=document.getElementById('pomoSound');if(sndBtn){sndBtn.textContent=soundOn?'🔔 صدا روشن':'🔕 صدا خاموش';sndBtn.onclick=()=>{soundOn=!soundOn;localStorage.setItem('pomoSound',soundOn?'on':'off');sndBtn.textContent=soundOn?'🔔 صدا روشن':'🔕 صدا خاموش';if(soundOn)playChime('focus');};}
document.getElementById('pomoReset').onclick=()=>{clearInterval(timer);timer=null;mode='focus';secs=pd.focus*60;document.getElementById('pomoStart').textContent='شروع';render();};
document.getElementById('pomoSkip').onclick=()=>{clearInterval(timer);timer=null;mode='focus';secs=pd.focus*60;document.getElementById('pomoStart').textContent='شروع';render();};
const ps=document.getElementById('pomoSettings');if(ps)ps.onsubmit=ev=>{ev.preventDefault();fetch('/api/pomodoro/settings/',{method:'POST',headers:{'X-CSRFToken':csrf()},body:new FormData(ps)}).then(r=>r.json()).then(()=>location.reload());};
})();}

// Statistics: pomodoro line chart (minutes per day) + per-task list is server-rendered
if(document.getElementById('statData')){(function(){
const sd=JSON.parse(document.getElementById('statData').textContent);
function fa(n){return String(n).replace(/\d/g,function(d){return '۰۱۲۳۴۵۶۷۸۹'[d];});}
const c=document.getElementById('chartFocusLine');if(!c)return;
const dpr=window.devicePixelRatio||1,W=c.clientWidth||c.parentElement.clientWidth||600,H=260;
c.width=W*dpr;c.height=H*dpr;c.style.height=H+'px';
const ctx=c.getContext('2d');ctx.scale(dpr,dpr);
const days=sd.days||[];
const padL=44,padR=14,padT=18,padB=34;
const max=Math.max(30,...days.map(function(d){return d.focus_minutes;}));
function X(i){return days.length===1?padL+(W-padL-padR)/2:padL+i*(W-padL-padR)/(days.length-1);}
function Y(v){return padT+(1-v/max)*(H-padT-padB);}
ctx.clearRect(0,0,W,H);
// gridlines + y labels
ctx.strokeStyle='#2c2e36';ctx.fillStyle='#9aa0ab';ctx.font='11px Vazirmatn, sans-serif';ctx.textAlign='left';ctx.lineWidth=1;
for(let g=0;g<=4;g++){const v=Math.round(max*g/4),y=Y(v);
  ctx.beginPath();ctx.moveTo(padL,y);ctx.lineTo(W-padR,y);ctx.stroke();
  ctx.fillText(fa(v),6,y+4);}
// area fill
if(days.length){
  const grad=ctx.createLinearGradient(0,padT,0,H-padB);
  grad.addColorStop(0,'rgba(255,107,26,.35)');grad.addColorStop(1,'rgba(255,107,26,0)');
  ctx.beginPath();ctx.moveTo(X(0),Y(days[0].focus_minutes));
  days.forEach(function(d,i){ctx.lineTo(X(i),Y(d.focus_minutes));});
  ctx.lineTo(X(days.length-1),H-padB);ctx.lineTo(X(0),H-padB);ctx.closePath();
  ctx.fillStyle=grad;ctx.fill();
}
// line
ctx.beginPath();days.forEach(function(d,i){if(i===0)ctx.moveTo(X(i),Y(d.focus_minutes));else ctx.lineTo(X(i),Y(d.focus_minutes));});
ctx.strokeStyle='#ff6b1a';ctx.lineWidth=2.5;ctx.lineJoin='round';ctx.stroke();
// points + values + day labels
ctx.textAlign='center';
days.forEach(function(d,i){
  ctx.beginPath();ctx.arc(X(i),Y(d.focus_minutes),4,0,7);ctx.fillStyle='#ff6b1a';ctx.fill();
  ctx.beginPath();ctx.arc(X(i),Y(d.focus_minutes),7,0,7);ctx.strokeStyle='rgba(255,107,26,.4)';ctx.lineWidth=2;ctx.stroke();
  ctx.fillStyle='#eceef1';ctx.fillText(fa(d.focus_minutes),X(i),Y(d.focus_minutes)-12);
  ctx.fillStyle='#9aa0ab';ctx.fillText((d.label||'').slice(0,10),X(i),H-12);
});
c.title=days.map(function(d){return (d.label||d.date)+': '+fa(d.focus_minutes)+' دقیقه';}).join(' | ');
})();}
