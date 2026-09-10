/* Shared modal + task/goal/event forms (lifeboard style) */
(function(){
function csrf(){var el=document.querySelector('[name=csrfmiddlewaretoken]');if(el&&el.value)return el.value;var m=document.cookie.match(/csrftoken=([^;]+)/);return m?m[1]:'';}
function toast(msg){var t=document.createElement('div');t.className='toast';t.textContent=msg;document.body.appendChild(t);setTimeout(function(){t.classList.add('show');});setTimeout(function(){t.classList.remove('show');setTimeout(function(){t.remove();},300);},2200);}

function openModal(title,bodyEl,buttons){
  closeModal();
  var ov=document.createElement('div');ov.className='modal-ov';ov.id='appModal';
  var card=document.createElement('div');card.className='modal-card2';
  var head=document.createElement('div');head.className='modal-head';
  var h=document.createElement('h3');h.textContent=title;
  var x=document.createElement('button');x.className='modal-x';x.textContent='✕';x.onclick=closeModal;
  head.appendChild(h);head.appendChild(x);
  var body=document.createElement('div');body.className='modal-body';body.appendChild(bodyEl);
  var foot=document.createElement('div');foot.className='modal-foot';
  (buttons||[]).forEach(function(b){if(b)foot.appendChild(b);});
  card.appendChild(head);card.appendChild(body);card.appendChild(foot);
  ov.appendChild(card);document.body.appendChild(ov);
  ov.addEventListener('mousedown',function(e){if(e.target===ov)closeModal();});
  document.addEventListener('keydown',escClose);
  return ov;
}
function escClose(e){if(e.key==='Escape')closeModal();}
function closeModal(){var m=document.getElementById('appModal');if(m)m.remove();document.removeEventListener('keydown',escClose);}
function row(label,el){var d=document.createElement('div');d.className='frow';if(label){var l=document.createElement('label');l.textContent=label;d.appendChild(l);}d.appendChild(el);return d;}
function primaryBtn(text,fn){var b=document.createElement('button');b.className='btn btn-primary';b.textContent=text;b.onclick=fn;return b;}
function dangerBtn(text,fn){var b=document.createElement('button');b.className='btn btn-danger';b.textContent=text;b.onclick=fn;return b;}
function seg(opts,current,cb){var d=document.createElement('div');d.className='seg';var val=current;
  opts.forEach(function(o){var a=document.createElement('a');a.textContent=o.label;if(o.id===val)a.classList.add('sel');
    a.onclick=function(){val=o.id;d.querySelectorAll('a').forEach(function(x){x.classList.remove('sel');});a.classList.add('sel');cb(val);};d.appendChild(a);});
  return {el:d,get:function(){return val;}};}
function postForm(url,fd){return fetch(url,{method:'POST',headers:{'X-CSRFToken':csrf()},body:fd}).then(function(r){return r.json();});}
function goals(){return (window.PAGE_DATA&&window.PAGE_DATA.goals)||[];}

function openTaskModal(existing,preset){
  preset=preset||{};existing=existing||null;
  var title=document.createElement('input');title.className='form-input';title.placeholder='مثلاً: تمرین یونیتی';title.value=existing?existing.title:'';
  var taskDate=existing?(existing.due_date||Jalali.isoToday()):(preset.date||Jalali.isoToday());
  var picker=Jalali.JDateField(taskDate);picker.set(taskDate);
  var time=document.createElement('input');time.type='time';time.className='form-input';time.value=(existing&&existing.due_time)||'';
  var prio=seg([{id:'1',label:'بالا'},{id:'2',label:'متوسط'},{id:'3',label:'کم'}],String(existing?existing.priority:'2'),function(){});
  var gsel=document.createElement('select');gsel.className='form-input';
  var def=document.createElement('option');def.value='';def.textContent='— بدون هدف —';gsel.appendChild(def);
  var gid=existing?(existing.goal_id||''): (preset.goalId||'');
  goals().forEach(function(g){var o=document.createElement('option');o.value=g.id;o.textContent='🎯 '+g.title;if(String(g.id)===String(gid))o.selected=true;gsel.appendChild(o);});
  var isMain=document.createElement('label');isMain.className='check-row';
  var cb=document.createElement('input');cb.type='checkbox';cb.checked=!!(existing&&existing.is_main_task);
  isMain.appendChild(cb);isMain.appendChild(document.createTextNode(' جزو ۳ کار اصلی امروز'));
  var body=document.createElement('div');
  body.appendChild(row('عنوان',title));
  body.appendChild(row('تاریخ انجام (شمسی)',picker.el));
  var grid=document.createElement('div');grid.className='form-grid';
  grid.appendChild(row('ساعت',time));grid.appendChild(row('هدف',gsel));
  body.appendChild(grid);
  body.appendChild(row('اولویت',prio.el));
  body.appendChild(isMain);
  var url=existing?('/api/tasks/'+existing.id+'/update/'):'/api/tasks/create/';
  openModal(existing?'ویرایش کار':'کار جدید',body,[
    primaryBtn('ذخیره',function(){
      if(!title.value.trim()){toast('عنوان کار را بنویس');return;}
      var fd=new FormData();
      fd.append('title',title.value.trim());fd.append('due_date',picker.get()||'');fd.append('due_time',time.value);
      fd.append('priority',prio.get());fd.append('goal',gsel.value);
      if(cb.checked)fd.append('is_main_task','on');
      postForm(url,fd).then(function(r){if(r.error){toast(r.error);return;}toast(existing?'کار ویرایش شد ✏️':'کار اضافه شد ✅');closeModal();location.reload();});
    }),
    existing?dangerBtn('حذف',function(){
      fetch('/api/tasks/'+existing.id+'/delete/',{method:'POST',headers:{'X-CSRFToken':csrf()}}).then(function(){closeModal();location.reload();});
    }):null
  ]);
  setTimeout(function(){title.focus();},50);
}

function openGoalModal(existing){
  existing=existing||null;
  var title=document.createElement('input');title.className='form-input';title.placeholder='مثلاً: ساخت بازی من';title.value=existing?existing.title:'';
  var desc=document.createElement('textarea');desc.className='form-input';desc.placeholder='توضیحات (اختیاری)';desc.rows=3;desc.value=(existing&&existing.description)||'';
  var dl=Jalali.JDateField((existing&&existing.deadline)||'');
  var body=document.createElement('div');
  body.appendChild(row('عنوان هدف',title));
  body.appendChild(row('موعد نهایی (شمسی)',dl.el));
  body.appendChild(row('',desc));
  var url=existing?('/api/goals/'+existing.id+'/update/'):'/api/goals/create/';
  openModal(existing?'ویرایش هدف':'هدف جدید',body,[
    primaryBtn('ذخیره',function(){
      if(!title.value.trim()){toast('عنوان هدف را بنویس');return;}
      var fd=new FormData();
      fd.append('title',title.value.trim());fd.append('description',desc.value);fd.append('deadline',dl.get()||'');
      postForm(url,fd).then(function(r){if(r.error){toast(r.error);return;}toast('هدف ذخیره شد 🎯');closeModal();location.reload();});
    }),
    existing?dangerBtn('حذف',function(){
      fetch('/api/goals/'+existing.id+'/delete/',{method:'POST',headers:{'X-CSRFToken':csrf()}}).then(function(){closeModal();location.reload();});
    }):null
  ]);
  setTimeout(function(){title.focus();},50);
}

function openEventModal(presetDate){
  var title=document.createElement('input');title.className='form-input';title.placeholder='مثلاً: جلسه پروژه';
  var picker=Jalali.JDateField(presetDate||Jalali.isoToday());
  var time=document.createElement('input');time.type='time';time.className='form-input';
  var rem=document.createElement('label');rem.className='check-row';
  var rcb=document.createElement('input');rcb.type='checkbox';rcb.checked=true;
  rem.appendChild(rcb);rem.appendChild(document.createTextNode(' یادآوری'));
  var body=document.createElement('div');
  body.appendChild(row('عنوان',title));
  body.appendChild(row('تاریخ (شمسی)',picker.el));
  body.appendChild(row('ساعت',time));
  body.appendChild(rem);
  openModal('رویداد جدید',body,[
    primaryBtn('ذخیره',function(){
      if(!title.value.trim()){toast('عنوان رویداد را بنویس');return;}
      var fd=new FormData();
      fd.append('title',title.value.trim());fd.append('date',picker.get()||'');fd.append('time',time.value);
      if(rcb.checked)fd.append('reminder','on');
      postForm('/api/events/create/',fd).then(function(r){if(r.error){toast(r.error);return;}toast('رویداد ذخیره شد 📅');closeModal();location.reload();});
    })
  ]);
  setTimeout(function(){title.focus();},50);
}

var HABIT_COLORS=['#ff8a3d','#ff5560','#5dd39e','#5b8def','#c792ea'];
function openHabitModal(existing){
  existing=existing||null;
  var name=document.createElement('input');name.className='form-input';name.placeholder='مثلاً: مطالعه روزانه';name.value=existing?existing.name:'';
  var icon=document.createElement('input');icon.className='form-input';icon.style.width='60px';icon.style.textAlign='center';icon.style.fontSize='18px';icon.value=(existing&&existing.icon)||'🔥';
  var color=(existing&&existing.color)||'#ff8a3d';
  var dots=document.createElement('div');dots.className='color-dots';
  dots.appendChild(icon);
  HABIT_COLORS.forEach(function(c){
    var d=document.createElement('div');d.className='color-dot'+(c===color?' sel':'');d.style.background=c;
    d.onclick=function(){color=c;dots.querySelectorAll('.color-dot').forEach(function(x){x.classList.remove('sel');});d.classList.add('sel');};
    dots.appendChild(d);
  });
  var target=document.createElement('input');target.type='number';target.min='1';target.max='7';target.className='form-input';target.value=(existing&&existing.target)||7;
  var body=document.createElement('div');
  body.appendChild(row('نام عادت',name));
  body.appendChild(row('آیکون و رنگ',dots));
  body.appendChild(row('هدف در هفته (روز)',target));
  var url=existing?('/api/habits/'+existing.id+'/update/'):'/api/habits/create/';
  openModal(existing?'ویرایش عادت':'عادت جدید',body,[
    primaryBtn('ذخیره',function(){
      if(!name.value.trim()){toast('نام عادت را بنویس');return;}
      var fd=new FormData();
      fd.append('name',name.value.trim());fd.append('icon',icon.value.trim()||'🔥');fd.append('color',color);fd.append('target',target.value||7);
      postForm(url,fd).then(function(r){if(r.error){toast(r.error);return;}toast('عادت ذخیره شد 🔥');closeModal();location.reload();});
    }),
    existing?dangerBtn('حذف',function(){
      fetch('/api/habits/'+existing.id+'/delete/',{method:'POST',headers:{'X-CSRFToken':csrf()}}).then(function(){closeModal();location.reload();});
    }):null
  ]);
  setTimeout(function(){name.focus();},50);
}

document.addEventListener('click',function(e){
  var t=e.target.closest('[data-new-task]');if(t){openTaskModal(null,{date:t.dataset.newTask||undefined,goalId:t.dataset.goal||undefined});return;}
  var et=e.target.closest('[data-edit-task]');if(et){var d=window.PAGE_DATA||{};var item=(d.tasks||[]).find(function(x){return String(x.id)===et.dataset.editTask;});if(item)openTaskModal(item);return;}
  var g=e.target.closest('[data-new-goal]');if(g){openGoalModal();return;}
  var eg=e.target.closest('[data-edit-goal]');if(eg){var d2=window.PAGE_DATA||{};var gl=(d2.goalsFull||[]).find(function(x){return String(x.id)===eg.dataset.editGoal;});if(gl)openGoalModal(gl);return;}
  var ev=e.target.closest('[data-new-event]');if(ev){openEventModal(ev.dataset.newEvent||undefined);return;}
  var nh=e.target.closest('[data-new-habit]');if(nh){openHabitModal();return;}
  var eh=e.target.closest('[data-edit-habit]');if(eh){var d3=window.PAGE_DATA||{};var hb=(d3.habitsFull||[]).find(function(x){return String(x.id)===eh.dataset.editHabit;});if(hb)openHabitModal(hb);return;}
});
window.AppForms={openTaskModal:openTaskModal,openGoalModal:openGoalModal,openEventModal:openEventModal,openHabitModal:openHabitModal,toast:toast,closeModal:closeModal};
})();
