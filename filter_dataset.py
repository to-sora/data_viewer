import argparse
import shutil
from pathlib import Path
from collections import defaultdict

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv'}
AUDIO_EXTS = {'.mp3', '.wav', '.ogg'}
TEXT_EXTS  = {'.txt', '.csv', '.json', '.yaml', '.yml'}
MEDIA_FILE_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | TEXT_EXTS

QUICK_LABEL_NAME = 'system_label_meta_txt'
DIR_LABEL_NAME   = 'system_label_dir_meta_txt'

def build_index(root: Path):
    groups = defaultdict(list)
    for fp in root.rglob('*'):
        if fp.is_file() and '.' in fp.name:
            rel = fp.relative_to(root)
            base = str(rel).rsplit('.', 1)[0]
            groups[base].append(fp)

    for base, files in sorted(groups.items()):
        media_candidates = []
        annos = []
        for f in files:
            ext = f.name.rsplit('.', 1)[1]
            if '_' in ext:
                annos.append(f)
            else:
                if f.suffix.lower() in MEDIA_FILE_EXTS:
                    media_candidates.append(f)
        if not media_candidates:
            continue
        # priority IMAGE < VIDEO < AUDIO < TEXT
        prio = {**{e:0 for e in IMAGE_EXTS},
                **{e:1 for e in VIDEO_EXTS},
                **{e:2 for e in AUDIO_EXTS},
                **{e:3 for e in TEXT_EXTS}}
        media = sorted(media_candidates, key=lambda f: prio[f.suffix.lower()])[0]
        yield base, media, annos

def eval_filter(expr: str, text: str) -> bool:
    x = text
    try:
        return bool(eval(expr, {}, {'x': x}))
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description='Filter dataset using quick labels')
    parser.add_argument('input_dir', help='Dataset root directory')
    parser.add_argument('output_dir', help='Destination directory')
    parser.add_argument('--ext', default='all', help='Comma separated extensions, default all')
    parser.add_argument('--filter-mode', choices=['item', 'dir'], default='item', help='Filter by item or directory labels')
    parser.add_argument('--expr', required=True, help='Python expression using variable x as label text')
    parser.add_argument('--mode', choices=['copy', 'move'], default='copy', help='Copy or move files')
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.ext == 'all':
        exts = set()
    else:
        exts = {e if e.startswith('.') else '.' + e for e in args.ext.split(',')}

    copy_fn = shutil.copy2 if args.mode == 'copy' else shutil.move

    dir_label_cache = {}
    if args.filter_mode == 'dir':
        for d in input_dir.rglob('*'):
            if d.is_dir():
                label_file = d / DIR_LABEL_NAME
                if label_file.exists():
                    try:
                        txt = label_file.read_text(encoding='utf-8', errors='ignore')
                    except Exception:
                        txt = ''
                else:
                    txt = ''
                dir_label_cache[d] = txt

    for base, media, annos in build_index(input_dir):
        if exts and media.suffix.lower() not in exts:
            continue

        label_text = ''
        if args.filter_mode == 'item':
            lbl = next((f for f in annos if f.name.endswith(QUICK_LABEL_NAME)), None)
            if lbl and lbl.exists():
                try:
                    label_text = lbl.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    label_text = ''
        else:  # dir mode
            label_text = dir_label_cache.get(media.parent, '')

        if not eval_filter(args.expr, label_text):
            continue

        group_files = [media] + annos
        for f in group_files:
            dest = output_dir / f.relative_to(input_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            copy_fn(str(f), str(dest))

if __name__ == '__main__':
    main()
