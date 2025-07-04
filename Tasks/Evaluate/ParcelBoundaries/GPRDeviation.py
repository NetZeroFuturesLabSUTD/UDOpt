import os, json, random, copy, math
from shapely.geometry import Point, Polygon, LineString, shape

from Utilities.Visualize import *
from Utilities.Utilities import *

def main(UDS):

    total_score = 0

    for i, PB in enumerate(UDS['Features']['ParcelBoundaries']):

        try:

            allocated_GPR = float(PB['properties']['GPR'])

            boundary = shape(PB['geometry'])

            UDS_include, _ = IncludeUDSWithinBoundaries(UDS, [boundary])

            GFA = [shape(BF['geometry']).area*BF['properties']['levels'] for BF in UDS_include['Features']['BuildingFootprints']]

            acheived_GPR = sum(GFA) / boundary.area

            GPRDeviation = abs(allocated_GPR - acheived_GPR)

            UDS['Features']['ParcelBoundaries'][i]['properties']['GPRDeviation'] = GPRDeviation

            total_score += GPRDeviation
        
        except:
            
            pass

    UDS['Evaluations']['TotalGPRDeviation'] = total_score

    return UDS