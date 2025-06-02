import math, json, os
import numpy as np
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, LineString, shape
from PIL import Image

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MplPolygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.colors as colors

from Utilities.Utilities import *

def stitch_images_into_grid(images, max_images_per_row=4):
    # Ensure all images are the same size (resize if necessary)
    # Find the size of the first image
    width, height = images[0].size
    
    # Calculate the number of rows required
    num_images = len(images)
    num_rows = math.ceil(num_images / max_images_per_row)
    
    # Create a new blank image for the stitched result
    if len(images) < max_images_per_row:
        stitched_width = len(images) * width
    else:
        stitched_width = max_images_per_row * width
    stitched_height = num_rows * height
    stitched_image = Image.new('RGB', (stitched_width, stitched_height))

    # Paste images into the stitched image
    for i, img in enumerate(images):
        row = i // max_images_per_row
        col = i % max_images_per_row
        # Calculate the position to paste this image in the grid
        x_offset = col * width
        y_offset = row * height
        stitched_image.paste(img, (x_offset, y_offset))

    return stitched_image

"""
def PlotGrid(UDSs, titles=None, fig_size=(4,4), labelIndex=False):

    images = []

    for i in range(len(UDSs)):
        UDS = UDSs[i]

        # Define styles
        styledict = {
            'ParcelBoundaries':{
                "facecolor": "#BABD8D",
                "edgecolor": "#00770077",
                "linewidth": 1,
                "linestyle": "-",
                "zorder":0,
            },
            'BuildingFootprints':{
                "facecolor": "#11111144",
                "edgecolor": "black",
                "linewidth": 1,
                "linestyle": "-",
                "zorder":5,
            },
            'StudyAreas':{
                "facecolor": "None",
                "edgecolor": "#F8951D",
                "linewidth": 4,
                "linestyle": "--",
                "zorder":5,
            },
            'RoadCenterlines':{
                "color": "#7B6B2B",
                "linewidth": 1,
                "linestyle": "-",
                "zorder":5,
            }
        }

        fig,ax = plt.subplots(figsize=fig_size)

        
        for phenotype in UDS['Phenotype']:

            # Check that every phenotype has been defined before
            if phenotype not in styledict:
                print(f'define style for {phenotype}')
                return False
            
            # else plot it
            else:
                geometries = [shape(node['geometry']) for node in UDS['Phenotype'][phenotype]]
                gdf = gpd.GeoDataFrame({'geometry': geometries})
                if gdf.shape[0] != 0: gdf.plot(ax=ax, **styledict[phenotype])

                if labelIndex:

                    for g,geometry in enumerate(geometries):
                        try:
                            centroid = geometry.centroid
                            x,y = centroid.x, centroid.y
                            if 'color' in styledict[phenotype]:
                                anno_color = styledict[phenotype]['color']
                            elif 'edgecolor' in styledict[phenotype]:
                                anno_color = styledict[phenotype]['edgecolor']
                            ax.annotate(f"{g}", (x, y), ha='center', fontsize=8, color=anno_color, fontweight='black')
                        except:
                            pass
                    
                    if phenotype == 'RoadCenterlines':
                        G = geojson_lines_to_graph(UDS['Phenotype']['RoadCenterlines'])
                        for n,(x,y) in enumerate(list(G.nodes())):
                            ax.annotate(f"{n}", (x, y), ha='center', fontsize=6, color='black', fontweight='normal')
        
        try:
            ax.set_title(titles[i])
        except:
            ax.set_title(UDS['Metadata']['ID'])
        plt.close()
        canvas = FigureCanvas(fig)
        canvas.draw()
        image_array = np.frombuffer(canvas.buffer_rgba(), dtype='uint8')
        width, height = canvas.get_width_height()
        image_array = image_array.reshape(height, width, 4)
        image = Image.fromarray(image_array)
        images.append(image)
    
    return stitch_images_into_grid(images, max_images_per_row=4)
"""

