from pathlib import Path
import re
import xml.etree.ElementTree as ET

NS = {'svg': 'http://www.w3.org/2000/svg'}
BAD_WORDS = ['device_manage','key_manage','asym_crypto','sym_crypto','hash_ops','file_ops','pqc_ops']
MAX_TEXT_LEN = 18

def visible_text(root):
    for node in root.findall('.//svg:text', NS):
        txt = ''.join(node.itertext()).strip()
        if txt:
            yield txt

def num(v):
    return float(str(v).replace('px',''))

def check_file(path: Path):
    raw = path.read_text(encoding='utf-8')
    for bad in BAD_WORDS:
        assert bad not in raw, f'{path}: contains English handler {bad}'
    assert not re.search(r'<path[^>]+d="[^"]*[CQSTAqcsta][^"]*"', raw), f'{path}: contains curved path'
    root = ET.fromstring(raw)
    for txt in visible_text(root):
        compact = re.sub(r'\s+', '', txt)
        assert len(compact) <= MAX_TEXT_LEN, f'{path}: text too long: {txt}'
    for line in root.findall('.//svg:line', NS):
        x1, y1 = num(line.get('x1')), num(line.get('y1'))
        x2, y2 = num(line.get('x2')), num(line.get('y2'))
        assert x1 == x2 or y1 == y2, f'{path}: diagonal line {x1},{y1}->{x2},{y2}'
    for poly in root.findall('.//svg:polyline', NS):
        pts = []
        for part in poly.get('points','').split():
            x, y = part.split(',')
            pts.append((num(x), num(y)))
        for (x1,y1),(x2,y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, f'{path}: diagonal polyline {x1},{y1}->{x2},{y2}'

for f in sorted(Path('images').glob('*.svg')):
    check_file(f)
print('SVG layout checks passed')
