all: NC-Precinct-Model.NC-House.votes.csv.gz \
     NC-Precinct-Model.NC-Senate.votes.csv.gz \
     NC-Precinct-Model.US-House.votes.csv.gz

# Raw votes are calculated from Dem proportion and turnout estimates
%.votes.csv.gz: %.propD.csv.gz %.turnout.csv.gz
	./premultiply.py $^ $@
