#!/usr/bin/env python3
import sys, argparse, gzip, csv, re, collections, logging, json, math
from osgeo import ogr

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)09s - %(message)s')

parser = argparse.ArgumentParser(description='Merge layers and votes')
parser.add_argument('geo_name', help='Spatial file with layers and areas')
parser.add_argument('votes_name', help='Tabular CSV file with vote counts')
parser.add_argument('acs_name', help='Tabular CSV file with ACS population')
parser.add_argument('model_name', help='Tabular CSV file with model vote counts')
parser.add_argument('out_name', help='Output GeoJSON file with areas and votes')

args = parser.parse_args()

logging.info('Reading ACS population from {}...'.format(args.acs_name))

populations = collections.defaultdict(lambda: collections.defaultdict(int))

with open(args.acs_name, 'r') as acs_file:
    rows = csv.DictReader(acs_file)
    vpop_keys = [f'B010010{male:02d}' for male in range(7, 26)] \
              + [f'B010010{female:02d}' for female in range(31, 50)]
    
    for row in rows:
        geoid, _ = row.pop('geoid'), row.pop('name')
        populations[geoid]['Population 2015'] = int(row['B01001001'])
        populations[geoid]['Population 2015, Error'] = int(row['B01001001, Error'])
        populations[geoid]['Black Population 2015'] = int(row['B02009001'])
        populations[geoid]['Black Population 2015, Error'] = int(row['B02009001, Error'])
        populations[geoid]['Hispanic Population 2015'] = int(row['B03002012'])
        populations[geoid]['Hispanic Population 2015, Error'] = int(row['B03002012, Error'])
        
        vpop = [int(row[k]) for k in vpop_keys]
        populations[geoid]['Voting-Age Population 2015'] = sum(vpop)

        vpop_var = [int(row[f'{k}, Error']) ** 2 for k in vpop_keys]
        populations[geoid]['Voting-Age Population 2015, Error'] = round(math.sqrt(sum(vpop_var)))
        
logging.info('Read population for {} areas.'.format(len(populations)))
logging.info('Reading model vote counts from {}...'.format(args.model_name))

votes = collections.defaultdict(lambda: collections.defaultdict(float))
model_pattern = re.compile(r'^(DEM|REP)\d+$')

with gzip.open(args.model_name, 'rt') as file2:
    for row in csv.DictReader(file2):
        psid = int(row['psid'].split(':', 2)[1])
        for (key, value) in row.items():
            if model_pattern.match(key):
                votes[psid][key] += float(value)

logging.info('Reading other vote counts from {}...'.format(args.votes_name))
votes_pattern = re.compile(r'.* - (DEM|REP)$')

with gzip.open(args.votes_name, 'rt') as votes_file:
    for row in csv.DictReader(votes_file):
        if ':' not in row['PSID']:
            continue
        psid = int(row['PSID'].split(':', 2)[1])
        for (key, value) in row.items():
            if votes_pattern.match(key):
                votes[psid][key] += int(value)

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

for layer in (ds.GetLayer('precincts'), ):
    for feature in layer:
        feature_json = json.loads(feature.ExportToJson())
        properties = feature_json['properties']
        properties.update({key: round(value, 1)
            for (key, value) in votes[properties['psid']].items()
            if model_pattern.match(key) or votes_pattern.match(key)})
        features_json.append(json.dumps(feature_json, sort_keys=True))

logging.info('Read {} areas.'.format(len(features_json)))
logging.info('Writing areas to {}...'.format(args.out_name))

with open(args.out_name, 'w') as file3:
    print('{"type": "FeatureCollection", "features": [', file=file3)
    print(',\n'.join(features_json), file=file3)
    print(']}', file=file3)
