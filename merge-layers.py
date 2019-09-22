#!/usr/bin/env python3 -i
import sys, argparse, logging, json, geopandas, pandas, numpy, shapely.geometry

logging.basicConfig(format='%(asctime)s - %(filename)s - %(message)s',
    stream=sys.stderr, level=logging.INFO)

parser = argparse.ArgumentParser(description='Merge layers and votes')
parser.add_argument('geo_name', help='Spatial file with layers and areas')
parser.add_argument('acs_name', help='Tabular CSV file with ACS population')
parser.add_argument('census_name', help='Tabular CSV file with Census population')
parser.add_argument('votecsv_name', help='Tabular CSV file with vote counts')
parser.add_argument('out_name', help='Output GeoJSON file with areas and votes')

args = parser.parse_args()

logging.info('Reading ACS population from {}...'.format(args.acs_name))

acs_df = pandas.read_csv(args.acs_name, index_col='geoid')

populations_df = pandas.DataFrame(index=acs_df.index,
    data=numpy.empty((acs_df.shape[0], 16), dtype=int), columns=[
    'Population 2016', 'Population 2016, Error', 'Households 2016', 'Households 2016, Error',
    'Black Population 2016', 'Black Population 2016, Error', 'Hispanic Population 2016',
    'Hispanic Population 2016, Error', 'Household Income 2016', 'Household Income 2016, Error',
    'Voting-Age Population 2016', 'Voting-Age Population 2016, Error', 'Education Population 2016',
    'Education Population 2016, Error', 'High School or GED 2016', 'High School or GED 2016, Error'
    ])

populations_df['Population 2016'] = acs_df['B01001001']
populations_df['Population 2016, Error'] = acs_df['B01001001, Error']
populations_df['Households 2016'] = acs_df['B11001001']
populations_df['Households 2016, Error'] = acs_df['B11001001, Error']
populations_df['Black Population 2016'] = acs_df['B02009001']
populations_df['Black Population 2016, Error'] = acs_df['B02009001, Error']
populations_df['Hispanic Population 2016'] = acs_df['B03002012']
populations_df['Hispanic Population 2016, Error'] = acs_df['B03002012, Error']
populations_df['Household Income 2016'] = acs_df['B19013001']
populations_df['Household Income 2016, Error'] = acs_df['B19013001, Error']
populations_df['Education Population 2016'] = acs_df['B15003001']
populations_df['Education Population 2016, Error'] = acs_df['B15003001, Error']
populations_df['High School or GED 2016'] = acs_df['B15003017'] + acs_df['B15003018']
populations_df['High School or GED 2016, Error'] = \
    (acs_df['B15003017, Error'] ** 2 + acs_df['B15003018, Error'] ** 2).pow(.5)

# Voting-age population is spread over a range of columns
pop18_keys = [f'B010010{male:02d}' for male in range(7, 26)] \
           + [f'B010010{female:02d}' for female in range(31, 50)]

pop18_var_keys = [f'{key}, Error' for key in pop18_keys]

populations_df['Voting-Age Population 2016'] = acs_df[pop18_keys].sum(axis=1)
populations_df['Voting-Age Population 2016, Error'] \
    = round((acs_df[pop18_var_keys] ** 2).sum(axis=1).pow(.5))

logging.info('Read population for {} areas.'.format(len(populations_df)))
logging.info('Reading vote counts from {}...'.format(args.votecsv_name))

# Aggregate simulated votes by PSID
votes_df = pandas.read_csv(args.votecsv_name)
votes_df = votes_df.groupby(['psid']).agg('sum')

logging.info('Read counts for {} areas.'.format(len(votes_df)))
logging.info('Reading Census population from {}...'.format(args.census_name))

features_json = list()

census_df = pandas.read_csv(args.census_name, index_col='geoid')
census_df['Geometry'] = list(zip(census_df.lon, census_df.lat))
census_df.Geometry = census_df.Geometry.apply(shapely.geometry.Point)
census_df = geopandas.GeoDataFrame(census_df, geometry='Geometry')

property_names = list(set(census_df.columns) - {'lat', 'lon', 'Geometry'})
census_df[property_names] = round(census_df[property_names], 3)

logging.debug('Dumping Census population to JSON features...')

for (geoid, row) in census_df.iterrows():
    geometry = shapely.geometry.mapping(row.Geometry)
    feature_json = dict(type='Feature', geometry=geometry, properties={})
    feature_json['properties'] = dict(geoid=geoid, **row[property_names].to_dict())
    features_json.append(json.dumps(feature_json, sort_keys=True))

block_count = len(features_json)
logging.info('Read population for {} blocks.'.format(block_count))
logging.info('Reading areas from {}...'.format(args.geo_name))

for (_, row) in geopandas.read_file(args.geo_name, layer='tracts').iterrows():
    try:
        feature_geoid = '14000US{}'.format(row.geoid)
        geometry = shapely.geometry.mapping(row.geometry)
        properties = populations_df.loc[feature_geoid].to_dict()
        feature_json = dict(type='Feature', geometry=geometry, properties=properties)
        features_json.append(json.dumps(feature_json, sort_keys=True))
    except KeyError:
        logging.debug(f'Missing feature {feature_geoid} in populations_df')

for (_, row) in geopandas.read_file(args.geo_name, layer='precincts').iterrows():
    try:
        feature_psid = 'PSID:{}'.format(row.psid)
        geometry = shapely.geometry.mapping(row.geometry)
        properties = votes_df.loc[feature_psid].to_dict()
        feature_json = dict(type='Feature', geometry=geometry, properties=properties)
        features_json.append(json.dumps(feature_json, sort_keys=True))
    except KeyError:
        logging.debug(f'Missing precinct {feature_psid} in votes_df')

logging.info('Read {} areas.'.format(len(features_json) - block_count))
logging.info('Writing areas to {}...'.format(args.out_name))

with open(args.out_name, 'w') as file3:
    print('{"type": "FeatureCollection", "features": [', file=file3)
    print(',\n'.join(features_json), file=file3)
    print(']}', file=file3)
