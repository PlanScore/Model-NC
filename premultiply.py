#!/usr/bin/env python3
import sys, pandas, numpy, itertools, logging

filename1, filename2, filename3 = sys.argv[1:]

logging.basicConfig(format='%(asctime)s - %(filename)s - %(message)s',
    stream=sys.stderr, level=logging.INFO)

logging.info('Reading input files...')

# Democratic vote share in file 1,
# absolute turnout in file 2 scaled by .01 in upstream R code
dem_share = pandas.read_csv(filename1)
sims, rows = 1000, dem_share.shape[0]

turnout = pandas.read_csv(filename2)
turnout.iloc[:, -sims:] *= 100

logging.info('Creating output frame...')

# Ignore the blank first column of input to prepare votes output,
# build an empty frame with 2x sims columns for DEM and REP votes,
# concatenate both into a complete votes frame.
votes1 = dem_share.iloc[:, 1:-sims]
votes2 = pandas.DataFrame(data=numpy.empty((rows, sims*2)), dtype=float,
    columns=[f'{party}{sim:03d}' for (sim, party)
        in itertools.product(range(sims), ('DEM', 'REP'))])

votes = pandas.concat((votes1, votes2), axis=1)

# Iterate over simulations populating Democratic and Republican vote shares
s_cols, t_cols = dem_share.columns[-sims:], turnout.columns[-sims:]

for (sim, s_col, t_col) in zip(range(sims), s_cols, t_cols):
    d_col, r_col = f'DEM{sim:03d}', f'REP{sim:03d}'
    votes[d_col] = round(turnout[t_col] * dem_share[s_col], 1)
    votes[r_col] = round(turnout[t_col] * (1 - dem_share[s_col]), 1)

logging.info('Writing output file...')
votes.to_csv(filename3, index=False, compression='gzip')
logging.info('Done.')
