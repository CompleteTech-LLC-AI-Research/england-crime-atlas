"""Validate the committed aggregate map and its provenance without raw downloads."""
import argparse
import json
from collections import Counter
from pathlib import Path


def verify(directory):
    source = (directory / 'index.html').read_text(encoding='utf-8')
    assert '__PAYLOAD__' not in source and '__ENRICHMENT_SCRIPT__' not in source
    embedded = source.split('const DATA=', 1)[1].split(';\nconst meta=', 1)[0]
    data = json.loads(embedded)
    metadata = json.loads((directory / 'run_metadata.json').read_text(encoding='utf-8'))
    assert data['metadata'] == metadata, 'HTML and run metadata disagree'
    names = data['categories']
    features = data['geojson']['features']
    category_totals = Counter()
    for feature in features:
        assert set(feature['properties']) == {'counts'}, 'Unexpected incident-level attributes'
        assert len(feature['properties']['counts']) == len(names)
        for name, count in zip(names, feature['properties']['counts']):
            assert isinstance(count, int) and count >= 0
            category_totals[name] += count
    assert dict(category_totals) == metadata['category_counts']
    assert len(features) == metadata['occupied_cells']
    assert sum(category_totals.values()) == metadata['counts']['mapped_rows']
    crime_total = sum(category_totals.values()) - category_totals.get('Anti-social behaviour', 0)
    assert crime_total == metadata['mapped_crime_excluding_asb']
    counts = metadata['counts']
    assert counts['source_rows'] == counts['england_rows'] + counts['non_england_or_missing_lsoa'] + counts.get('duplicate_crime_ids', 0)
    court = data['convictions']
    assert court['metadata'] == metadata['convictions_enrichment']
    assert court['metadata'] == json.loads((directory / 'convictions_metadata.json').read_text(encoding='utf-8'))
    boundaries = court['boundaries']['features']
    assert len(boundaries) == 39
    assert all(f['properties']['PFA24CD'].startswith('E23') for f in boundaries)
    areas, weapons, indictable = Counter(), Counter(), 0
    margin_count = 0
    for record in court['records']:
        assert record['force'] in court['metadata']['area_counts']
        assert isinstance(record['total'], int) and record['total'] > 0
        for dimension in ('sex', 'age', 'ethnicity', 'detailed_ethnicity', 'quarter'):
            assert all(isinstance(n, int) and n >= 0 for n in record[dimension].values())
            assert sum(record[dimension].values()) == record['total'], (record['code'], dimension)
            margin_count += 1
        areas[record['force']] += record['total']
        indictable += record['total'] if record['indictable'] else 0
        if record['group'] == 'Possession of weapons':
            weapons[record['code']] += record['total']
    assert dict(areas) == court['metadata']['area_counts']
    assert sum(areas.values()) == court['metadata']['audit']['selected_convictions']
    unavailable = set(court['metadata']['boundary_areas_without_published_rows'])
    boundary_names = {f['properties']['moj_name'] for f in boundaries}
    assert boundary_names == set(areas) | unavailable
    report = json.loads((directory / 'enrichment_verification.json').read_text(encoding='utf-8'))
    assert report['status'] == 'passed'
    assert report['demographic_marginals_checked'] == margin_count
    assert report['English_area_totals_checked'] == len(areas)
    assert report['English_person_conviction_occasions'] == sum(areas.values())
    assert report['weapon_codes_independently_recounted'] == len(weapons)
    assert report['weapon_conviction_occasions'] == sum(weapons.values())
    assert 'https://tile.openstreetmap.org/{z}/{x}/{y}.png' in source
    assert 'basemaps.cartocdn.com' not in source
    return {'status': 'passed', 'recorded_crimes': crime_total, 'English_profiles': len(areas),
            'person_conviction_occasions': sum(areas.values()), 'indictable_conviction_occasions': indictable,
            'weapon_codes': len(weapons), 'demographic_marginals': margin_count}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('results/2026-07'))
    args = parser.parse_args()
    print(json.dumps(verify(args.directory), indent=2))
