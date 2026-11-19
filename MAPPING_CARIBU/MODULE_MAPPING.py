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
import math

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

# 2- FOR PANNEL MAPPING USING PLANTGL SCENE
def plotting_panels(scene):
    """_summary_
    Args:
        scene (_type_): _this function generate the coordonate x,y z for plotting panel on matplotlib_
    Returns:
        _type_: _description_
    """
    scene_f= get_panels(scene)
    list_rectangle=[]
    for element in scene_f:
        xmin=BoundingBox(element).getXMin()
        xmax=BoundingBox(element).getXMax()
        ymin=BoundingBox(element).getYMin()
        ymax=BoundingBox(element).getYMax() 
        rectangle=Rectangle((ymin,xmin),ymax-ymin,xmax-xmin,edgecolor='black',facecolor='none')
        list_rectangle.append(rectangle)
    return list_rectangle

# 3- FOR MAPPING 2 D EXTRACTION COORDINITATE 2 D (X AND Y)
def extraction_x_y(primitive_triangle):
    """_summary_
    Args:
        primitive_triangle (_type_): _from primitive geometry we extract (x1,x2,x3) and (y1,y2,y3)_
    Returns:
        _type_: _description_
    """
    coord_x=[]
    coord_y=[]
    for element in primitive_triangle:
        if element[0][2] == 0:
            x=(element[0][0],element[1][0],element[2][0])
            y=(element[0][1],element[1][1],element[2][1])
            coord_x.append(x)
            coord_y.append(y)
    return coord_x,coord_y


# 4- PLOTTING PANEL SCENE 
### plotting triangles 
def plotting_triangle(coord_x,coord_y):
    triangle=[]
    fig,axe=plt.subplots(figsize=(10,10))
    for i in range(len(coord_x)):
        add=tri.Triangulation(coord_x[i],coord_y[i])
        triangle.append(add)
        axe.triplot(add)
    axe.autoscale_view()
    axe.set_aspect('equal')
    return axe,triangle

#5- SOIL MESH PLOTTING

def soil_mesh_triangleV2(nb_rangee,nb_panel,ecart_rang,largeur_p,orientation="sud",resol=0.01):
    """_summary_
    Args:
        ecart_p (_type_): _panle ecart_
        ecart_rang (_type_): _rang distance_
        long_x_p (_type_): _panel length_
        larg_y_p (_type_): _panel width_
        orientation (str, optional): _description_. Defaults to "sud".
        resol (float, optional): _description_. Defaults to 0.01.
    Returns:
        _type_: _description_
    """
    resol_x=resol
    resol_y=resol
    points =[Vector3(-resol_x/2,-resol_y/2,0),Vector3(resol_x/2,-resol_y/2,0),Vector3(resol_x/2,resol_y/2,0),Vector3(-resol_x/2,resol_y/2,0)]
    sommet=[(0,1,2),(0,2,3)]
    triangle_unit=TriangleSet(points,sommet)

    if orientation.lower() in ["sud","nord"]:

        nb_pixel_x_unitaire=math.ceil((ecart_rang)/resol) # rang
        nb_pixel_y_unitaire=math.ceil((largeur_p)/resol) # distance between two row
        pos_x_depart=-(nb_pixel_x_unitaire*resol_x*nb_rangee)/2
        pos_y_depart=-(nb_pixel_y_unitaire*resol_y*nb_panel)/2
        nb_pixel_x=nb_pixel_x_unitaire*nb_rangee
        nb_pixel_y=nb_pixel_y_unitaire*nb_panel
        
        
    else :
        nb_pixel_x_unitaire=math.ceil((largeur_p)/resol) # rang
        nb_pixel_y_unitaire=math.ceil((ecart_rang)/resol) # distance between two row
        pos_x_depart=-(nb_pixel_x_unitaire*resol_x*nb_panel)/2
        pos_y_depart=-(nb_pixel_y_unitaire*resol_y*nb_rangee)/2
        nb_pixel_x=nb_pixel_x_unitaire*nb_panel
        nb_pixel_y=nb_pixel_y_unitaire*nb_rangee
        

    # if orientation =="sud":
    #     nb_pixel_x=math.ceil((ecart_rang + larg_y_p)/resol)
    #     nb_pixel_y=math.ceil((ecart_p + long_x_p)/resol)

    # else:
    #     nb_pixel_x=math.ceil((ecart_p + long_x_p)/resol)
    #     nb_pixel_y=math.ceil((ecart_rang + larg_y_p)/resol)
    # central mesh

    # pos_x_depart=-(nb_pixel_x-1)*resol_x/2
    # pos_y_depart=-(nb_pixel_y-1)*resol_y/2
    id_sol=0
    maillage=[]
    for i in range(int(nb_pixel_x)):
        for j in range(int(nb_pixel_y)):
            x_final = pos_x_depart + (resol_x * i)
            y_final = pos_y_depart + (resol_y * j)
            objet=Shape(Translated(Vector3(x_final,y_final,0),triangle_unit),id=id_sol)
            maillage.append(objet)
            id_sol+=1
    maillage_col=[Shape(maille.geometry, Material(Color3(0,0,0)), id=maille.id) for maille in maillage]
    return Scene(maillage_col)

