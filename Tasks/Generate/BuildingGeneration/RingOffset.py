from Utilities.Utilities import *
import shapely
from shapely.geometry import LinearRing, LineString, Point, MultiLineString, MultiPolygon
import random
import math

def randomize_starting_position_ring(ring):
    """
    Randomly changes the starting position of a LinearRing.

    Args:
    - ring (LinearRing): The input Shapely LinearRing.

    Returns:
    - LinearRing: A new LinearRing with a randomly shifted starting position.
    """
    if not isinstance(ring, LinearRing):
        raise TypeError("Input must be a Shapely LinearRing.")
    
    # Get the coordinates of the ring (excluding the closing duplicate point)
    coords = list(ring.coords[:-1])
    
    # Randomly choose a new starting index
    idx = random.randint(0, len(coords) - 1)
    
    # Rearrange the coordinates to start from the new index
    new_coords = coords[idx:] + coords[:idx] + [coords[idx]]
    
    # Return a new LinearRing with the rearranged coordinates
    return LinearRing(new_coords)


def dashed_linear_ring(linear_ring, dash_min=60, dash_max=120, gap_min=20, gap_max=20):
    if not isinstance(linear_ring, LinearRing):
        raise TypeError("Input must be a Shapely LinearRing.")
    
    # Total length of the ring
    total_length = linear_ring.length
    
    # Pseudo-randomly generate dash-gap patterns
    patterns = []
    while sum(patterns) < total_length:
        dash = random.uniform(dash_min, dash_max)
        gap = random.uniform(gap_min, gap_max)
        patterns.extend([dash, gap])
    
    # Trim patterns to fit the total length
    patterns = patterns[:-1] if sum(patterns) > total_length else patterns
    
    # Generate the dashes
    dashes = []
    current_position = 0.0
    for i, length in enumerate(patterns):
        if current_position >= total_length:
            break
        
        next_position = min(current_position + length, total_length)
        if i % 2 == 0:  # Even indices are dashes
            dash = linear_ring.interpolate(current_position, normalized=False)
            next_dash = linear_ring.interpolate(next_position, normalized=False)
            dash_line = LineString([dash, next_dash])
            if dash_line.length >= dash_min:
                dashes.append(dash_line)
        
        current_position = next_position
    return dashes





@enforce_bounds({'offset':(20,60)})
def main(UDS, offset=45):
    SA_geometries =  [shape(SA['geometry']) for SA in UDS['Features']['StudyAreas']]
    SubUDS, _ = IncludeUDSWithinBoundaries(UDS, SA_geometries)


    for PB in SubUDS['Features']['ParcelBoundaries']:

        if 'GPR' in PB['properties'] and PB['properties']['GPR']!= None:

            boundary = shape(PB['geometry'])
            footprints = []
            rings = []

            for i in range(20,200,int(offset)):
                buffer_geometry = boundary.buffer(-i, cap_style=2, join_style=3)
                if shapely.is_empty(buffer_geometry): break
                if buffer_geometry.geom_type == 'Polygon': rings.append(buffer_geometry)
                if buffer_geometry.geom_type == 'MultiPolygon': 
                    for geom in buffer_geometry.geoms: rings.append(geom)

            for ring in rings:
                dash_ring = dashed_linear_ring(randomize_starting_position_ring(ring.exterior))
                multi_line = shapely.geometry.MultiLineString(dash_ring)
                merged_line = shapely.ops.linemerge(multi_line)
                if merged_line.geom_type == 'LineString': merged_line = MultiLineString([merged_line])

                for dash in merged_line.geoms:
                    footprint = dash.buffer(8, cap_style=2, join_style=3).exterior
                    if all(not footprint.intersects(shape) for shape in footprints + [boundary.exterior]):
                        footprints.append(Polygon(footprint))

            if len(footprints)!=0:
                levels = math.floor(float(PB['properties']['GPR']) * boundary.area / sum([footprint.area for footprint in footprints]))
                for footprint in footprints:
                    UDS['Features']['BuildingFootprints'].append(
                        {
                            'geometry':{'coordinates':[[[x,y,0] for x,y in np.array(footprint.exterior.coords.xy).transpose()]],'type':'Polygon'}, 
                            'properties':{'building':'residential','levels':levels,'height':levels*3}
                        }
                    )
    UDS = UpdateParameters(UDS,{'RingOffset':{
        'offset': offset, 
        }})
    UDS = UpdateID(UDS)
    return UDS