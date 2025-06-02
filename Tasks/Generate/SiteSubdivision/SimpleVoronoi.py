import shapely, random
from shapely import MultiPoint, voronoi_polygons, Polygon, Point
import geopandas as gpd
from Utilities.Utilities import *

def random_points_in_polygon(polygon, num_points, seed):
    points = []
    minx, miny, maxx, maxy = polygon.bounds  # Get the bounding box of the polygon 
    while len(points) < num_points:  
        # Generate a random point within the bounding box
        random_point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        # Check if the point is inside the polygon
        if polygon.contains(random_point):
            points.append(random_point)
    return MultiPoint(points)

def get_clip_voronoi(boundary, n, seed):
    count = 0
    while True:
        points = random_points_in_polygon(boundary, n, seed)
        voronoi = list(shapely.voronoi_polygons(points,tolerance=0,extend_to=boundary).geoms)
        clipped_voronoi = [boundary.intersection(polygon) for polygon in voronoi]
        area = [polygon.area for polygon in clipped_voronoi]
        if max(area) / min(area) <2 or count > 10000:
            if all([isinstance(clipvoronoi, Polygon) for clipvoronoi in clipped_voronoi]):
                return clipped_voronoi
            else: return [boundary]

@enforce_bounds({'n': (1, 5), 'seed': (1,2**32)})
def main(UDS, n=3, seed=1):
    random.seed(int(seed))
    newPBs = []
    for boundary in  [shape(SA['geometry']) for SA in UDS['Phenotype']['StudyAreas']]:
        for subd_boundary in get_clip_voronoi(boundary,int(n), seed):
            newPBs.append({'geometry':{'type':'Polygon', 'coordinates':[list(subd_boundary.exterior.coords)]},'properties':{}})
    UDS['Phenotype']['ParcelBoundaries'] += newPBs
    UDS = UpdateID(UDS)
    UDS = UpdateParameters(UDS,{'SimpleVoronoi':{'n':n, 'seed':int(seed)}})
    return UDS