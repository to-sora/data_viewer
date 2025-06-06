/* ---------- 全域變數 ---------- */
const QUICK_LABEL_NAME = 'system_label_meta_txt';
let currentIdx = 0;
const cacheItems = {};          // 前端快取 JSON

/* ---------- 初始化 ---------- */
window.addEventListener('DOMContentLoaded', () => {
  loadItem(0);
  document.addEventListener('keydown', onKey);
  document.getElementById('quick-label').focus();
});

/* ---------- 資料載入 ---------- */
async function loadItem(idx) {
  if (cacheItems[idx]) {
    render(cacheItems[idx]);
  } else {
    const res  = await fetch(`/api/item/${idx}`);
    const data = await res.json();
    cacheItems[idx] = data;
    render(data);
  }
}

/* ---------- 渲染 ---------- */
function render(d) {
  currentIdx = d.idx;
  // 檔名
  document.getElementById('media-info').textContent = d.media_name;

  // 左邊媒體
  const area = document.getElementById('media-area');
  area.innerHTML = '';
  if (d.media_kind === 'image') {
    const img = new Image();
    img.src = d.media_url; area.appendChild(img);
  } else if (d.media_kind === 'video') {
    const v = document.createElement('video');
    v.src = d.media_url; v.controls = true; v.preload = 'auto';
    area.appendChild(v);
  } else if (d.media_kind === 'audio') {
    const a = document.createElement('audio');
    a.src = d.media_url; a.controls = true; a.preload = 'auto';
    area.appendChild(a);
  } else { // text
    fetch(d.media_url).then(r=>r.text()).then(txt=>{
      const pre=document.createElement('pre');pre.textContent=txt;area.appendChild(pre);
    });
  }

  // 右邊 annotations
  const annoDiv = document.getElementById('anno-area');
  annoDiv.innerHTML = '';
  let quickInit = '';

  d.annotations.forEach(a=>{
    if (a.filename.endsWith('.'+QUICK_LABEL_NAME)) {
      quickInit = a.content.trim();
      return;
    }
    const block = document.createElement('div');
    block.className = 'anno-block';

    const h4 = document.createElement('h4');
    h4.textContent = a.filename;
    block.appendChild(h4);

    const ta = document.createElement('textarea');
    ta.value = a.content;
    ta.dataset.filename = a.filename;
    block.appendChild(ta);

    annoDiv.appendChild(block);
  });

  const quick = document.getElementById('quick-label');
  quick.value = quickInit;
  quick.focus();
}

/* ---------- 鍵盤控制 ---------- */
function onKey(e){
  if (e.key==='ArrowRight'){e.preventDefault();saveThenMove(+1);}
  if (e.key==='ArrowLeft'){e.preventDefault();saveThenMove(-1);}
}

async function saveThenMove(step){
  await saveCurrent();
  const next=(currentIdx+step+TOTAL)%TOTAL;
  await loadItem(next);
  // 背景預抓
  for(let i=1;i<=5;i++){
    const idx=(next+i)%TOTAL;
    if(!cacheItems[idx]){
      fetch(`/api/item/${idx}`).then(r=>r.json()).then(d=>cacheItems[idx]=d);
    }
  }
}

/* ---------- 儲存 ---------- */
async function saveCurrent(){
  const annos=[...document.querySelectorAll('#anno-area textarea')]
               .map(t=>({filename:t.dataset.filename,content:t.value}));
  const quick=document.getElementById('quick-label').value.trim();

  await fetch(`/api/item/${currentIdx}`,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({annotations:annos,quick_label:quick})
  });
}
