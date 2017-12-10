#!/usr/bin/env python3
import csv, sys, statistics, gzip, argparse

parser = argparse.ArgumentParser(description='Premultiply votes')
parser.add_argument('filename1', help='Tabular CSV file with Democrat vote proportion')
parser.add_argument('filename2', help='Tabular CSV file with estimated turnout')
parser.add_argument('filename3', help='Output CSV file with party vote totals')

args = parser.parse_args()

with gzip.open(args.filename1, 'rt') as file1, gzip.open(args.filename2, 'rt') as file2:
    rows1 = csv.reader(file1)
    rows2 = csv.reader(file2)
    
    head1, head2 = next(rows1), next(rows2)
    
    if head1[:4] != head2[:4] or len(head1) != 1004 or len(head2) != 1004:
        raise Exception()
    
    with gzip.open(args.filename3, 'wt') as file3:
        columns = ['county', 'precinct', 'psid']
        for i in range(1000):
            columns += [f'DEM{i:03d}', f'REP{i:03d}']
        
        out = csv.writer(file3)
        out.writerow(columns)
        
        for (row1, row2) in zip(rows1, rows2):
            row = row1[1:4]
            propDs = list(map(float, row1[4:]))
            turnouts = list(map(float, row2[4:]))
            
            print(' '.join(row),
                #'{:.3f} ±{:.3f}'.format(statistics.mean(propDs),
                #statistics.stdev(propDs)),
                #'{:.0f} ±{:.0f}'.format(statistics.mean(turnouts),
                #statistics.stdev(turnouts)),
                file=sys.stderr)
            
            for (propD, turnout) in zip(propDs, turnouts):
                dem_votes = propD * turnout
                rep_votes = turnout - dem_votes
                row += [f'{dem_votes:.1f}', f'{rep_votes:.1f}']
            
            out.writerow(row)
