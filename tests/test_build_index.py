import importlib.util
import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / 'app.py'


def load_app(tmp_path: Path):
    """Import ``app.py`` with a custom argv and return the module."""
    sys.argv = ['app.py', str(tmp_path)]
    if 'app' in sys.modules:
        del sys.modules['app']
    spec = importlib.util.spec_from_file_location('app', APP_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['app'] = module
    assert spec.loader  # for mypy, loader is not None
    spec.loader.exec_module(module)
    return module


def test_index_and_ordering(tmp_path):
    # create files
    (tmp_path/'image1.jpg').write_text('img')
    (tmp_path/'image1.caption2_txt').write_text('c2')
    (tmp_path/'image1.caption1_txt').write_text('c1')
    (tmp_path/'image1.meta_json').write_text('{}')
    (tmp_path/'image1.WD14_txt').write_text('w')
    app = load_app(tmp_path)
    assert len(app.INDEX) == 1
    item = app.INDEX[0]
    assert item['id'] == 'image1'
    assert item['media'].name == 'image1.jpg'
    anno_names = [f.name for f in item['annos']]
    assert anno_names == ['image1.meta_json', 'image1.WD14_txt',
                          'image1.caption1_txt', 'image1.caption2_txt']


def test_media_priority(tmp_path):
    (tmp_path/'data2.mp4').write_text('vid')
    (tmp_path/'data2.png').write_text('img')
    app = load_app(tmp_path)
    assert len(app.INDEX) == 1
    assert app.INDEX[0]['media'].name == 'data2.png'


def test_directory_field(tmp_path):
    sub = tmp_path / 'dir1'
    sub.mkdir()
    (sub/'img.jpg').write_text('img')
    app = load_app(tmp_path)
    assert len(app.INDEX) == 1
    assert app.INDEX[0]['dir'] == 'dir1'

