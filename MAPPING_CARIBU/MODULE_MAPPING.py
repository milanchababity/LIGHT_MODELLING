import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.tri as tri
import numpy as np
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandas as pd
import pickle

## getting uniquely the panels of the scene
def get_panels(scene):
    """_summary_
    Args:
        scene (_panel_): _for plotting in matplotlib_
    Returns:
        _scene_panel plangl_: _description_
    """
    panels=[]
    soil=[]
    for shape in scene:
        if shape.id == 3000000:
            panels.append(shape)
        else:
            soil.append(shape)
    return Scene(panels)


def coordinate_x_y(agg,primitive_tri, id_primitive,id_panel=3000000):
    """_summary_

    Args:
        agg (_dicct_): _outputs aggregated caribu_
        id_panel (_integer_): _3000000_
        primitive_tri (_list_): _outputs primitive triangles_
        id_primitive (_list_): _outputs primitive triangles_

    Returns:
        _list_: _description_
    """
    coord_x = []
    coord_y = []
    values_Ei = [] # to storage values id associate with one triangle
    for idx, val in zip(id_primitive, primitive_tri):        # filter on triangles meshes on soil
        if idx != int(id_panel): # cheking values 
            if idx in agg:
                x = (val[0][0], val[1][0], val[2][0])
                y = (val[0][1], val[1][1], val[2][1])
                coord_x.append(x)
                coord_y.append(y)
                values_Ei.append(agg[idx])
    return coord_x, coord_y, values_Ei


#### selected values froms soils mesh
def soils_values (dataframe_panda,id_panel=3000000):
    """_summary_

    Args:
        dataframe_panda (_dataframe pandas_): _data frame contain id traingles as index and values Ei calculated_
        id_panel (int, optional): _description_. Defaults to 3000000.

    Returns:
        _type_: _retransform id(key) and val Ei  to primitive aggregated caribu outputs in ordre to match each id and triangle with values_
    """

    if dataframe_panda.get("Ei_total_sum") is not None:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_sum"]))
    else:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_mean"]))
    return {key:val for key, val in dico_value_calculare.items() if key != id_panel}


def importation_primitive_id(id_pickled,triangle_pickled):
    data_=[id_pickled,triangle_pickled]
  
    for ix,element in enumerate(data_):
        if ix ==0:
            with open(id_pickled,"rb") as f:
                data_id=pickle.load(f)
        else:
            with open(triangle_pickled,"rb") as f:
                data_triangle=pickle.load(f)

    return data_id,data_triangle
                


def plotting_panels(scene_original):
    """_summary_
    Args:
        scene (_type_): _this function generate the coordonate x,y z for plotting panel on matplotlib_
    Returns:
        _type_: _description_
    """
    scene_f= get_panels(scene_original)
    list_rectangle=[]
    for element in scene_f:
        xmin=BoundingBox(element).getXMin()
        xmax=BoundingBox(element).getXMax()
        ymin=BoundingBox(element).getYMin()
        ymax=BoundingBox(element).getYMax() 
        rectangle=Rectangle((ymin,xmin),ymax-ymin,xmax-xmin,edgecolor='black',facecolor='none')
        list_rectangle.append(rectangle)
    return list_rectangle


def mapping_2D (dataframe_panda,primitive_tri,id_primitive,scene_save,name,id_panel=3000000):
    dict_values_calculated=soils_values(dataframe_panda,id_panel)
    coord_x,coord_y,values_calculated=coordinate_x_y(dict_values_calculated,primitive_tri, id_primitive,id_panel=3000000)

    x_flat = np.array(coord_x).flatten()
    y_flat = np.array(coord_y).flatten()
    num_triangles = len(coord_x)
    triangles_indices = np.arange(num_triangles * 3).reshape((num_triangles, 3))
    z_flat = np.repeat(values_calculated, 3)
    
    # # val_min= 0
    # # val_max=1

    # # val_min=0
    # # val_max=25
    # level= np.linspace(val_min,val_max,25)
        
    triangulation_parfaite = tri.Triangulation(y_flat,x_flat, triangles=triangles_indices)
    figure,axe=plt.subplots(figsize=(15, 15))
                    # triangle countourung
    # contour = axe.tricontourf(triangulation_parfaite, z_flat, levels=level, vmin=val_min,vmax=val_max, cmap='jet')
    contour = axe.tripcolor(triangulation_parfaite,facecolors=values_calculated,cmap="jet",shading="flat")
    
    divider = make_axes_locatable(axe)
    cax = divider.append_axes("right",size="2%",pad=0.5)
        
    rectangle=plotting_panels(scene_save)
    for rect in rectangle:
            axe.add_patch(rect)
    axe.autoscale_view()
    axe.set_aspect('equal')
    cbar = figure.colorbar(contour, cax=cax,extend="max")
    cbar.set_label("Soil_irradiance(Megajoule/m2/jour)")
    axe.set_xlabel("East-west")
    axe.set_ylabel("South-North")
    axe.set_title(f"Light shelttering_")
    axe.invert_xaxis()
    plt.tight_layout()
                # axe.invert_yaxis()
    plt.savefig(f"MAPPING_CARIBU/GIF_MAPPING/mapping_figure{name}.png", dpi=800)
    plt.close()
    
    