"""Independently reconcile the local camera snapshot, grid join and overlap scenarios."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from pyproj import Transformer


def verify(directory=None):
    root = Path(__file__).resolve().parents[1]
    directory = directory or root / 'results/output-camera-pilot/2026-07'
    html = (directory / 'index.html').read_text(encoding='utf-8')
    data = json.loads(html.split('const DATA=', 1)[1].split(';\nconst meta=', 1)[0])
    camera = data['cameras']
    raw = (root / 'data/cameras/bristol-cctv-source.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == camera['metadata']['source_sha256']
    rows = json.loads(raw)['features']
    source_positions = Counter((round(r['geometry']['x'], 2), round(r['geometry']['y'], 2)) for r in rows)
    assert len(rows) == camera['metadata']['source_record_count']
    assert len(source_positions) == len(camera['positions']) == camera['metadata']['distinct_positions']
    assert not camera['metadata']['excluded_record_ids']
    assert len({r['id'] for p in camera['positions'] for r in p['records']}) == len(rows)
    for p in camera['positions']:
        assert source_positions[(p['x'], p['y'])] == len(p['records'])
        assert p['grid'] == [math.floor(p['x'] / 2000), math.floor(p['y'] / 2000)]
    assert camera['metadata']['coverage_status'] == 'unknown'
    assert camera['metadata']['effectiveness_status'] == 'not assessable'
    inverse = Transformer.from_crs(27700, 4326, always_xy=True)
    occupied = {tuple(p['grid']) for p in camera['positions']}
    # Verify each supplied key against all four source-projection cell corners.
    matched = []
    for f, key in zip(data['geojson']['features'], data['camera_grid_keys'], strict=True):
        x, y = key
        expected = [(x*2000,y*2000),((x+1)*2000,y*2000),((x+1)*2000,(y+1)*2000),(x*2000,(y+1)*2000)]
        for corner, projected in zip(f['geometry']['coordinates'][0][:4], expected):
            lon, lat = inverse.transform(*projected)
            assert abs(lon-corner[0]) < .000001 and abs(lat-corner[1]) < .000001
        if tuple(key) in occupied:
            matched.append(f)
    asb = data['categories'].index('Anti-social behaviour')
    crimes = sum(sum(n for i, n in enumerate(f['properties']['counts']) if i != asb) for f in matched)
    pairs = {}
    points = camera['positions']
    for radius in [100, 250]:
        pairs[radius] = sum(math.hypot(p['x']-q['x'],p['y']-q['y']) < 2*radius
                            for i,p in enumerate(points) for q in points[:i])
    return {'status': 'passed', 'source_records': len(rows), 'distinct_positions': len(points),
            'occupied_crime_cells_with_positions': len(matched), 'crimes_in_entire_cells': crimes,
            'hypothetical_overlapping_position_pairs': pairs}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
