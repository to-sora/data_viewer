#!/usr/bin/env python
"""
Dataset Annotator  (port 49145)
啟動：python app.py /absolute/path/to/dataset
"""
import sys, io, mimetypes
from pathlib import Path
from collections import defaultdict, OrderedDict
from flask import Flask, request, jsonify, render_template, send_file, abort

# ─── 常數 ──────────────────────────────────────────────────────────────
IMAGE_EXTS   = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
VIDEO_EXTS   = {'.mp4', '.mov', '.avi', '.mkv'}
AUDIO_EXTS   = {'.mp3', '.wav', '.ogg'}
TEXT_EXTS    = {'.txt', '.csv', '.json', '.yaml', '.yml'}

MEDIA_FILE_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | TEXT_EXTS
CACHE_SIZE       = 5
QUICK_LABEL_NAME = 'system_label_meta_txt'

# ─── Flask 與全域狀態 ───────────────────────────────────────────────────
app       = Flask(__name__, static_folder='static', static_url_path='/static')
DATA_ROOT = Path(sys.argv[1]).expanduser().resolve()
INDEX: list[dict] = []                      # [{id, media, annos}]
IMG_CACHE: OrderedDict[Path, bytes] = OrderedDict()

# ─── 建立索引 ──────────────────────────────────────────────────────────
def build_index(root: Path):
    """
    命名規則  
      filename = A . B  
      若  '_' not in B             →  主要媒體（原檔）  
      若  '_'  in B  (恰 1~n 個)    →  註解檔 (labeler_suffix)  
      例：image1.jpg,  image1.caption_txt,  image1._txt
    """
    groups: dict[str, list[Path]] = defaultdict(list)
    for fp in root.rglob('*'):
        if fp.is_file() and '.' in fp.name:
            rel  = fp.relative_to(root)
            base = str(rel).rsplit('.', 1)[0]
            groups[base].append(fp)

    for data_id, files in sorted(groups.items()):
        media_candidates = []
        annos            = []

        for f in files:
            ext_str = f.name.rsplit('.', 1)[1]     # B
            if '_' in ext_str:                     # annotation
                # 取 '_' 之後最後一段做副檔名判定
                label_ext = '.' + ext_str.rsplit('_', 1)[-1].lower()
                if label_ext in TEXT_EXTS:
                    annos.append(f)
            else:                                  # potential media
                if f.suffix.lower() in MEDIA_FILE_EXTS:
                    media_candidates.append(f)

        if not media_candidates:                   # 無真媒體 → 略過
            continue

        # 優先序：IMAGE < VIDEO < AUDIO < TEXT
        prio = {**{e:0 for e in IMAGE_EXTS},
                **{e:1 for e in VIDEO_EXTS},
                **{e:2 for e in AUDIO_EXTS},
                **{e:3 for e in TEXT_EXTS}}
        media = sorted(media_candidates, key=lambda f: prio[f.suffix.lower()])[0]

        INDEX.append({'id': data_id, 'media': media, 'annos': annos})

build_index(DATA_ROOT)
TOTAL = len(INDEX)

# ─── 快取 ──────────────────────────────────────────────────────────────
def preload(idx: int):
    for i in range(idx+1, min(idx+6, TOTAL)):
        fp = INDEX[i]['media']
        if fp.suffix.lower() in IMAGE_EXTS:
            if fp not in IMG_CACHE:
                if len(IMG_CACHE) >= CACHE_SIZE:
                    IMG_CACHE.popitem(last=False)
                IMG_CACHE[fp] = fp.read_bytes()

# ─── API ──────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html', total=TOTAL)

@app.route('/api/item/<int:idx>')
def api_item(idx: int):
    if idx < 0 or idx >= TOTAL:
        abort(404)
    ent = INDEX[idx]
    fp  = ent['media']
    kind = ('image' if fp.suffix.lower() in IMAGE_EXTS else
            'video' if fp.suffix.lower() in VIDEO_EXTS else
            'audio' if fp.suffix.lower() in AUDIO_EXTS else
            'text')

    annos = []
    for f in ent['annos']:
        try:
            txt = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            txt = ''
        annos.append({'filename': str(f.relative_to(DATA_ROOT)), 'content': txt})

    preload(idx)
    return jsonify({
        'idx'        : idx,
        'id'         : ent['id'],
        'media_url'  : f'/file/{fp.relative_to(DATA_ROOT)}',
        'media_kind' : kind,
        'media_name' : str(fp.relative_to(DATA_ROOT)),
        'annotations': annos
    })

@app.route('/api/item/<int:idx>', methods=['POST'])
def api_save(idx: int):
    if idx < 0 or idx >= TOTAL:
        abort(404)
    payload = request.get_json(force=True)
    ent     = INDEX[idx]

    # 1. annotation 協定儲存
    for row in payload.get('annotations', []):
        path = DATA_ROOT / row['filename']
        path.write_text(row['content'], encoding='utf-8')
        if path not in ent['annos']:
            ent['annos'].append(path)

    # 2. 快速標籤
    quick = (payload.get('quick_label') or '').strip()
    if quick:
        qpath = DATA_ROOT / f'{ent["id"]}.{QUICK_LABEL_NAME}'
        qpath.write_text(quick+'\n', encoding='utf-8')
        if qpath not in ent['annos']:
            ent['annos'].append(qpath)

    return jsonify({'status': 'ok'})

@app.route('/file/<path:fname>')
def serve_file(fname):
    fp = DATA_ROOT / fname
    if not fp.exists():
        abort(404)
    if fp in IMG_CACHE:
        return send_file(io.BytesIO(IMG_CACHE[fp]),
                         mimetype=mimetypes.guess_type(fp)[0] or 'application/octet-stream')
    return send_file(fp)

if __name__ == '__main__':
    print(f'📂 Dataset: {DATA_ROOT}')
    print(f'🔢 Total  : {TOTAL} items')
    app.run(host='0.0.0.0', port=49145, threaded=True)
