import random, string, json, copy, datetime
import os
import importlib
from functools import wraps
import numpy as np
import networkx as nx
from shapely.geometry import Point, Polygon, LineString, shape

def WriteUDS(UDSolution, file_path):
    formatted_json_string = pretty_format_json(UDSolution)
    with open(file_path, 'w') as json_file:
        json_file.write(formatted_json_string)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super().default(obj)

def pretty_format_json(data, indent=4, max_depth=4):
    def custom_format(obj, current_depth=0):
        if max_depth is not None and current_depth >= max_depth:
            # Stop indenting further, print as a compact JSON string
            return json.dumps(obj, cls=NumpyEncoder)
        if isinstance(obj, dict):
            formatted = "{\n"
            # Sort keys from Z to A
            sorted_items = sorted(obj.items(), key=lambda x: x[0], reverse=False)
            for key, value in sorted_items:
                formatted += " " * (current_depth * indent) + f'"{key}": {custom_format(value, current_depth + 1)},\n'
            formatted = formatted.rstrip(",\n") + "\n" + " " * ((current_depth - 1) * indent) + "}"
            return formatted
        elif isinstance(obj, list):
            formatted = "[\n"
            for item in obj:
                formatted += " " * (current_depth * indent) + f"{custom_format(item, current_depth + 1)},\n"
            formatted = formatted.rstrip(",\n") + "\n" + " " * ((current_depth - 1) * indent) + "]"
            return formatted
        else:
            return json.dumps(obj, cls=NumpyEncoder)  # For primitive types

    return custom_format(data)

def GenerateID(N=5):
    random.seed(int(10000*datetime.datetime.now().timestamp()))
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(characters) for _ in range(N))
    return code

def UpdateID(UDS,N=5):
    UDS['Metadata']['ID'] += f'-{GenerateID(N)}'
    return UDS

def UpdateParameters(UDS,param_dict):
    UDS['Metadata']['parameters'].append(param_dict)
    return UDS


def ModulesDict(folder_path):

    modules = {}

    py_files = [f for f in os.listdir(folder_path) if f.endswith('.py') and f != '__init__.py']

    for py_file in py_files:

        module_name = py_file[:-3]

        format_folder_path = folder_path.replace('\\','.')

        module = importlib.import_module(f"{format_folder_path}.{module_name}")

        modules[module_name] = module
    
    return modules

def WithinBoundaryBuffer(check, reference, buffer=0.01):
    return reference.buffer(buffer).contains(check)

def RemovePhenotypeWithinBoundary(UDS, reference, always_include=['StudyArea']):
    ans = copy.deepcopy(UDS)
    phenotype_copy = {}
    include, exclude = 0,0
    for key,phenotypes in UDS['Phenotype'].items():

        if key in always_include:
            phenotype_copy[key] = phenotypes
        
        else:
            if key not in phenotype_copy: phenotype_copy[key] = []
            for phenotype in phenotypes:
                check = shape(phenotype['geometry'])
                if WithinBoundaryBuffer(check, reference):
                    include += 1
                else:
                    exclude += 1
                    phenotype_copy[key].append(phenotype)
    ans['Phenotype'] = phenotype_copy
    return ans

def IncludeUDSWithinBoundaries(UDS, boundaries):
    UDS_include = copy.deepcopy(UDS)
    UDS_include['Phenotype'] = {}
    UDS_exclude = copy.deepcopy(UDS)
    UDS_exclude['Phenotype'] = {}

    for key,phenotypes in UDS['Phenotype'].items():

        if key not in UDS_include['Phenotype']: 
            UDS_include['Phenotype'][key] = []
        if key not in UDS_exclude['Phenotype']: 
            UDS_exclude['Phenotype'][key] = []

        for phenotype in phenotypes:
            condition = [WithinBoundaryBuffer(shape(phenotype['geometry']), boundary) for boundary in boundaries]
            if any(condition):
                UDS_include['Phenotype'][key].append(phenotype)
            else:
                UDS_exclude['Phenotype'][key].append(phenotype)
    
    return UDS_include, UDS_exclude

