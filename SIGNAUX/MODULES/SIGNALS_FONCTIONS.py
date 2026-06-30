# importation data
from openalea.caribu.CaribuScene import CaribuScene
from openalea.plantgl.all import *
from pathlib import Path
import pandas as pd 
import math
from time import time 
import datetime
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal



def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)


#fonction separated scene to put the same id for each species
def fonction_separation_scene(scene):
    luz=[]
    fet=[]
    scene_final=Scene()
    for shp in scene:
        if shp.geometry.getName()=="100000000000":
            shape_luz=Shape(shp.geometry,id=0)
            luz.append(shape_luz)
        else:
            shape_fet=Shape(shp.geometry,id=1000)
            fet.append(shape_fet)
    scene_luz=Scene(luz)
    scene_fet=Scene(fet)
    scene_final.add(scene_luz)
    scene_final.add(scene_fet)
    return scene_luz,scene_fet,scene_final

def forcing_id_scene(scene):
    scene_final=[]
    id_init=0
    for shape in scene:
        ob=Shape(shape.geometry,id=id_init)
        scene_final.append(ob)
    scene_id_forced=Scene(scene_final)
    return scene_id_forced
        

# fonction separated scene to put different id for each triangle with no distinction between species
def fonction_separation_scene_rc_rs(scene):
    luz=[]
    fet=[]
    scene_final=Scene()
    id_luz=100000000
    id_fet=0
    for shp in scene:
        if shp.geometry.getName()=="100000000000":
            shape_luz=Shape(shp.geometry,id=id_luz)
            luz.append(shape_luz)
            id_luz+=1
        else:
            shape_fet=Shape(shp.geometry,id=id_fet)
            fet.append(shape_fet)
            id_fet+=1
    scene_luz=Scene(luz)
    scene_fet=Scene(fet)
    scene_final.add(scene_luz)
    scene_final.add(scene_fet)
    return scene_luz,scene_fet,scene_final


### transformed can file to scene plantgl
def can_to_scene(str_file):
    run=CaribuScene(str_file)
    run_scene=run.scene
    scene_final=run_scene.generate_scene(None)
    return scene_final

def scaled_fonction(scene,factor=0.1):
    scale_list=[]
    for obj in scene:
        scaled_final=Shape(Scaled((factor,factor,factor),obj.geometry),id=obj.id)
        scale_list.append(scaled_final)
    return scale_list

# use this fonction to fixe shape geometry downscaling
def color(scene, factor=0.1):
    scale_file = scaled_fonction(scene, factor)
    scale_f = []
    for obj in scale_file:
        new_shape = Shape(
            obj.geometry, 
            Material(Color3(34, 139, 34)), 
            id=obj.id
        )
        scale_f.append(new_shape) 
    return Scene(scale_f)

### for rotating scene on 90 degree
def rotation_scene(scene_init):
    x=[]
    for shape in scene_init:
        ob=AxisRotated(Vector3(0,0,1),math.pi/2,shape.geometry)
        obj_col=Shape(ob,Material(Color3(34, 139, 34)),id=shape.id)
        x.append(obj_col)
    return Scene(x)

## duplicate mock ups for all scene surface 
def semis_alfalfa_rc_rs(scene_init, nb_rangee, ecart_rangee, nb_plant, ecart_plant,orientation):
    alfalfa_sowing = []
    id_plant=0
    if orientation in ["sud","nord"]:
        start_x = -((nb_rangee - 1) * ecart_rangee) / 2
        start_y = -((nb_plant - 1) * ecart_plant) / 2
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (r * ecart_rangee)
                current_y = start_y + (p * ecart_plant)
                for objet in scene_init:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=Shape(data_scaled,id=id_plant)
                    alfalfa_sowing.append(data_final)
                    id_plant+=1

    else:
        scene_int=rotation_scene(scene_init)
        start_y = -((nb_rangee - 1) * ecart_rangee) / 2
        start_x = -((nb_plant - 1) * ecart_plant) / 2 
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (p * ecart_plant)
                current_y = start_y + (r * ecart_rangee)
                for objet in scene_int:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=Shape(data_scaled,id=id_plant)
                    alfalfa_sowing.append(data_final)
                    id_plant+=1
                    
    return Scene(alfalfa_sowing)

# definition optical proprieties for each material in the scene, with possibility to add panel proprieties if there is a panel in the scene
def get_optical_proprieties(scene, abs_1, trans_1, band_name_1, abs_2, trans_2, band_name_2, panel_scene):
    opt_config = {}

    opt_config[band_name_1] = {}
    opt_config[band_name_2] = {}

    for mat in scene:
        opt_config[band_name_1][mat.id] = (abs_1, trans_1)
        opt_config[band_name_2][mat.id] = (abs_2, trans_2)

    if panel_scene is not None:
        for po in panel_scene:
            opt_config[band_name_1][po.id] = (0.06, 0)
            opt_config[band_name_2][po.id] = (0.06, 0)


    return opt_config


def centre_scene_scaled(scene_scaled):
    """_summary_
We use this function for those scene which not center in (0,0)
before using this function, the scene input must to be scaled 
we can use this function for mixture Fescues-Clover and Wheat pea. they need a center function to center all scene in 0,0

    Args:
        scene_scaled (_type_): _description_
        scene scaled 

    Returns:
        _type_: _description_
        scene center 
    """
    xmax=BoundingBox(scene_scaled).getXMax()
    xmin=BoundingBox(scene_scaled).getXMin()
    ymax=BoundingBox(scene_scaled).getYMax()
    ymin=BoundingBox(scene_scaled).getYMin()
    
    dist_x=(xmax-xmin)/2
    dist_y=(ymax-ymin)/2
    tr_x=0-dist_x
    tr_y=0-dist_y
    shape_final=[]
    for shape in scene_scaled:
        shp=Shape(Translated(Vector3(tr_x,tr_y,0),shape.geometry),id=shape.id)
        shape_final.append(shp)
    scene_shape=Scene(shape_final)
    return scene_shape


    

