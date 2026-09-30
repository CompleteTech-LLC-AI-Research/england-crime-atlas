"""Snapshot Bristol's public CCTV layer and join distinct positions to the crime grid."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from pyproj import Transformer

SOURCE = 'https://maps1.bristol.gov.uk/server/rest/services/Pinpoint125/MapServer/30'
PAGE = 'https://www.bristol.gov.uk/residents/crime-and-emergencies/cctv-in-bristol'


def prepare(output, raw_dir, cell_m=2000):
    raw_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    def get(url, **params):
        response = session.get(url, params={'f': 'json', **params}, timeout=60)
        response.raise_for_status()
        data = response.json()
        if 'error' in data:
            raise ValueError(data['error'])
        return data, response.content
    layer, _ = get(SOURCE)
    count, _ = get(SOURCE + '/query', where='1=1', returnCountOnly='true')
    data, raw = get(SOURCE + '/query', where='1=1', outFields='OBJECTID,FEATURE_LOCATION,SYNERGY_CAMERA_ID',
                    outSR=27700, returnGeometry='true', orderByFields='OBJECTID')
    rows = data['features']
    if data.get('exceededTransferLimit') or len(rows) != count['count']:
        raise ValueError('Incomplete camera snapshot; pagination required')
    (raw_dir / 'bristol-cctv-source.json').write_bytes(raw)
    inverse = Transformer.from_crs(27700, 4326, always_xy=True)
    positions = defaultdict(list)
    excluded = []
    for row in rows:
        geometry = row.get('geometry') or {}
        x, y = geometry.get('x'), geometry.get('y')
        # Pilot extent includes the council's explicitly documented out-of-area cameras.
        if x is None or y is None or not (math.isfinite(x) and math.isfinite(y)
                and 345000 <= x <= 380000 and 150000 <= y <= 195000):
            excluded.append(row['attributes']['OBJECTID'])
            continue
        positions[(round(x, 2), round(y, 2))].append(row['attributes'])
    points = []
    for (x, y), records in sorted(positions.items()):
        lon, lat = inverse.transform(x, y)
        points.append({'x': x, 'y': y, 'lat': lat, 'lon': lon,
                       'grid': [math.floor(x / cell_m), math.floor(y / cell_m)],
                       'records': [{'id': r['OBJECTID'], 'label': r.get('FEATURE_LOCATION') or 'Unnamed position',
                                    'camera_id': r.get('SYNERGY_CAMERA_ID')} for r in records]})
    metadata = {'source': SOURCE, 'source_page': PAGE, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_description': layer['description'],
                'source_record_count': len(rows), 'distinct_positions': len(points),
                'colocated_extra_records': len(rows) - len(excluded) - len(points),
                'excluded_record_ids': excluded, 'cell_m': cell_m,
                'coverage_status': 'unknown', 'effectiveness_status': 'not assessable',
                'licence_status': 'No explicit reuse licence found on the layer or portal item; local pilot only.',
                'attribution': 'Bristol City Council; portal attribution includes OS Crown copyright and database rights 2026 OS 100023406.',
                'notes': ['Includes some South Gloucestershire cameras; not a Bristol administrative boundary census.',
                          'Records at identical centimetre-rounded positions are grouped, not assumed to be a single camera.',
                          'Direction, field of view, range, active dates, outages and incident assistance are unavailable.',
                          'Current camera positions cannot establish their presence during the July 2026 crime month.',
                          'Proximity circles and their intersections are hypothetical, not CCTV viewing areas.',
                          'Anonymised crime coordinates and 2 km cells cannot establish incident visibility.',
                          'No listed positions means no positions in this source, not no cameras.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'metadata': metadata, 'positions': points}, separators=(',', ':')), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/cameras'))
    parser.add_argument('--cell-m', type=int, default=2000)
    args = parser.parse_args()
    prepare(args.output, args.raw_dir, args.cell_m)
