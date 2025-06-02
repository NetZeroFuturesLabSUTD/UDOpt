from PIL import Image, ImageDraw, ImageFont
import mahotas
import pickle
from shapely.geometry import Point, Polygon, LineString, shape
import numpy as np
import pandas as pd
import shapely

def compute_major_axis(polygon):
    # Ensure the input is a Shapely Polygon
    if not isinstance(polygon, Polygon):
        raise ValueError("Input must be a Shapely Polygon")

    # Get the coordinates of the polygon exterior
    x, y = polygon.exterior.xy

    # Compute the covariance matrix of the coordinates
    coordinates = np.array(list(zip(x, y)))
    covariance_matrix = np.cov(coordinates, rowvar=False)

    # Compute the eigenvectors and eigenvalues of the covariance matrix
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # Find the index of the maximum eigenvalue
    max_eigenvalue_index = np.argmax(eigenvalues)

    # Get the corresponding eigenvector
    major_axis_vector = eigenvectors[:, max_eigenvalue_index]

    return major_axis_vector

def angle_to_true_north(vector):
    # Define the true north vector (y-axis)
    true_north_vector = np.array([0, 1])

    # Normalize the input vector
    vector_normalized = vector / np.linalg.norm(vector)

    # Calculate the dot product between the vectors
    dot_product = np.dot(true_north_vector, vector_normalized)

    # Calculate the angle in radians
    angle_radians = np.arccos(np.clip(dot_product, -1.0, 1.0))

    # Convert the angle to degrees
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees

def GetMoments(image):
    imageArray = np.array(image)
    try:
        radius = 512
        zernike_moments = mahotas.features.zernike_moments(imageArray, radius)
    except:
        zernike_moments = [False]
    return zernike_moments

def GetImage(polygons,centroid,wireframe=False):
    image_size = (512,512)
    img = Image.new("RGB", image_size, "black")
    draw = ImageDraw.Draw(img)
    for polygon in polygons:
        if polygon.geom_type == 'MultiPolygon': # when a parcel has more than one polygon.
            polygon = Polygon(np.array(sorted([(p.area,p) for p in polygon])[-1][1].exterior.xy).transpose()) # return the largest polygon, which should be the exterior  one.
        translated_polygon = Polygon([(x - centroid.x + (image_size[0]/2), (image_size[1]/2) - y + centroid.y) for x, y, z in polygon.exterior.coords])
        polygon_coords = list(translated_polygon.exterior.coords)
        if wireframe:
            draw.polygon(polygon_coords,outline='white')
        else:
            draw.polygon(polygon_coords,fill='white')
    return img.convert('L')

def GetPolarRay(centroid, length, number):
            ray = LineString([centroid, (centroid.x, centroid.y + length)])
            angles = [i*360/number for i in range(number)]
            rays = [shapely.affinity.rotate(ray, angle, origin=centroid, use_radians=False) for angle in angles]
            return rays

def GetContextProperties(BFs, i, ray_length=255, ray_qty=20):

    bf_df = pd.DataFrame([{**BF['properties'], **{'geometry':shape(BF['geometry'])}} for BF in BFs])
    ref_df = bf_df.iloc[i]
    others_df = bf_df.drop(i)
    others_df['distance'] = [g.distance(ref_df.geometry) for g in others_df.geometry]
    nearby_others_df = others_df.loc[others_df['distance'] < ray_length].reset_index(drop=True)

    context = []
    rays = GetPolarRay(centroid=ref_df.geometry.centroid, length=ray_length, number=ray_qty)
    for ray in rays:
        distance_index = sorted([(ref_df.geometry.centroid.distance(polygon),index) for index,polygon in enumerate(nearby_others_df.geometry) if not ray.intersection(polygon.exterior).is_empty])
        if distance_index == []:
            context.append({'levels':0,'distance':ray_length})
        else:
            context.append(nearby_others_df.iloc[distance_index[0][1]].drop('geometry').to_dict())
    
    return context

def main(UDS):
    surrogate_model = pickle.load(open('Tasks\\Evaluate\\BuildingFootprints\\SM_AnnualEUI_Resi_Singapore.pickle', 'rb'))

    for i,BF in enumerate(UDS['Phenotype']['BuildingFootprints']):

        if BF['properties']['building'] == 'residential':

            geometry = shape(BF['geometry'])

            reference_shape = list(GetMoments(GetImage([geometry],geometry.centroid)))
            reference_levels = [BF['properties']['levels']]
            reference_angle = [angle_to_true_north(compute_major_axis(geometry))]
            reference_size = [geometry.area]

            context_properties = GetContextProperties(UDS['Phenotype']['BuildingFootprints'], i, ray_length=255, ray_qty=10) # SM trained on 255 and 10. do not change parameters.
            context_levels = [fetched_property['levels'] for fetched_property in context_properties]
            context_distance = [fetched_property['distance'] for fetched_property in context_properties]

            X = np.array([reference_shape + reference_levels + reference_angle + reference_size + context_distance + context_levels]) # shape MUST be (1,48)
            y_pred = surrogate_model.predict(X)[0]
            UDS['Phenotype']['BuildingFootprints'][i]['properties']['ApproxAnnualEUI'] = y_pred
    
    UDS['Genotype']['TotalApproxAnnualEUI'] = sum([BF['properties']['ApproxAnnualEUI'] for BF in UDS['Phenotype']['BuildingFootprints'] if 'ApproxAnnualEUI' in BF['properties']])
    return UDS