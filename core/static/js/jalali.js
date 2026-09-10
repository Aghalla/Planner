/* Jalali utils + pretty Persian date picker (ported from lifeboard algorithm) */
(function(){
function div(a,b){return Math.floor(a/b);}
function mod(a,b){return a-Math.floor(a/b)*b;}
function toJalali(gy,gm,gd){
  var g_d_m=[0,31,59,90,120,151,181,212,243,273,304,334];
  var jy=gy<=1600?0:979; gy-=gy<=1600?621:1600;
  var gy2=gm>2?gy+1:gy;
  var days=365*gy+div(gy2+3,4)-div(gy2+99,100)+div(gy2+399,400)-80+gd+g_d_m[gm-1];
  jy+=33*div(days,12053); days%=12053;
  jy+=4*div(days,1461); days%=1461;
  if(days>365){jy+=div(days-1,365);days=mod(days-1,365);}
  var jm=days<186?1+div(days,31):7+div(days-186,30);
  var jd=1+(days<186?mod(days,31):mod(days-186,30));
  return {jy:jy,jm:jm,jd:jd};
}
function toGregorian(jy,jm,jd){
  jy+=1595;
  var days=-355668+365*jy+div(jy,33)*8+div(mod(jy,33)+3,4)+jd+(jm<7?(jm-1)*31:(jm-7)*30+186);
  var gy=400*div(days,146097); days%=146097;
  if(days>36524){days--;gy+=100*div(days,36524);days%=36524;if(days>=365)days++;}
  gy+=4*div(days,1461); days%=1461;
  if(days>365){gy+=div(days-1,365);days=mod(days-1,365);}
  var gd=days+1;
  var leap=((gy%4===0&&gy%100!==0)||gy%400===0);
  var sal_a=[0,31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
  var gm; for(gm=0;gm<13&&gd>sal_a[gm];gm++)gd-=sal_a[gm];
  return {gy:gy,gm:gm,gd:gd};
}
var J_MONTHS=['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند'];
var WEEK=['ش','ی','د','س','چ','پ','ج'];
function faNum(n){return String(n).replace(/\d/g,function(d){return '۰۱۲۳۴۵۶۷۸۹'[d];});}
function pad(n){return String(n).padStart(2,'0');}
function isoToday(){var d=new Date();return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
function jalaliParts(iso){var p=iso.split('-').map(Number);return toJalali(p[0],p[1],p[2]);}
function formatJalali(iso){try{var p=jalaliParts(iso);return faNum(p.jd)+' '+J_MONTHS[p.jm-1]+' '+faNum(p.jy);}catch(e){return iso;}}
function isLeap(jy){return [1,5,9,13,17,22,26,30].indexOf(jy%33)>=0;}
function monthLen(jy,jm){return jm<=6?31:(jm<=11?30:(isLeap(jy)?30:29));}
function addDays(iso,n){var p=iso.split('-').map(Number);var d=new Date(p[0],p[1]-1,p[2]+n);return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}
function weekdaySat0(iso){var p=iso.split('-').map(Number);return (new Date(p[0],p[1]-1,p[2]).getDay()+1)%7;}
function monthCells(jy,jm){
  var g=toGregorian(jy,jm,1);
  var first=g.gy+'-'+pad(g.gm)+'-'+pad(g.gd);
  var off=weekdaySat0(first),cells=[],i;
  for(i=off;i>=1;i--){var iso=addDays(first,-i);cells.push({iso:iso,jd:jalaliParts(iso).jd,other:true});}
  var len=monthLen(jy,jm),last=addDays(first,len-1);
  for(var d=1;d<=len;d++)cells.push({iso:addDays(first,d-1),jd:d,other:false});
  var k=1;while(cells.length%7!==0||cells.length<35){var niso=addDays(last,k);cells.push({iso:niso,jd:jalaliParts(niso).jd,other:true});k++;if(cells.length>42)break;}
  return cells;
}
function todayJ(){var d=new Date();return toJalali(d.getFullYear(),d.getMonth()+1,d.getDate());}

/* Pretty popup picker. Usage: JDateField(initialIso, onChange) -> {el, get(), set(v)} */
function JDateField(initialIso,onChange){
  var value=initialIso||'';
  var input=document.createElement('input');
  input.type='text';input.readOnly=true;input.className='form-input jdate-input';
  input.placeholder='انتخاب تاریخ…';input.style.cursor='pointer';
  var wrap=document.createElement('div');wrap.className='jdate-wrap';wrap.appendChild(input);
  function refresh(){input.value=value?formatJalali(value):'';}
  function close(){document.querySelectorAll('.jdate-popup').forEach(function(p){p.remove();});document.removeEventListener('mousedown',docClick);}
  function docClick(e){var p=document.querySelector('.jdate-popup');if(p&&!p.contains(e.target)&&e.target!==input)close();}
  function open(){
    close();
    var t=value?jalaliParts(value):todayJ();
    var cy=t.jy,cm=t.jm;
    var pop=document.createElement('div');pop.className='jdate-popup';
    function draw(){
      pop.innerHTML='';
      var head=document.createElement('div');head.className='jdate-head';
      var prev=document.createElement('button');prev.type='button';prev.textContent='‹';
      prev.onclick=function(){cm--;if(cm<1){cm=12;cy--;}draw();};
      var title=document.createElement('div');title.className='jdate-title';title.textContent=J_MONTHS[cm-1]+' '+faNum(cy);
      var next=document.createElement('button');next.type='button';next.textContent='›';
      next.onclick=function(){cm++;if(cm>12){cm=1;cy++;}draw();};
      head.appendChild(prev);head.appendChild(title);head.appendChild(next);
      var week=document.createElement('div');week.className='jdate-week';
      WEEK.forEach(function(w){var s=document.createElement('div');s.textContent=w;week.appendChild(s);});
      var grid=document.createElement('div');grid.className='jdate-grid';
      var tj=todayJ();
      monthCells(cy,cm).forEach(function(c){
        var isToday=!c.other&&tj.jy===cy&&tj.jm===cm&&c.jd===tj.jd;
        var isSel=value===c.iso;
        var b=document.createElement('button');b.type='button';
        b.className='jdate-day'+(isSel?' sel':'')+(isToday?' today':'')+(c.other?' other':'');
        b.textContent=faNum(c.jd);
        b.onclick=function(){value=c.iso;refresh();close();if(onChange)onChange(value);};
        grid.appendChild(b);
      });
      var foot=document.createElement('div');foot.className='jdate-foot';
      var tb=document.createElement('button');tb.type='button';tb.className='link';tb.textContent='امروز';
      tb.onclick=function(){var x=todayJ();cy=x.jy;cm=x.jm;draw();};
      foot.appendChild(tb);
      if(value){var cb=document.createElement('button');cb.type='button';cb.className='link danger';cb.textContent='پاک‌کردن';
        cb.onclick=function(){value='';refresh();close();if(onChange)onChange(value);};foot.appendChild(cb);}
      pop.appendChild(head);pop.appendChild(week);pop.appendChild(grid);pop.appendChild(foot);
    }
    draw();wrap.appendChild(pop);
    setTimeout(function(){document.addEventListener('mousedown',docClick);});
  }
  input.addEventListener('click',open);
  refresh();
  return {el:wrap,get:function(){return value;},set:function(v){value=v||'';refresh();}};
}
window.Jalali={isoToday:isoToday,formatJalali:formatJalali,faNum:faNum,JDateField:JDateField,todayJ:todayJ,monthCells:monthCells};
})();
