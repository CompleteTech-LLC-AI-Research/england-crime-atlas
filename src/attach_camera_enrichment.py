"""Refresh the viewer from its embedded aggregates without rereading raw crime data."""
import argparse
import json
from pathlib import Path
from pyproj import Transformer


def index_grid(payload):
    forward = Transformer.from_crs(4326, 27700, always_xy=True)
    size = payload['metadata']['cell_m']
    payload['camera_grid_keys'] = []
    for feature in payload['geojson']['features']:
        corner = feature['geometry']['coordinates'][0][0]
        x, y = forward.transform(*corner)
        payload['camera_grid_keys'].append([round(x / size), round(y / size)])
        feature['properties'].pop('camera_grid', None)


def attach(map_path, cameras):
    html = map_path.read_text(encoding='utf-8')
    payload = json.loads(html.split('const DATA=', 1)[1].split(';\nconst meta=', 1)[0])
    payload['cameras'] = json.loads(cameras.read_text(encoding='utf-8'))
    if payload['cameras']['metadata']['cell_m'] != payload['metadata']['cell_m']:
        raise ValueError('Camera and crime grid sizes differ')
    index_grid(payload)
    source = Path(__file__).parent
    template = (source / 'england_crime_map.html').read_text(encoding='utf-8')
    template = template.replace('__ENRICHMENT_SCRIPT__', (source / 'convictions_panel.js').read_text(encoding='utf-8'))
    template = template.replace('__CAMERA_SCRIPT__', (source / 'camera_panel.js').read_text(encoding='utf-8'))
    encoded = json.dumps(payload, separators=(',', ':')).replace('</', '<\\/')
    map_path.write_text(template.replace('__PAYLOAD__', encoded), encoding='utf-8')
    map_path.with_name('cameras_metadata.json').write_text(json.dumps(payload['cameras']['metadata'], indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map', type=Path, required=True)
    parser.add_argument('--cameras', type=Path, required=True)
    args = parser.parse_args()
    attach(args.map, args.cameras)
