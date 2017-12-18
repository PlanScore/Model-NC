#!/usr/bin/env python3
import sys, argparse, gzip, csv, re, collections, logging, json
from osgeo import ogr

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)09s - %(message)s')

parser = argparse.ArgumentParser(description='Merge layers and votes')
parser.add_argument('geo_name', help='Spatial file with layers and areas')
parser.add_argument('acs_name', help='Tabular CSV file with ACS population')
parser.add_argument('votecsv_name', help='Tabular CSV file with vote counts')
parser.add_argument('out_name', help='Output GeoJSON file with areas and votes')

args = parser.parse_args()

logging.info('Reading ACS population from {}...'.format(args.acs_name))

populations = collections.defaultdict(lambda: collections.defaultdict(int))

with open(args.acs_name, 'r') as acs_file:
    rows = csv.DictReader(acs_file)
    
    for row in rows:
        geoid, _ = row.pop('geoid'), row.pop('name')
        populations[geoid]['Population'] += int(row['B01001001'])
        populations[geoid]['Population, Error'] += int(row['B01001001, Error'])

logging.info('Read population for {} areas.'.format(len(populations)))
logging.info('Reading vote counts from {}...'.format(args.votecsv_name))

votes = collections.defaultdict(lambda: collections.defaultdict(float))
column_pattern = re.compile(r'^(DEM|REP)\d+$')

with gzip.open(args.votecsv_name, 'rt') as file2:
    rows = csv.DictReader(file2)
    
    for row in rows:
        #break
        psid = int(row['psid'].split(':', 2)[1])
        for (key, value) in row.items():
            if column_pattern.match(key):
                votes[psid][key] += float(value)

logging.info('Read counts for {} areas.'.format(len(votes)))
logging.info('Reading areas from {}...'.format(args.geo_name))

ds = ogr.Open(args.geo_name)
features_json = list()

for feature in ds.GetLayer('tracts'):
    feature_json = json.loads(feature.ExportToJson())
    properties = feature_json['properties']
    feature_geoid = properties['geoid']
    properties.update(populations[f'14000US{feature_geoid}'])
    features_json.append(json.dumps(feature_json, sort_keys=True))

for layer in (ds.GetLayer('counties'), ds.GetLayer('precincts')):
    for feature in layer:
        feature_json = json.loads(feature.ExportToJson())
        properties = feature_json['properties']
        properties.update({key: round(value, 1) for (key, value)
            in votes[properties['psid']].items() if column_pattern.match(key)})
        features_json.append(json.dumps(feature_json, sort_keys=True))

logging.info('Read {} areas.'.format(len(features_json)))
logging.info('Writing areas to {}...'.format(args.out_name))

with open(args.out_name, 'w') as file3:
    print('{"type": "FeatureCollection", "features": [', file=file3)
    print(',\n'.join(features_json), file=file3)
    print(']}', file=file3)
