/* ---------------- 全域常數 ---------------- */
const QUICK_LABEL_NAME = DIR_MODE ? 'system_label_dir_meta_txt'
                                 : 'system_label_meta_txt';
let dirMode = DIR_MODE;
let debugMode = typeof DEBUG_MODE !== 'undefined' ? DEBUG_MODE : false;
let currentIdx = 0;
const cacheItems = {};      // idx -> item json

/* ---------------- 初始化 ------------------ */
window.addEventListener("DOMContentLoaded", () => {
  if (debugMode) {
    console.warn("DEBUG MODE active");
  }
  const last = parseInt(localStorage.getItem("lastIdx")) || 0;
  loadItem(Math.min(Math.max(last,0), TOTAL-1));
  document.addEventListener("keydown", onKey);
  document.getElementById("quick-label").focus();
  document.getElementById("page-form").addEventListener("submit", e => {
    e.preventDefault();
    const val = parseInt(document.getElementById("page-input").value);
    if(!isNaN(val)) loadItem(Math.min(Math.max(val-1,0), TOTAL-1));
  });
});
/* ---------------- 資料載入 ---------------- */
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

/* ---------------- 主渲染 ------------------ */
function render(d) {
  currentIdx = d.idx;
  document.getElementById("page-input").value = d.idx + 1;
  document.getElementById("page-total").textContent = TOTAL;
  localStorage.setItem("lastIdx", d.idx);
  document.getElementById('media-info').textContent = d.media_name;

  /* ── 左側媒體 ───────────────────────────*/
  const area = document.getElementById('media-area');
  area.innerHTML = '';

  if (d.media_kind === 'image') {
    const img = new Image(); img.src = d.media_url;
    area.appendChild(img);
  } else if (d.media_kind === 'video') {
    const v = document.createElement('video');
    v.src = d.media_url; v.controls = true; v.preload = 'auto';
    area.appendChild(v);
  } else if (d.media_kind === 'audio') {
    const a = document.createElement('audio');
    a.src = d.media_url; a.controls = true; a.preload = 'auto';
    area.appendChild(a);
  } else {  // text
    fetch(d.media_url).then(r => r.text()).then(txt => {
      const pre = document.createElement('pre'); pre.textContent = txt;
      area.appendChild(pre);
    });
  }

  /* ── 右側 annotations ───────────────────*/
  const annoDiv = document.getElementById('anno-area');
  annoDiv.innerHTML = '';

  let quickInit = dirMode ? (d.dir_label || '') : '';
  d.annotations.forEach(a => {
    const isQuick = a.filename.endsWith('.' + QUICK_LABEL_NAME);
    if (!dirMode && isQuick) {
      quickInit = a.content.trim();
      return;
    }
    const blk = document.createElement('div');
    blk.className = 'anno-block';

    const h4 = document.createElement('h4');
    h4.textContent = a.filename;
    blk.appendChild(h4);

    const ta = document.createElement('textarea');
    ta.value = a.content;
    ta.dataset.filename = a.filename;
    if (a.filename.endsWith('.system_label_meta_txt')) {
      ta.disabled = true;
    }
    blk.appendChild(ta);

    annoDiv.appendChild(blk);
  });

  const quickFile = dirMode ? `${d.dir_name}/${QUICK_LABEL_NAME}`
                            : `${d.id}.${QUICK_LABEL_NAME}`;
  document.getElementById('quick-name').textContent = quickFile;
  const quickBox = document.getElementById('quick-label');
  quickBox.value = quickInit;
  quickBox.focus();
}

/* ---------------- 鍵盤事件 ---------------- */
function onKey(e) {
  if (e.key === 'ArrowRight') { e.preventDefault(); saveThenMove(+1); }
  if (e.key === 'ArrowLeft')  { e.preventDefault(); saveThenMove(-1); }
  if (dirMode && e.key === 'ArrowDown') { e.preventDefault(); moveDir(+1); }
  if (dirMode && e.key === 'ArrowUp')   { e.preventDefault(); moveDir(-1); }
}

/* ---------------- 儲存並移動 -------------- */
async function saveThenMove(step) {
  await saveCurrent();
  const next = (currentIdx + step + TOTAL) % TOTAL;
  loadItem(next);

  // 預抓 5 張
  for (let i = 1; i <= 5; i++) {
    const idx = (next + i) % TOTAL;
    if (!cacheItems[idx]) {
      fetch(`/api/item/${idx}`).then(r => r.json()).then(d => cacheItems[idx] = d);
    }
  }
}

/* ---------------- 儲存當前 ---------------- */
async function saveCurrent() {
  const annos = [...document.querySelectorAll('#anno-area textarea:not([disabled])')]
                .map(t => ({ filename: t.dataset.filename, content: t.value }));
  const quick = document.getElementById('quick-label').value.trim();

  await fetch(`/api/item/${currentIdx}`, {
    method : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body   : JSON.stringify({ annotations: annos, quick_label: quick })
  });

  /* ▲ 失效目前快取，確保下次載入時拿到最新內容 */
  delete cacheItems[currentIdx];
}

function moveDir(step) {
  const d = cacheItems[currentIdx];
  const next = step > 0 ? d.dir_next_idx : d.dir_prev_idx;
  if (typeof next === 'number') {
    loadItem(next);
  }
}