def PlotUDSSimple(UDS, figSize=(8,8), labelIndex=False):

    # Define styles
    styledict = {
        'ParcelBoundaries':{
            "facecolor": "#BABD8D",
            "edgecolor": "#00770077",
            "linewidth": 1,
            "linestyle": "-",
            "zorder":0,
        },
        'BuildingFootprints':{
            "facecolor": "#11111144",
            "edgecolor": "black",
            "linewidth": 1,
            "linestyle": "-",
            "zorder":5,
        },
        'StudyAreas':{
            "facecolor": "None",
            "edgecolor": "#F8951D",
            "linewidth": 4,
            "linestyle": "--",
            "zorder":5,
        },
        'RoadCenterlines':{
            "color": "#7B6B2B",
            "linewidth": 1,
            "linestyle": "-",
            "zorder":5,
        }
    }

    fig,ax = plt.subplots(figsize=figSize)

    ID = UDS['Metadata']['ID']
    formatted_id = '\n'.join([ID.split('-')[0]] + ['-'.join(sublist) for sublist in [ID.split('-')[1:][i:i + 4] for i in range(0, len(ID.split('-')[1:]), 4)]])
    ax.set_title(formatted_id)
    
    for phenotype in UDS['Phenotype']:

        # Check that every phenotype has been defined before
        if phenotype not in styledict:
            print(f'define style for {phenotype}')
            return False
        
        # else plot it
        geometries = [shape(node['geometry']) for node in UDS['Phenotype'][phenotype]]
        gdf = gpd.GeoDataFrame({'geometry': geometries})
        if gdf.shape[0] != 0: gdf.plot(ax=ax, **styledict[phenotype])

        if labelIndex:
            # plot index for visual confirmation
            for g,geometry in enumerate(geometries):
                try:
                    centroid = geometry.centroid
                    x,y = centroid.x, centroid.y
                    if 'color' in styledict[phenotype]:
                        anno_color = styledict[phenotype]['color']
                    elif 'edgecolor' in styledict[phenotype]:
                        anno_color = styledict[phenotype]['edgecolor']
                    ax.annotate(f"{g}", (x, y), ha='center', fontsize=8, color=anno_color, fontweight='black')
                except:
                    pass
            
            # exception for roadcenterlines, to plot node index along with edge index
            if phenotype == 'RoadCenterlines':
                G = geojson_lines_to_graph(UDS['Phenotype']['RoadCenterlines'])
                for n,(x,y) in enumerate(list(G.nodes())):
                    ax.annotate(f"{n}", (x, y), ha='center', fontsize=6, color='black', fontweight='normal')
    
    plt.close()
    return fig

