#!/usr/bin/env python3
import sys, csv

# https://factfinder.census.gov/help/en/summary_level_code_list.htm
STATE_SUMLEV = '040'
COUNTY_SUMLEV = '050'
TRACT_SUMLEV = '140'
BLOCK_SUMLEV = '101'

def line_part(line, start, length):
    '''
    '''
    return line[start-1:length+start-1]

with open('ncgeo2010.sf1') as file1, open('nc000032010.sf1') as file2, open('nc000042010.sf1') as file3:
    rows2, rows3 = csv.reader(file2), csv.reader(file3)
    output = csv.DictWriter(sys.stdout,
        ('geoid', 'lat', 'lon', 'Population 2010', 'Hispanic Population 2010',
        'Black Population 2010', 'Voting-Age Population 2010',
        'Hispanic Voting-Age Population 2010', 'Black Voting-Age Population 2010', ),
        dialect='excel')
    output.writeheader()
    
    for (line1, row2, row3) in zip(file1, rows2, rows3):
        SUMLEV = line_part(line1, 9, 3)
        GEOCOMP = line_part(line1, 12, 2)
        STATE = line_part(line1, 28, 2)
        COUNTY = line_part(line1, 30, 3).rstrip()
        TRACT = line_part(line1, 55, 6).rstrip()
        BLOCK = line_part(line1, 62, 4).rstrip()
        geoid = f'{SUMLEV}00{GEOCOMP}US{STATE}{COUNTY}{TRACT}{BLOCK}'

        geo = dict(
            LOGRECNO = line_part(line1, 19, 7),
            POP100 = line_part(line1, 319, 9), # Total population
            INTPTLAT = line_part(line1, 337, 11),
            INTPTLON = line_part(line1, 348, 12),
            )
        
        sf1_3 = dict(
            LOGRECNO = row2[4],
            P0090001 = row2[125+1], # Total Population
            P0090002 = row2[125+2], # Hispanic or Latino
            P0090006 = row2[125+6], # Black Alone
            P0090013 = row2[125+13], # Partially-Black
            P0090018 = row2[125+18], # Partially-Black
            P0090019 = row2[125+19], # Partially-Black
            P0090020 = row2[125+20], # Partially-Black
            P0090021 = row2[125+21], # Partially-Black
            P0090029 = row2[125+29], # Partially-Black
            P0090030 = row2[125+30], # Partially-Black
            P0090031 = row2[125+31], # Partially-Black
            P0090032 = row2[125+32], # Partially-Black
            P0090039 = row2[125+39], # Partially-Black
            P0090040 = row2[125+40], # Partially-Black
            P0090041 = row2[125+41], # Partially-Black
            P0090042 = row2[125+42], # Partially-Black
            P0090043 = row2[125+43], # Partially-Black
            P0090044 = row2[125+44], # Partially-Black
            P0090050 = row2[125+50], # Partially-Black
            P0090051 = row2[125+51], # Partially-Black
            P0090052 = row2[125+52], # Partially-Black
            P0090053 = row2[125+53], # Partially-Black
            P0090054 = row2[125+54], # Partially-Black
            P0090055 = row2[125+55], # Partially-Black
            P0090060 = row2[125+60], # Partially-Black
            P0090061 = row2[125+61], # Partially-Black
            P0090062 = row2[125+62], # Partially-Black
            P0090063 = row2[125+63], # Partially-Black
            )
        
        sf1_4 = dict(
            LOGRECNO = row3[4],
            P0100001 = row3[5], # Total 18+ Population
            P0110001 = row3[75+1], # Total 18+ Population
            P0110002 = row3[75+2], # Hispanic or Latino 18+ Population
            P0110006 = row3[75+6], # Black Alone 18+ Population
            P0110013 = row3[75+13], # Partially-Black 18+ Population
            P0110018 = row3[75+18], # Partially-Black 18+ Population
            P0110019 = row3[75+19], # Partially-Black 18+ Population
            P0110020 = row3[75+20], # Partially-Black 18+ Population
            P0110021 = row3[75+21], # Partially-Black 18+ Population
            P0110029 = row3[75+29], # Partially-Black 18+ Population
            P0110030 = row3[75+30], # Partially-Black 18+ Population
            P0110031 = row3[75+31], # Partially-Black 18+ Population
            P0110032 = row3[75+32], # Partially-Black 18+ Population
            P0110039 = row3[75+39], # Partially-Black 18+ Population
            P0110040 = row3[75+40], # Partially-Black 18+ Population
            P0110041 = row3[75+41], # Partially-Black 18+ Population
            P0110042 = row3[75+42], # Partially-Black 18+ Population
            P0110043 = row3[75+43], # Partially-Black 18+ Population
            P0110044 = row3[75+44], # Partially-Black 18+ Population
            P0110050 = row3[75+50], # Partially-Black 18+ Population
            P0110051 = row3[75+51], # Partially-Black 18+ Population
            P0110052 = row3[75+52], # Partially-Black 18+ Population
            P0110053 = row3[75+53], # Partially-Black 18+ Population
            P0110054 = row3[75+54], # Partially-Black 18+ Population
            P0110055 = row3[75+55], # Partially-Black 18+ Population
            P0110060 = row3[75+60], # Partially-Black 18+ Population
            P0110061 = row3[75+61], # Partially-Black 18+ Population
            P0110062 = row3[75+62], # Partially-Black 18+ Population
            P0110063 = row3[75+63], # Partially-Black 18+ Population
            )
        
        assert geo['LOGRECNO'] == sf1_3['LOGRECNO']
        assert geo['LOGRECNO'] == sf1_4['LOGRECNO']
        assert int(geo['POP100']) == int(sf1_3['P0090001'])
        assert int(sf1_4['P0100001']) == int(sf1_4['P0110001'])
        assert int(sf1_4['P0110002']) <= int(sf1_3['P0090002'])
        assert int(sf1_4['P0110006']) <= int(sf1_3['P0090006'])
        
        if SUMLEV not in (BLOCK_SUMLEV, ):
            continue
        
        print(geoid, geo, file=sys.stderr)
        
        output.writerow({
            'geoid': geoid,
            'lat': float(geo['INTPTLAT'].lstrip('+')),
            'lon': float(geo['INTPTLON'].lstrip('+')),

            # Table P9: Hispanic and non-Hispanic race for total population
            'Population 2010': int(sf1_3['P0090001']),
            'Hispanic Population 2010': int(sf1_3['P0090002']),
            
            # Every non-Hispanic Black or African American
            'Black Population 2010': sum([int(sf1_3[key]) for key in (
                'P0090006', 'P0090013', 'P0090018', 'P0090019', 'P0090020',
                'P0090021', 'P0090029', 'P0090030', 'P0090031', 'P0090032',
                'P0090039', 'P0090040', 'P0090041', 'P0090042', 'P0090043',
                'P0090044', 'P0090050', 'P0090051', 'P0090052', 'P0090053',
                'P0090054', 'P0090055', 'P0090060', 'P0090061', 'P0090062',
                'P0090063', )]),

            # Table P11: Hispanic and non-Hispanic race for 18+
            'Voting-Age Population 2010': int(sf1_4['P0110001']),
            'Hispanic Voting-Age Population 2010': int(sf1_4['P0110002']),

            # Every 18+ non-Hispanic Black or African American
            'Black Voting-Age Population 2010': sum([int(sf1_4[key]) for key in (
                'P0110006', 'P0110013', 'P0110018', 'P0110019', 'P0110020',
                'P0110021', 'P0110029', 'P0110030', 'P0110031', 'P0110032',
                'P0110039', 'P0110040', 'P0110041', 'P0110042', 'P0110043',
                'P0110044', 'P0110050', 'P0110051', 'P0110052', 'P0110053',
                'P0110054', 'P0110055', 'P0110060', 'P0110061', 'P0110062',
                'P0110063', )])
            })