def enforce_bounds(bounds):
    """
    A decorator to enforce parameter constraints including ranges, types, and allowed values.

    Args:
        bounds (dict): A dictionary where keys are parameter names and values are constraints.
            Constraints can be:
                - A tuple (min, max) for range checking.
                - A type (e.g., int, float) for type checking.
                - A list of allowed values for specific values.
    
    E.g:
        @enforce_bounds({
            'x': (0, 10),        # Range constraint
            'y': int,            # Type constraint
            'z': ['apple', 'banana', 'cherry']  # Specific values constraint
        })
        def example_function(x, y, z):
            return f"x: {x}, y: {y}, z: {z}"
        
        print(example_function._bounds)

    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function parameter names
            param_names = func.__code__.co_varnames
            # Validate positional arguments
            for i, value in enumerate(args):
                if param_names[i] in bounds:
                    constraint = bounds[param_names[i]]
                    _validate(value, constraint, param_names[i])
            # Validate keyword arguments
            for key, value in kwargs.items():
                if key in bounds:
                    constraint = bounds[key]
                    _validate(value, constraint, key)
            return func(*args, **kwargs)
        
        # Attach bounds to the function for introspection
        wrapper._bounds = bounds
        return wrapper
    return decorator

def _validate(value, constraint, param_name):
    """
    Validate a value against a constraint.

    Args:
        value: The value to validate.
        constraint: The constraint (tuple, type, or list) to validate against.
        param_name: The name of the parameter (for error messages).
    """
    if isinstance(constraint, tuple):  # Range constraint
        min_val, max_val = constraint
        if not (min_val <= value <= max_val):
            raise ValueError(f"'{param_name}' must be between {min_val} and {max_val}. Got {value}.")
    elif isinstance(constraint, type):  # Type constraint
        if not isinstance(value, constraint):
            raise TypeError(f"'{param_name}' must be of type {constraint.__name__}. Got {type(value).__name__}.")
    elif isinstance(constraint, list):  # Specific values constraint
        if value not in constraint:
            raise ValueError(f"'{param_name}' must be one of {constraint}. Got {value}.")
    else:
        raise ValueError(f"Invalid constraint for '{param_name}': {constraint}.")

def GetGFA(UDS):
    GFA = []
    siteArea = []
    if not UDS['Phenotype']['ParcelBoundaries']:
        print('No ParcelBoundaries')
        return None

    for PB in UDS['Phenotype']['ParcelBoundaries']:
        try:
            inside_UDS, outside_UDS = IncludeUDSWithinBoundaries(UDS, boundaries=[shape(PB['geometry'])])
            siteArea.append(shape(PB['geometry']).area)
            if len(inside_UDS['Phenotype']['BuildingFootprints']) == 0:
                GFA.append(np.nan)
            else:
                GFA.append(sum([shape(BF['geometry']).area * BF['properties']['levels'] for BF in inside_UDS['Phenotype']['BuildingFootprints']]))  
        except:
            pass

    return GFA

def geojson_lines_to_graph(geojson_features, weight_by_length=True):

    G = nx.Graph()

    for edge_index,feature in enumerate(geojson_features):
        geom = shape(feature['geometry'])

        if not isinstance(geom, LineString):
            continue  # Skip non-LineStrings

        coords = list(geom.coords)
        props = feature.get("properties", {})

        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            if len(p1)==3: p1 = p1[:2]
            if len(p2)==3: p2 = p2[:2]
            edge_data = props.copy()  # Optional: include GeoJSON properties
            edge_data['edge_index'] = edge_index

            if weight_by_length:
                length = LineString([p1, p2]).length
                edge_data["length"] = length

            G.add_edge(p1, p2, **edge_data)

    return G