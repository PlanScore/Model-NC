#!/usr/bin/env python3
import sys, argparse, gzip, csv, re, collections, logging, json
from osgeo import ogr

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(levelname)09s - %(message)s')

parser = argparse.ArgumentParser(description='Merge layers and votes')
parser.add_argument('filename1', help='Spatial file with layers and areas')
parser.add_argument('filename2', help='Tabular CSV file with vote counts')
parser.add_argument('filename3', help='Output GeoJSON file with areas and votes')

args = parser.parse_args()

votes = collections.defaultdict(lambda: collections.defaultdict(float))
column_pattern = re.compile(r'^(DEM|REP)\d+$')

logging.info('Reading vote counts from {}...'.format(args.filename2))

with gzip.open(args.filename2, 'rt') as file2:
    rows = csv.DictReader(file2)
    
    for row in rows:
        #break
        psid = int(row['psid'].split(':', 2)[1])
        for (key, value) in row.items():
            if column_pattern.match(key):
                votes[psid][key] += float(value)

logging.info('Read counts for {} areas.'.format(len(votes)))
logging.info('Reading areas from {}...'.format(args.filename1))

ds = ogr.Open(args.filename1)
features_json = list()

for layer in ds:
    for feature in layer:
        feature_json = json.loads(feature.ExportToJson())
        properties = feature_json['properties']
        properties.update({key: round(value, 1) for (key, value)
            in votes[properties['psid']].items() if column_pattern.match(key)})
        features_json.append(json.dumps(feature_json, sort_keys=True))

logging.info('Read {} areas.'.format(len(features_json)))
logging.info('Writing areas to {}...'.format(args.filename3))

with open(args.filename3, 'w') as file3:
    print('{"type": "FeatureCollection", "features": [', file=file3)
    print(',\n'.join(features_json), file=file3)
    print(']}', file=file3)
