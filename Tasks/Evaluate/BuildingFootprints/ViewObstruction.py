import os, json, random, copy, math
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import shapely
import matplotlib.pyplot as plt
import geopandas as gpd

from Utilities.Visualize import *
from Utilities.Utilities import *


def main(UDS,distance=50):

    # get df of all BG with some important info
    abdf = []
    for BF in UDS['Phenotype']['BuildingFootprints']:
        try:
            abdf.append({
                'total_height':BF['properties']['height'],
                'total_levels':BF['properties']['levels'],
                'base_height':min([coor[2] for coor in BF['geometry']['coordinates'][0]]),
                'f2f_height':BF['properties']['height']/BF['properties']['levels'],
                'geometry':shape(BF['geometry'])
            })
        except Exception as e: 
            print(e)
    abdf = pd.DataFrame(abdf)
    abdf

    # count score for each row
    distance_threshold = 50
    total_score = 0
    for i,row in abdf.iterrows():
        try:

            # split to main and others
            main_df = abdf.iloc[[i]]
            others_df = abdf.drop(index=i)
            others_df['distance'] = [geometry.distance(main_df.iloc[0].geometry) for geometry in others_df.geometry]
            others_df = others_df.loc[others_df['distance'] < distance_threshold]

            # for each level in main, calculate number of nearby buildings that are at least as high as current level.
            ViewObstructionCount = []
            for level in range(main_df['total_levels'].iloc[0]):
                main_Z = (main_df.base_height + (level*main_df.f2f_height)).values[0]
                sub_others_df = others_df.loc[others_df.total_height >= main_Z]
                ViewObstructionCount.append(sub_others_df.shape[0])
            UDS['Phenotype']['BuildingFootprints'][i]['properties']['ViewObstruction'] = sum(ViewObstructionCount)
            total_score += sum(ViewObstructionCount)
        except Exception as e: 
            print(e)
    UDS['Genotype']['TotalViewObstruction'] = total_score
    return UDS
