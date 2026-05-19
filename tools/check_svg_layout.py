from pathlib import Path
import re
import xml.etree.ElementTree as ET

NS = {'svg': 'http://www.w3.org/2000/svg'}
MAX_TEXT_LEN = 12
FORBIDDEN = ['device_manage','key_manage','asym_crypto','sym_crypto','hash_ops','file_ops','pqc_ops']

def fnum(v):
    return float(str(v).replace('px',''))

def check(path: Path):
    raw = path.read_text(encoding='utf-8')
    for bad in FORBIDDEN:
        assert bad not in raw, f'{path}: forbidden English handler {bad}'
    assert not re.search(r'<path[^>]+d="[^"]*[CQSTAqcsta][^"]*"', raw), f'{path}: curved path exists'
    root = ET.fromstring(raw)
    for text in root.findall('.//svg:text', NS):
        s = ''.join(text.itertext()).strip()
        if not s:
            continue
        compact = re.sub(r'\s+', '', s)
        assert len(compact) <= MAX_TEXT_LEN, f'{path}: text too long: {s}'
        fs = float(text.get('font-size', '20'))
        y = fnum(text.get('y'))
        # Text baseline must not sit on a horizontal rule. This catches the Chinese-height overlap problem.
        tx_x = fnum(text.get('x'))
        for ln in root.findall('.//svg:line', NS):
            x1, y1, x2, y2 = map(lambda k: fnum(ln.get(k)), ['x1','y1','x2','y2'])
            assert x1 == x2 or y1 == y2, f'{path}: diagonal line {x1},{y1}->{x2},{y2}'
            if y1 == y2 and min(x1, x2) <= tx_x <= max(x1, x2) and abs(y - y1) < fs * 0.9:
                raise AssertionError(f'{path}: text baseline too close to horizontal line: {s}')
    for poly in root.findall('.//svg:polyline', NS):
        pts = []
        for part in poly.get('points','').split():
            x, y = part.split(',')
            pts.append((float(x), float(y)))
        for (x1,y1),(x2,y2) in zip(pts, pts[1:]):
            assert x1 == x2 or y1 == y2, f'{path}: diagonal polyline {x1},{y1}->{x2},{y2}'

for svg in sorted(Path('images').glob('*.svg')):
    check(svg)
print('SVG layout checks passed')