def PlotUDSMetric(UDS, figSize=(14,8), labelMetrics={}, legend=True):

    """
    Example of label metrics

    labelMetrics = {
    'BuildingFootprints':{'metric_name':'ApproxAnnualEUI', 'cmap':mpl.cm.cool},
    'RoadCenterlines':{'metric_name':'DensityReach', 'cmap':mpl.cm.viridis, 'min_max':(0,30)},
    }

    """


    fig, ax = plt.subplots(figsize=figSize)
    ID = UDS['Metadata']['ID']
    last_3_formatted_id = '\n'.join([ID.split('-')[0]] + ['-'.join(sublist) for sublist in [ID.split('-')[1:][i:i + 4] for i in range(0, len(ID.split('-')[1:]), 4)]][-3:])
    ax.set_title(last_3_formatted_id)

    for phenotype_name in sorted(UDS['Phenotype'])[::-1]:

        color_phenotypes = []
        plain_phenotypes = []

        if phenotype_name=='StudyAreas':
            gdf = gpd.GeoDataFrame({'geometry': [shape(SA['geometry']) for SA in UDS['Phenotype']['StudyAreas']]})
            if gdf.shape[0] != 0: gdf.plot(ax=ax, facecolor="None", edgecolor="#F8951D", linewidth= 4, linestyle= "--", zorder=10)

        # add to plain condition
        if not labelMetrics or phenotype_name not in labelMetrics or phenotype_name!='StudyAreas':
            for phenotype in UDS['Phenotype'][phenotype_name]:
                plain_phenotypes.append({'geometry':shape(phenotype['geometry'])})
        
        # colorful chart condition
        if phenotype_name in labelMetrics:
            metric_name = labelMetrics[phenotype_name]['metric_name']
            for phenotype in UDS['Phenotype'][phenotype_name]:
                if metric_name in phenotype['properties']:
                    color_phenotypes.append({'geometry':shape(phenotype['geometry']), 'metric':phenotype['properties'][metric_name]})
                else:
                    plain_phenotypes.append({'geometry':shape(phenotype['geometry'])})
        
        # plot with color if any
        if color_phenotypes!=[]:
            geoms = [p['geometry'] for p in color_phenotypes]
            values = [p['metric'] for p in color_phenotypes]
            if 'min_max' in labelMetrics[phenotype_name]:
                norm = colors.Normalize(vmin=labelMetrics[phenotype_name]['min_max'][0], vmax=labelMetrics[phenotype_name]['min_max'][1])
            else:
                norm = colors.Normalize(vmin=min(values), vmax=max(values))
            cmap = labelMetrics[phenotype_name]['cmap']
            colors_mapped = [cmap(norm(val)) for val in values]

            if geoms[0].geom_type == 'LineString':
                segments = [[[coords[0], coords[1]] for coords in list(geom.coords)] for geom in geoms]
                ax.add_collection(LineCollection(segments, alpha=0.8, colors=colors_mapped, linewidths=3))
            
            if geoms[0].geom_type == 'Polygon':
                patches = [MplPolygon(list(zip(geom.exterior.xy[0], geom.exterior.xy[1])), closed=True) for geom in geoms]
                ax.add_collection(PatchCollection(patches, alpha=0.8, facecolor=colors_mapped, edgecolor='black'))
            
            #plot legend
            if legend:
                plt.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, label=metric_name, fraction=0.0225)
        
        # else just plot in grey
        if plain_phenotypes!=[]:
            geoms = [p['geometry'] for p in plain_phenotypes]

            if geoms[0].geom_type == 'LineString':
                segments = [[[coords[0], coords[1]] for coords in list(geom.coords)] for geom in geoms]
                ax.add_collection(LineCollection(segments, alpha=0.8, colors='#88888888', linewidths=1,zorder=0))

            if geoms[0].geom_type == 'Polygon':
                patches = [MplPolygon(list(zip(geom.exterior.xy[0], geom.exterior.xy[1])), closed=True) for geom in geoms]
                ax.add_collection(PatchCollection(patches, alpha=0.8, facecolor='#88888888', edgecolor='black',zorder=0))       
    ax.autoscale()
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.close()
    return fig

def stitch_figures_into_grid(figs, max_images_per_row=4):

    images = []
    for fig in figs:
        canvas = FigureCanvas(fig)
        canvas.draw()
        image_array = np.frombuffer(canvas.buffer_rgba(), dtype='uint8')
        width, height = canvas.get_width_height()
        image_array = image_array.reshape(height, width, 4)
        image = Image.fromarray(image_array)
        images.append(image)

    # Get img size denomination
    img_sizes = np.array([img.size for img in images]).transpose()
    # Find the size of the first image
    width, height = max(img_sizes[0]), max(img_sizes[1])
    
    # Calculate the number of rows required
    num_images = len(images)
    num_rows = math.ceil(num_images / max_images_per_row)
    
    # Create a new blank image for the stitched result
    if len(images) < max_images_per_row:
        stitched_width = len(images) * width
    else:
        stitched_width = max_images_per_row * width
    stitched_height = num_rows * height
    stitched_image = Image.new('RGB', (stitched_width, stitched_height))

    # Paste images into the stitched image
    for i, img in enumerate(images):
        row = i // max_images_per_row
        col = i % max_images_per_row
        # Calculate the position to paste this image in the grid
        x_offset = col * width
        y_offset = row * height
        stitched_image.paste(img, (x_offset, y_offset))

    return stitched_image