def soil_mesh_trianglev1(ecart_p,ecart_rang,long_x_p,larg_y_p,orientation="sud",resol=0.01):
    """_summary_
    Args:
        ecart_p (_type_): _panle ecart_
        ecart_rang (_type_): _rang distance_
        long_x_p (_type_): _panel length_
        larg_y_p (_type_): _panel width_
        orientation (str, optional): _description_. Defaults to "sud".
        resol (float, optional): _description_. Defaults to 0.01.
    Returns:
        _type_: _description_
    """
    resol_x=resol
    resol_y=resol
    points =[Vector3(-resol_x/2,-resol_y/2,0),Vector3(resol_x/2,-resol_y/2,0),Vector3(resol_x/2,resol_y/2,0),Vector3(-resol_x/2,resol_y/2,0)]
    sommet=[(0,1,2),(0,2,3)]
    triangle_unit=TriangleSet(points,sommet)
    if orientation =="sud":
        nb_pixel_x=math.ceil((ecart_rang+larg_y_p)/resol)
        nb_pixel_y=math.ceil((ecart_p + long_x_p)/resol)

    else:
        nb_pixel_x=math.ceil((ecart_p + long_x_p)/resol)
        nb_pixel_y=math.ceil((ecart_rang+larg_y_p)/resol)
    # central mesh
    pos_x_depart=-(nb_pixel_x-1)*resol_x/2
    pos_y_depart=-(nb_pixel_y-1)*resol_y/2
    id_sol=0
    maillage=[]
    for i in range(nb_pixel_x):
        for j in range(nb_pixel_y):
            x_final = pos_x_depart + (resol_x * i)
            y_final = pos_y_depart + (resol_y * j)
            objet=Shape(Translated(Vector3(x_final,y_final,0),triangle_unit),id=id_sol)
            maillage.append(objet)
            id_sol+=1
    maillage_col=[Shape(maille.geometry, Material(Color3(255,255,255)), id=maille.id) for maille in maillage]
    return Scene(maillage_col)

#6- SOIL VALUES EXTRACTION FOR PLOTTING
def soils_values (dataframe_panda,id_panel=3000000):
    """_summary_
    Args:
        aggregated (_type_): _outputs caribu_
        id_panel (_type_): _id panels numbers = 30000_
    Returns:
        _type_: _description_ get those values for soil mesh 
        dict with id was kept in order to link with values
    """
    if dataframe_panda.get("Ei_total_sum") is not None:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_sum"]))
    else:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_mean"]))
    return {key:val for key, val in dico_value_calculare.items() if key != id_panel}

#6- SOIL COORDONATE EXTRACTION
def coordinate_x_y(agg, id_panel, primitive_tri, id_primitive):
    coord_x = []
    coord_y = []
    values_Ei = []
    for idx, val in zip(id_primitive, primitive_tri):

        if idx != int(id_panel):

            if idx in agg:
                x = (val[0][0], val[1][0], val[2][0])
                y = (val[0][1], val[1][1], val[2][1])
                coord_x.append(x)
                coord_y.append(y)
                values_Ei.append(agg[idx])
    return coord_x, coord_y, values_Ei



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


def mapping_2D (dataframe_panda,data_contr,primitive_tri,id_primitive,scene_save,name,id_panel=3000000):
    
    dict_values_calculated=soils_values(dataframe_panda,id_panel)
    coord_x,coord_y,values_calculated=coordinate_x_y(dict_values_calculated,primitive_tri, id_primitive,id_panel=3000000)
    mean_contr=np.round(data_contr["values_totale"].mean(),decimals=2)
    data_normalized = np.round((values_calculated/mean_contr),decimals=2)
    min_irradiance = np.round(np.min(values_calculated),decimals=2)
    mean_shade= np.round(1-(np.mean(values_calculated)/mean_contr),decimals=2)*100

    x_flat = np.array(coord_x).flatten()
    y_flat = np.array(coord_y).flatten()
    num_triangles = len(coord_x)
    triangles_indices = np.arange(num_triangles * 3).reshape((num_triangles, 3))
    z_flat = np.repeat(data_normalized, 3)
    
    val_min=0
    val_max=1
    level= np.linspace(val_min,val_max,15)
        
    triangulation_parfaite = tri.Triangulation(y_flat,x_flat, triangles=triangles_indices)
    
    # FIGURE SIZE
    figure,axe=plt.subplots(figsize=(16, 22))

    contour = axe.tricontourf(triangulation_parfaite, z_flat, levels=level, vmin=val_min,vmax=val_max, cmap='jet')

    
    divider = make_axes_locatable(axe)
    cax = divider.append_axes("right",size="2%",pad=0.5)
        
    rectangle=plotting_panels(scene_save)
    for rect in rectangle:
            axe.add_patch(rect)
    axe.autoscale_view()
    axe.set_aspect('equal')
    cbar = figure.colorbar(contour, cax=cax,extend="max")
    cbar.set_label(f"Soil_irradiance normalized", rotation=270, labelpad=20)
    axe.set_xlabel("East-west")
    axe.set_ylabel("South-North")
    axe.set_title(f"Irradiance on soil for {name} (normalized)")
    axe.invert_xaxis()
    axe.text(
    0.02, 0.02,
    f"Control irradiance: {mean_contr}\n"
    f"Min irradiance: {min_irradiance}\n"
    f"Mean shading: {mean_shade}",
    transform=axe.transAxes,
    ha="left",
    va="bottom",
    bbox=dict(
        boxstyle="square",
        facecolor="white",
        edgecolor="black",
        linewidth=1.5
    ))
    plt.tight_layout()
                # axe.invert_yaxis()
    # plt.show()
    plt.savefig(f"MAPPING_CARIBU/GIF_MAPPING/{name}.png", dpi=800)
    
    plt.close()
    
    