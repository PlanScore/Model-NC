all: NC-Precinct-Model.NC-House.votes.geojson \
     NC-Precinct-Model.NC-Senate.votes.geojson \
     NC-Precinct-Model.US-House.votes.geojson

# Spatial votes are calculated from raw votes and geographic areas
%.geojson: %.csv.gz
	./merge-layers.py NC-Geographies.gpkg $< $@

# Raw votes are calculated from Dem proportion and turnout estimates
%.votes.csv.gz: %.propD.csv.gz %.turnout.csv.gz
	./premultiply.py $^ $@
