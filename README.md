# England Crime Atlas

An interactive map of recorded crime in England, with a separate regional view of convicted-person demographics and detailed legal offences. A project by **CompleteTech LLC AI Research**.

## Explore the map

```powershell
python -m http.server 8766 --bind 127.0.0.1 --directory results
```

Open **http://127.0.0.1:8766/2026-07/index.html**. If port 8766 is already occupied, use 8767 instead. Internet access is needed for Leaflet and OpenStreetMap tiles. Serve the page over localhost so tile requests include a web referrer.

The [published HTML](results/2026-07/index.html) is self-contained apart from its mapping library and basemap tiles. Download it or clone this repository to view it; GitHub's file browser shows HTML source.

| View | Period | What it shows |
| --- | --- | --- |
| Recorded crime | July 2026 | 408,722 mappable recorded crimes in 2 km British National Grid cells; optional ASB view includes another 87,621 records |
| Conviction profiles | April 2025–March 2026 | Regional conviction occasions for records classified as persons, with sex, age, ethnicity, quarterly outcomes and detailed offence codes |

Use the crime-category selector, click cells for category counts, and adjust overlay opacity to reveal roads and place names. In **Conviction profiles**, choose a force area or click its polygon, then filter by offence group, subtype and detailed Home Office code. Charts show unknown-value coverage alongside the selected counts.

**Explore weapon offences** opens nine offence subtypes and 40 detailed codes with convictions in the selected period. These include bladed articles in public or on school premises, firearm/imitation-firearm offences, shotgun certificate offences and corrosive substances in public. Across all offence groups, 325 subtypes and 867 detailed codes are available.

## Interpret the results

- Crime counts are available recorded reports, not population-adjusted rates or personal safety scores. Published locations are anonymised approximations. England membership uses source LSOA codes starting `E01`; cells can cross country borders.
- July crime files are missing for British Transport Police, Gloucestershire, Greater Manchester and North Yorkshire. Records without an LSOA cannot be assigned to England and are excluded. Blank areas are not evidence of zero crime.
- Conviction statistics are **separate regional context**: they cannot identify the offender behind a mapped incident. Published court-statistics geography is not offender residence or exact crime location, and court completion dates differ from crime occurrence dates.
- Conviction counts describe occasions on a principal-offence basis, not distinct individuals. Records classified as companies/public bodies or unknown person status are excluded. Unknown demographic values within included person records remain in chart denominators.
- The default indictable-offence view has 214,584 conviction occasions; the all-offence view has 820,587. Ethnicity is poorly recorded for summary offences. Each demographic chart is a separate marginal distribution: charts cannot be added together or interpreted as demographic intersections.
- There are 38 published English area profiles. City of London's separate boundary has no separate published profile in this extract and is labelled unavailable.
- Weapon labels describe legal offences, not complete physical specifications. A generic offensive-weapon code cannot tell us whether the item was a knife, bat or another object. The broad weapons group also contains threats, intent, supply and marketing offences; read the full selected code label.
- Do not divide these court counts by July crime counts to calculate conviction rates.

## Reproduce

Requires Python 3.10+; no API keys or paid inference services are used.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python src/download_england_crime.py --month 2026-07
python src/download_moj.py
python src/prepare_moj_enrichment.py
python src/generate_england_crime.py --input data/england-crime-2026-07.zip --output-dir results/2026-07 --convictions data/moj-convictions-2026.json
python src/verify_moj_enrichment.py
python src/verify_published_map.py
```

On macOS/Linux, activate with `source .venv/bin/activate` and use `python3` where appropriate. Omit `--month` to download the latest Police.uk month and update the subsequent input/output paths accordingly. The MoJ downloader deliberately pins the March 2026 publication. Downloads can be revised by publishers, so reruns are not guaranteed to be byte-for-byte identical.

Raw archives, local intermediate data and Python environments are ignored. Downloads have SHA-256 receipts; preparation validates the source archive, streams the CSV and retains disjoint offence aggregates and separate demographic margins. The map embeds only aggregate counts, provenance and simplified regional boundaries.

## Verification

The original MoJ CSV was independently reread to reconcile all 38 English area totals and all 40 weapon-code totals. All **60,190 demographic margins** reconciled. Browser checks covered offence groups, all weapon codes and regional profiles, fiscal-quarter ordering, missing-area handling, demographic charts, basemap visibility and switching back to the original July crime counts.

GitHub Actions validates the published embedded data and metadata without downloading source archives. This establishes artifact consistency; it does not validate statistical representativeness or infer missing records.

- [Crime and combined-run provenance](results/2026-07/run_metadata.json)
- [Court-data provenance](results/2026-07/convictions_metadata.json)
- [Independent source verification](results/2026-07/enrichment_verification.json)

## Official sources

- [Police.uk downloads](https://data.police.uk/data/), [definitions](https://data.police.uk/about/) and [known gaps](https://data.police.uk/changelog/)
- [MoJ Criminal Justice Statistics Quarterly: March 2026](https://www.gov.uk/government/statistics/criminal-justice-statistics-quarterly-march-2026)
- [MoJ technical guide](https://assets.publishing.service.gov.uk/media/6a689bd8f938595f17d020ec/criminal-justice-statistics-technical-guide-Q1-2026.pdf)
- [ONS December 2024 police-force boundaries](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Police_Force_Areas_Dec_2024_EW_BGC/FeatureServer)

See [data attribution and licences](DATA_LICENSES.md).
