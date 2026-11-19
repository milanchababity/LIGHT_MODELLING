# importation data
from openalea.caribu.CaribuScene import CaribuScene
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
from pathlib import Path
import pandas as pd 
import math
from time import time 
from pathlib import Path
from tqdm import tqdm
import datetime
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
from lightvegemanager.src.lightvegemanager.VTK import *
from lightvegemanager.src.lightvegemanager.LVM import *
import os




def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

#fonction separated scene 
def separation_scene_AF(scene):
    luz=[]
    fet=[]
    scene_final=Scene()
    for shp in scene:
        if shp.geometry.getName()=="100000000000":
            shape_luz=Shape(shp.geometry,Material(Color3(34, 139, 34)),id=1000)
            luz.append(shape_luz)
        else:
            shape_fet=Shape(shp.geometry,Material(Color3(139, 0, 0)),id=2000)
            fet.append(shape_fet)
    scene_luz=Scene(luz)
    scene_fet=Scene(fet)
    scene_final.add(scene_luz)
    scene_final.add(scene_fet)
    return scene_luz,scene_fet,scene_final


def separation_scene_Autre_MIXTE(scene,id1=2,id2=1):
    scene_id1=[]
    scene_id2=[]
    scene_final=Scene()
    for ob in scene:
        id=str(ob.id)
        if id.startswith(str(id1)):
            shape_id1=Shape(ob.geometry,Material(Color3(34, 139, 34)),id=1000)
            scene_id1.append(shape_id1)
            
        elif id.startswith(str(id2)):
            
            shape_id2=Shape(ob.geometry,Material(Color3(139, 0, 0)),id=2000)
            scene_id2.append(shape_id2)
        else:
            shape_sol=Shape(ob.geometry,Material(Color3(0,0,0)),id=0)
    scene_mixt_1=Scene(scene_id1)
    scene_mixt_2=Scene(scene_id2)
    scene_final.add(scene_mixt_1)
    scene_final.add(scene_mixt_2)
    scene_sol=Scene([shape_sol])
    
    return scene_mixt_1,scene_mixt_2,scene_final,scene_sol


def centre_scene_scaled(scene_scaled,sol):
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
    xmax=BoundingBox(sol).getXMax()
    xmin=BoundingBox(sol).getXMin()
    ymax=BoundingBox(sol).getYMax()
    ymin=BoundingBox(sol).getYMin()
    
    dist_x=(xmax+xmin)/2
    dist_y=(ymax+ymin)/2
    tr_x=0-dist_x
    tr_y=0-dist_y
    shape_final=[]
    for shape in scene_scaled:
        shp=Shape(Translated(Vector3(tr_x,tr_y,0),shape.geometry),id=shape.id)
        shape_final.append(shp)
    scene_shape=Scene(shape_final)
    return scene_shape

def extraction_infinite(scene):
    xmax=BoundingBox(scene).getXMax()
    xmin=BoundingBox(scene).getXMin()
    ymax=BoundingBox(scene).getYMax()
    ymin=BoundingBox(scene).getYMin()
    zmax=BoundingBox(scene).getZMax()
    zmin=BoundingBox(scene).getZMin()
    
    return (xmin,ymin,xmax,ymax)



def can_to_scene(str_file):
    """_summary_
    this function can be use when the input file scene is canestra format

    Args:
        str_file (_type_): _description_

    Returns:
        _type_: _description_
        the return is a scene.bgeom 
    """
    run=CaribuScene(str_file)
    run_scene=run.scene
    scene_final=run_scene.generate_scene(None)
    return scene_final


def scaled_fonction(scene,factor=0.1):
    scale_list=[]
    for obj in scene:
        scaled_final= Shape(pgl.Scaled((factor,factor,factor),obj.geometry),id=obj.id)
        scale_list.append(scaled_final)
    return scale_list

# use this fonction to fixe shape geometry downscaling

def color(scene, factor=0.1):
    """_summary_
for downing scaled use this function to adapt scene on panel scale (m)
    Args:
        scene (_type_): _description_
        factor (float, optional): _description_. Defaults to 0.1.

    Returns:
        _type_: _description_
        the function return scene final 
    """
    scale_file = scaled_fonction(scene, factor)
    scale_f = []
    for obj in scale_file:
        new_shape = Shape(obj.geometry, Material(Color3(34, 139, 34)),id=obj.id) if obj.id== 1000 else Shape(obj.geometry,Material(Color3(139, 0, 0)),id=obj.id) 
        scale_f.append(new_shape) 
    return Scene(scale_f)

def rotation_scene(scene_init):
    x=[]
    for shape in scene_init:
        ob=AxisRotated(Vector3(0,0,1),math.pi/2,shape.geometry)
        obj_col=Shape(ob,Material(Color3(34, 139, 34)),id=shape.id)
        x.append(obj_col)
    return Scene(x)


## conbinaison des deux fonction
def semis_alfalfa(scene_init, nb_rangee, ecart_rangee, nb_plant, ecart_plant,orientation):
    
    """
   the puropose of this function is to duplicate all mock-ups to all surface scene 
   nb-rangee : number of range total according the motif calculated
   nb-plant : number of plant total in row 
   for using this function, make sure you have the correct replication dimension 
    
    """
    alfalfa_sowing = []
    if orientation in ["sud","nord"]:
        start_x = -((nb_rangee - 1) * ecart_rangee) / 2
        start_y = -((nb_plant - 1) * ecart_plant) / 2
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (r * ecart_rangee)
                current_y = start_y + (p * ecart_plant)
                for objet in scene_init:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=  Shape(data_scaled,Material(Color3(34, 139, 34)),id=objet.id) if objet.id == 1000 else Shape(data_scaled,Material(Color3(139, 0, 0)),id=objet.id)
                    alfalfa_sowing.append(data_final)
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
                    data_final=  Shape(data_scaled,Material(Color3(34, 139, 34)),id=objet.id) if objet.id == 1000 else Shape(data_scaled,Material(Color3(139, 0, 0)),id=objet.id)
                    alfalfa_sowing.append(data_final)               
    return Scene(alfalfa_sowing)


"""_Readme for identification id for each mixture_
    
    peaid=200  (function str.startswith())
    wheatid=100 (function str.startswith())
    Fescueid= 1 (function str.startswith())
    Cloverid= 2 (function str.startswith())
    Alfalfaid.geometry.getName=="100000000000" (function obj.geometry.getName(100000000000))
    Fescueid.geometry.getName()=="esle"
    
    ##" sepcific attention for scene duplication 
    nb range and nb plant depend the orientation 
    when the scene duplication is set for east for example, rangee is extent on x coordonate and when
    it set to south, the row extent follow y coordonate. the nb plant is the inverse
    
    
    
"""

# alfalfa_scene=Scene(r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom")
# _,_,sep_alfalfa=separation_scene_AF(alfalfa_scene)
# alafalfa_HD1=color(sep_alfalfa,0.01)
# Viewer.display()

# path="testa"
# vtk_scene=PlantGL_to_VTK(alfalfa_scene,path)
# S2v=

# print(vtk_scene)
# PlantGL_to_VTK(alfalfa_scene,path)
# print(os.listdir(r"C:\Users\mbabity\Documents"))












    



