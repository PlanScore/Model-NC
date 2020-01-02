#!/usr/bin/env python3
import sys, pandas, numpy, itertools, logging, argparse

parser = argparse.ArgumentParser()
parser.add_argument('open')
parser.add_argument('turnout')
parser.add_argument('incD')
parser.add_argument('incR')
parser.add_argument('votes')
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s - %(filename)s - %(message)s',
    stream=sys.stderr, level=logging.INFO)

logging.info('Reading input files...')

# Democratic vote share in file 1,
# absolute turnout in file 2 scaled by .01 in upstream R code
dem_share = pandas.read_csv(args.open)
input_sims = len([c for c in dem_share.columns if c.startswith('v.')])
output_sims, rows = 350, dem_share.shape[0]

turnout = pandas.read_csv(args.turnout)
turnout.iloc[:, -input_sims:] *= 100

incd_share = pandas.read_csv(args.incD)
incr_share = pandas.read_csv(args.incR)

logging.info('Creating output frame...')

# Ignore the blank first column of input to prepare votes output,
# build an empty frame with 6x output_sims columns for DEM and REP votes
# in three candidate scenarios, concatenate both into a complete votes frame.
votes1 = dem_share.iloc[:, 1:-input_sims]
votes2 = pandas.DataFrame(data=numpy.empty((rows, output_sims*6)), dtype=float,
    columns=[f'{inc}:{party}{sim:03d}' for (inc, sim, party)
        in itertools.product(('O', 'D', 'R'), range(output_sims), ('DEM', 'REP'))])

votes = pandas.concat((votes1, votes2), axis=1)

# Iterate over simulations populating Democratic and Republican vote shares
s_cols, t_cols = dem_share.columns[-input_sims:], turnout.columns[-input_sims:]
d_cols, r_cols = incd_share.columns[-input_sims:], incr_share.columns[-input_sims:]

for (sim, s_col, t_col, d_col, r_col) in zip(range(output_sims), s_cols, t_cols, d_cols, r_cols):
    turnout_val, share_val = turnout[t_col], dem_share[s_col]
    incd_val, incr_val = incd_share[d_col], incr_share[r_col]

    # Calculate shares for open seat and incumbent scenarios
    open_dem_share = share_val
    open_rep_share = (1 - share_val)
    incd_dem_share = (share_val + incd_val)
    incd_rep_share = (1 - (share_val + incd_val))
    incr_dem_share = (share_val - incr_val)
    incr_rep_share = (1 - (share_val - incr_val))
    
    # Assign raw votes counts rounded to one decimal place
    votes[f'O:DEM{sim:03d}'] = round(turnout_val * open_dem_share, 1)
    votes[f'O:REP{sim:03d}'] = round(turnout_val * open_rep_share, 1)
    votes[f'D:DEM{sim:03d}'] = round(turnout_val * incd_dem_share, 1)
    votes[f'D:REP{sim:03d}'] = round(turnout_val * incd_rep_share, 1)
    votes[f'R:DEM{sim:03d}'] = round(turnout_val * incr_dem_share, 1)
    votes[f'R:REP{sim:03d}'] = round(turnout_val * incr_rep_share, 1)

logging.info('Writing output file...')
votes.to_csv(args.votes, index=False, compression='gzip')
logging.info('Done.')