# ----------------------------------------------------------------------------------------------------- #

def ExtractChain(nested_list):
    ans = {}
    for chain in nested_list:
        if chain != []:
            if chain[0] not in ans: ans[chain[0]] = []
            ans[chain[0]].append(chain[1:])
    
    for key,value in ans.items():
        if value != [[]] or []:
            ans[key] = ExtractChain(value)
    return ans

def ExtractEdges(nested_dict, parent_key=None, edges=None):
    if edges is None:
        edges = []  # Initialize edges list

    for key, value in nested_dict.items():
        if parent_key is not None:
            edges.append((parent_key, key))  # Add edge from parent to current key
        
        if isinstance(value, dict):  # If the value is a dictionary, go deeper
            ExtractEdges(value, key, edges)
    
    return edges

def rename_keys_with_suffix(nested_dict, counts=None):
    if counts is None:
        counts = {}  # Dictionary to keep track of counts for each key

    new_dict = {}

    for key, value in nested_dict.items():
        # Update the count for the current key
        if key not in counts:
            counts[key] = 1
        else:
            counts[key] += 1
        
        # Rename the key with the count suffix
        new_key = f"{key}-{counts[key]}"

        # Recursively rename the keys in the nested dictionary
        if isinstance(value, dict):
            new_dict[new_key] = rename_keys_with_suffix(value, counts)
        else:
            new_dict[new_key] = value

    return new_dict

# Define a recursive layout function to arrange nodes as a tree
def hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None, parsed=[]):
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)
    children = list(G.neighbors(root))
    if not isinstance(G, nx.DiGraph) and parent is not None:
        children.remove(parent)
    if len(children) != 0:
        dx = width / len(children)
        nextx = xcenter - width/2 - dx/2
        for child in children:
            nextx += dx
            pos = hierarchy_pos(G, child, width=dx, vert_gap=vert_gap, vert_loc=vert_loc-vert_gap, xcenter=nextx, pos=pos, parent=root, parsed=parsed)
      
    return pos

# Evenly space positions
def EvenlySpacedPosition(pos, ndec = 9):
    XValues = np.array(list(pos.values())).transpose()[0]
    XValues = [round(v,ndec) for v in XValues]
    sortedX = sorted(pd.unique(XValues))
    indexList = [sortedX.index(v) for v in sortedX]

    for key,value in pos.items():
        pos[key] = (sortedX.index(round(value[0],ndec)),value[1])
    return pos
    
def PlotUAG(UDSs, font_size=4):

    # Extract ids as data to plot
    data = [UDS['Metadata']['ID'].split('-')for UDS in UDSs]

    # turn nested list into branching nested dictionary
    chains = ExtractChain(data)

    # rename revisited nodes on different chains with suffix
    #chains = rename_keys_with_suffix(chains)

    # extract all edges
    edges = ExtractEdges(chains)

    # Create a directed graph
    G = nx.DiGraph()

    # Add edges to represent the tree structure (root -> children)
    G.add_edges_from(edges)

    # Generate the layout
    pos = hierarchy_pos(G, root=list(chains.keys())[0], width=0.5, vert_gap=1, vert_loc=0, xcenter=0.5)
    pos = EvenlySpacedPosition(pos)

    # Manual edit position 1
    pos[list(pos.keys())[0]] = (int(np.array(list(pos.values())).transpose()[0].mean()), 5)

    # Draw the graph
    fig, ax = plt.subplots(figsize=(4,4))
    nx.draw(G, pos, ax=ax, with_labels=True, node_color='#99000055', node_size=50, font_size=font_size, arrows=False)
    plt.tight_layout()
    plt.close()
    canvas = FigureCanvas(fig)
    canvas.draw()
    image_array = np.frombuffer(canvas.buffer_rgba(), dtype='uint8')
    width, height = canvas.get_width_height()
    image_array = image_array.reshape(height, width, 4)
    image = Image.fromarray(image_array)
    return image

# ----------------------------------------------------------------------------------------------------- #