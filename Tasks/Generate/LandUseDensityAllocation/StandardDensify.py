import shapely, random
from shapely import MultiPoint, voronoi_polygons, Polygon, Point
import geopandas as gpd
from Utilities.Utilities import *

@enforce_bounds({})
def main(UDS, Target_GFA, landuse):

    inside_UDS, outside_UDS = IncludeUDSWithinBoundaries(UDS, [shape(SA['geometry']) for SA in UDS['Phenotype']['StudyAreas']])
    Outside_GFA = np.nansum(GetGFA(outside_UDS))
    inside_parcel_area = sum([shape(PB['geometry']).area for PB in inside_UDS['Phenotype']['ParcelBoundaries']])
    new_GPR = round((Target_GFA - Outside_GFA) / inside_parcel_area,2)

    for i in range(len(inside_UDS['Phenotype']['ParcelBoundaries'])):
        inside_UDS['Phenotype']['ParcelBoundaries'][i]['properties']['GPR'] = new_GPR
        inside_UDS['Phenotype']['ParcelBoundaries'][i]['properties']['landuse'] = landuse

    for key, features in inside_UDS['Phenotype'].items():

        if key not in outside_UDS['Phenotype']: outside_UDS['Phenotype'][key] = []

        outside_UDS['Phenotype'][key] += features
    
    UDS = outside_UDS
    UDS = UpdateParameters(UDS,{'StandardDensify':{
        'Target_GFA': Target_GFA, 
        'landuse': landuse,
        }})
    UDS = UpdateID(UDS)
    return UDS