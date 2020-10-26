all: NC-District-Model.votes.geojson

old: NC-Precinct-Model.US-House.votes.geojson \
     NC-Precinct-Model.NC-House.votes.geojson \
     NC-Precinct-Model.NC-Senate.votes.geojson

# Spatial votes are calculated from raw votes and geographic areas
%.geojson: ACS-data.csv Census-data.csv.gz %.csv.gz
	./merge-layers.py NC-Geographies.gpkg $^ $@

# Raw votes are calculated from Dem proportion, turnout estimates, and incumbency effects
%.votes.csv.gz: %.open.csv.gz %.turnout.csv.gz %.incD.csv.gz %.incR.csv.gz
	./premultiply.py $^ $@

# Read Census ACS data from Census Reporter by tract (140).
# Table B01001: Sex by Age, https://censusreporter.org/tables/B01001/
# Table B02009: Black Alone or in Combination, https://censusreporter.org/tables/B02009/
# Table B03002: Hispanic Origin by Race, https://censusreporter.org/tables/B03002/
# Table B11001: Household Type, https://censusreporter.org/tables/B11001/
# Table B15003: Educational Attainment, https://censusreporter.org/tables/B15003/
# Table B19013: Median Household Income, https://censusreporter.org/tables/B19013/
ACS-data.csv:
	mkdir -p ACS-temp
	curl -L 'https://api.censusreporter.org/1.0/data/download/latest?table_ids={B01001,B02009,B03002,B11001,B15003,B19013}&geo_ids=04000US37,140|04000US37&format=csv' -o 'ACS-temp/#1.zip' -s
	parallel unzip -o -d ACS-temp ::: ACS-temp/*.zip
	csvjoin -c geoid ACS-temp/acs2017_5yr_*/*.csv > $@

Census-data.csv.gz: nc2010.sf1.zip CVAP_CSV_Format_2011-2015.zip
	unzip -o nc2010.sf1.zip ncgeo2010.sf1 nc000032010.sf1 nc000042010.sf1
	unzip -o CVAP_CSV_Format_2011-2015.zip BlockGr.csv
	./zip-census-SF1.py | gzip --stdout > $@

nc2010.sf1.zip:
	curl -L https://www2.census.gov/census_2010/04-Summary_File_1/North_Carolina/nc2010.sf1.zip -o $@

CVAP_CSV_Format_2011-2015.zip:
	curl -L https://www.census.gov/rdo/pdf/CVAP_CSV_Format_2011-2015.zip -o $@
