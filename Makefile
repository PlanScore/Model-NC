all: NC-Precinct-Model.NC-House.votes.geojson \
     NC-Precinct-Model.NC-Senate.votes.geojson \
     NC-Precinct-Model.US-House.votes.geojson

# Spatial votes are calculated from raw votes and geographic areas
%.geojson: ACS-data.csv %.csv.gz
	./merge-layers.py NC-Geographies.gpkg NC-Votes.csv.gz $^ $@

# Raw votes are calculated from Dem proportion and turnout estimates
%.votes.csv.gz: %.propD.csv.gz %.turnout.csv.gz
	./premultiply.py $^ $@

# Read Census ACS data from Census Reporter by tract (140).
# Table B01001: Sex by Age, https://censusreporter.org/tables/B01001/
# Table B02009: Black Alone or in Combination, https://censusreporter.org/tables/B02009/
# Table B03002: Hispanic Origin by Race, https://censusreporter.org/tables/B03002/
ACS-data.csv:
	mkdir -p ACS-temp
	curl -L 'https://api.censusreporter.org/1.0/data/download/latest?table_ids={B01001,B02009,B03002}&geo_ids=04000US37,140|04000US37&format=csv' -o 'ACS-temp/#1.zip' -s
	parallel unzip -o -d ACS-temp ::: ACS-temp/*.zip
	csvjoin -c geoid ACS-temp/acs2015_5yr_*/*.csv > $@
