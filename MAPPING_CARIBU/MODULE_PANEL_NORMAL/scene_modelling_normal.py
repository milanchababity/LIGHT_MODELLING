#### importation des modules #############################
import math 
import time,datetime
import logging
import os.path
from scipy.integrate import quad

### module caribu 
import numpy as np
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
## module recup solar position 
from MAPPING_CARIBU.MODULE_SOLAR_METEO.SOLAR_POS_METEO import coordinate_extraction

##
import pandas as pd
# module monitoring process
from tqdm import tqdm
from functools import partial
import multiprocessing
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun
### information statut

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

def solar_intensity(data_output):
    solar_i=[]
    for i in range(len(data_output)):
        intens= math.sin(math.pi*(i/len(data_output)))
        solar_i.append(intens)
    return solar_i

def solar(t, longeur=25):
    return math.sin(math.pi * (t / longeur))




    ###1 fonction maillage sol 
## maillage version 2 operationelle 
"""
creation de maillage sol centre (0,0,0)
resolution=resolution du maillage 
longueur = longueur du sol
largeur= largeur du sol
idx=identifiants des unités
all of this parameters are obtains on params dictionary

"""

def maillage_sol_fonct(params_sol):
    resol=params_sol.get("resol")
    longueur=params_sol.get("longueur")
    largeur=params_sol.get("largeur")
    ep=params_sol.get("ep")
    ##### 
    res_x=resol
    res_y=resol
    ep=ep
    nb_pixel_x=math.ceil(longueur/resol)
    nb_pixel_y=math.ceil(largeur/resol)
    careau_unit=Box(Vector3(res_x/2,res_y/2,ep))
    maillage=[]
    idx=0
    ### centralisation du maillage 
    pos_x_depart= -((nb_pixel_x-1)*res_x)/2
    pos_y_depart= -((nb_pixel_y-1)*res_y)/2
    ## maillage totaux
    for i in range(nb_pixel_x):
        for j in range(nb_pixel_y):
            x_final = pos_x_depart + (res_x * i)
            y_final = pos_y_depart + (res_y * j)
            objet=Shape(Translated(Vector3(x_final,y_final,0),careau_unit),id=idx)
            maillage.append(objet)
            idx+=1
    maillage_col=[Shape(maille.geometry, Material(Color3(240, 68, 68)), id=maille.id) for maille in maillage]
    return maillage_col


def survey_zone(ecart_rangee,orientation):
    zone_1 = Box(Vector3(0.1, 0.1, 0.001))
    rouge = Material(Color3(255,0, 0))
    geom0 = zone_1
    if orientation in ["est","ouest"]:  
        geom1 = Translated(Vector3(0, -ecart_rangee/4, 0), zone_1)
        geom2 = Translated(Vector3(0, -ecart_rangee/2, 0), zone_1)
        place_box0 = Shape(geom0,rouge,id=0)
        place_box1 = Shape(geom1,rouge,id=1)
        place_box2 = Shape(geom2,rouge,id=2)
    else :
        geom1 = Translated(Vector3(-ecart_rangee/4,0,0), zone_1)
        geom2 = Translated(Vector3(-ecart_rangee/2,0,0), zone_1)
        place_box0 = Shape(geom0,rouge,id=0)
        place_box1 = Shape(geom1,rouge,id=1)
        place_box2 = Shape(geom2,rouge,id=2)
    return Scene([place_box0,place_box1,place_box2])

# use this to mesh soil as triangle mesh
def fonction_triangle_mesh(x,y,ecart_rangee,orientation):
    points =[Vector3(-x/2,-y/2,0),Vector3(x/2,-y/2,0),Vector3(x/2,y/2,0),Vector3(-x/2,y/2,0)]
    sommet=[(0,1,2),(0,2,3)]
    mesh0=TriangleSet(points,sommet)
    rouge = Material(Color3(255,0, 0))
    if orientation in ["est","ouest"]:
        mesh1 = Translated(Vector3(0, -ecart_rangee/4, 0), mesh0)
        mesh2 = Translated(Vector3(0, -ecart_rangee/2, 0), mesh0)
        place_box0 = Shape(mesh0,rouge,id=0)
        place_box1 = Shape(mesh1,rouge,id=1)
        place_box2 = Shape(mesh2,rouge,id=2)
        
    else:
        mesh1 = Translated(Vector3(-ecart_rangee/4, 0, 0), mesh0)
        mesh2 = Translated(Vector3(-ecart_rangee/2,0 , 0), mesh0)
        place_box0 = Shape(mesh0,rouge,id=0)
        place_box1 = Shape(mesh1,rouge,id=1)
        place_box2 = Shape(mesh2,rouge,id=2)
    scene_final=Scene([place_box0,place_box1,place_box2])
    return scene_final
        

#### another method use to put a distance between two diveds

def type_panneau_orient_univ(params):
    orientation = params.get("orientation").lower()
    type_panneau = params.get("type_panneau")
    longueur_p = params.get("longueur_p")# length according axe row panel
    largeur_p = params.get("largeur_p")# length according axe between row
    nb_panel = params.get("nb_panel")
    nb_rangee = params.get("nb_rangee")
    ecart_panel = params.get("ecart_panel") # near longueur_p
    ecart_rangee = params.get("ecart_rangee")
    hauteur_haut_p = params.get("hauteur_haut_p")
    hauteur_bas_p = params.get("hauteur_bas_p")
    angle_p = params.get("angle_p")
    panel_opacity=params.get("panel_opacity")# semi transparent panel

    angle_rad = math.radians(angle_p)
    hauteur_p = (hauteur_haut_p + hauteur_bas_p) / 2
    panel_final = []
    panel_unit = Box(Vector3(longueur_p/2, largeur_p/2, 0.001))
    poteau_init=[Cylinder(radius=0.05,height=hauteur_p)]
    pot_final=[]
    
    if type_panneau == "normal":
        panel_base = AxisRotated(Vector3(1,0,0), angle_rad, panel_unit)
        panel_incl = Translated(Vector3(0,0,hauteur_p), panel_base)
        panel_final_shape = [panel_incl]
    else:
        panel_base = Translated(Vector3(0,-largeur_p/2,0), panel_unit)
        panel_inc = AxisRotated(Vector3(1,0,0), angle_rad, panel_base)

        panel_1 = Translated(Vector3(0,0,hauteur_p), panel_inc)
        panel_2 = AxisRotated(Vector3(0,0,1), math.pi, panel_1)
        panel_final_shape = [panel_1, panel_2]

    mapping = {
        "sud": -math.pi/2,
        "nord": math.pi/2,
        "est": 0,
        "ouest": math.pi}
    angle_orientation = mapping.get(orientation, 0)

    offset_y_global = -((nb_rangee - 1) * (ecart_rangee)) / 2
    offset_x_global = -((nb_panel - 1) * ( ecart_panel)) / 2
    id_p=3000000
    for rang in range(nb_rangee):
        for pan in range(nb_panel):
            y = offset_y_global + rang * (ecart_rangee)
            x = offset_x_global + pan * (ecart_panel)

            x_rot = x * math.cos(angle_orientation) - y * math.sin(angle_orientation)
            y_rot = x * math.sin(angle_orientation) + y * math.cos(angle_orientation)

            for p in panel_final_shape:
                p_rot = AxisRotated(Vector3(0,0,1), angle_orientation, p)
                p_trans = Translated(Vector3(x_rot, y_rot, 0), p_rot)
                panel_final.append(Shape(p_trans,id=id_p))
            for pot in poteau_init:
                pot_int=Translated(Vector3(x_rot,y_rot, 0),pot)
                pot_final.append(pot_int)
    panel_colore = [Shape(panel.geometry, Material(Color3(58,56,56)),id=panel.id)for panel in panel_final]
    poteau_colore=[Shape(pot_1,Material(Color3(58,56,56))) for pot_1 in pot_final]
    return Scene(panel_colore),poteau_colore
            


#### functions annexes 
#### lunch the process with for processors (use it on multiprocessing)
def subdivide_date_measure(data, nb_processing=4):
    process_total = len(data) // nb_processing
    # On crée une liste de DataFrames
    chunks=[pd.DataFrame(data.iloc[:process_total]),
    pd.DataFrame(data.iloc[process_total:2*process_total]),
    pd.DataFrame(data.iloc[2*process_total:3*process_total]),
    pd.DataFrame(data.iloc[3*process_total:])]
    return chunks # Renvoie une liste de 4 DataFrames

### function extraction x,y for plotting

def extraction(triangle, groupe):
    tot = []
    for gliste in triangle:
        tot.append(gliste[0][0:2])
    df_groupe = pd.DataFrame(groupe, columns=['Triangles'])
    df_coords = pd.DataFrame(tot, columns=['X', 'Y'])
    data = pd.concat([df_groupe, df_coords], axis=1)
    data_groupe=data.groupby("Triangles").mean()
    return data_groupe

#### scene avec multiporcess works_v2 (optimisation de dataframe) and extract the data as Dataframe

def scene_carbi_run(params_sol,params_panel,data_date):
    from openalea.plantgl.all import Scene
    from openalea.caribu.CaribuScene import CaribuScene
    panel_opacity=params_panel.get("panel_opacity")
    orientation =params_panel.get("orientation")
    ecart_rangee=params_panel.get("ecart_rangee")
    scene=Scene()
    #sol_geom=maillage_sol_fonct(params_sol)
    geom_panel,poteau=type_panneau_orient_univ(params_panel)
    #for pot in poteau:
    #    opt_config["default_band"][pot.id] = (0.06,0)
    #    scene.add(pot)
    direct=True if panel_opacity==1 else False # we ue raycasting when opacity==0 and mixed radiosity (reflectance and transmittance when opacity lower than 1)
    zone_spot = fonction_triangle_mesh(x=0.1,y=0.1,ecart_rangee=ecart_rangee,orientation=orientation)
    opt_config = {"default_band": {}}
    # for sol in sol_geom:
    #     opt_config["default_band"][sol.id] = (0.06, 0)
    #     scene.add(sol)
    for z in zone_spot:
        opt_config["default_band"][z.id] = (0.06, 0)
        scene.add(z)
    for p in geom_panel:
        opt_config["default_band"][p.id] = (0.06, 1 - panel_opacity)
        scene.add(p) 
    #scene_sol=Scene(sol_geom)
    #scene_poteau=Scene(poteau)
    scene_panel=Scene(geom_panel)
    scene_panel.add(zone_spot)
    #scene.add(scene_sol)
    #scene.add(scene_poteau)
    date_elev=coordinate_extraction(data_date)
    doc=[]
    longueur=len(date_elev)
    intense, error = quad(solar, 0, longueur)
    final_intensity = 22/ intense 
    solar_intensity_list=[prop*final_intensity for prop in solar_intensity(date_elev)]
    scene_ploter=[]
    for ind, row in enumerate(tqdm(date_elev.itertuples(), total=len(date_elev))):
        light = [(solar_intensity_list[ind],(row.x,row.y,row.z))]
        cs = CaribuScene(scene, opt=opt_config,light=light)
        raw,aggregate=cs.run(direct=direct,simplify=True, infinite=False) #direct=direct
        dict_values=pd.DataFrame({"Triangles":list(aggregate["Ei"].keys()),"hours":[row.hour] * len(aggregate["Ei"]),"Ei":list(aggregate["Ei"].values())}).set_index("Triangles")
        doc.append(dict_values)
        #scene_plt,values=cs.plot(raw["Ei"],0,1,0.2,display=False)
        #scene_ploter.append(scene_plt)
    tri,grp,_,_,_=cs.as_primitive() 
    coord_x_y= extraction(tri,grp)
    data_extract=pd.concat(doc,axis=0,join="outer",ignore_index=False)
    #data_total=pd.merge(coord_x_y,data_final,left_index=True,right_index=True,how="left")
    ## data extraction for plotting
    #ploty=data_final.sum(axis=1).to_frame(name="sum")
    #pd_final = pd.merge(coord_x_y, ploty, on="Triangles", how="inner") ## data plot
    return data_extract,scene,coord_x_y

#### programming as oop for solar tracking and antitracking

###" fonction maillage triangle set "





####### maillage sol triangle useful ####################################################
def maillage_sol_triangle(x, y, long_panel, larg_panel):
    triangle_base = fonction_triangle_mesh(x, y)
    dx = math.ceil(long_panel / x) 
    dy = math.ceil(larg_panel / y )
    long_reel = dx * x
    larg_reel = dy * y
    pos_x_depart = -long_reel / 2 + x / 2
    pos_y_depart = -larg_reel / 2 + y / 2
    maillage_total = []
    id=0
    for i in range(dx):
        for j in range(dy):
            x_final = pos_x_depart + i * x
            y_final = pos_y_depart + j * y
            objet = Shape(Translated(Vector3(x_final, y_final, 0), triangle_base),id=id)
            maillage_total.append(objet)
            id+=1

    return maillage_total


"""
maille=maillage_sol_triangle(0.2,0.2,2,3)
scene_tr=Scene(maille)


data_met={
    "start":"2025-05-03",
    "end":"2025-05-04",
    "tz":"Europe/Paris",
    "latitude":47.23,
    "longitude":3.30}
    # paramètres d'entrée du panneau

params_panel_norm_sud={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.54, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":2, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":8, # panel heigth max
    "hauteur_bas_p":7, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":70} # angle beta_p (tilt)

panel,poteau=type_panneau_orient_univ(params_panel_norm_sud)
scene_panel,scenepoteau=Scene(panel),Scene(poteau)
scene_panel.add(scenepoteau)
#Viewer.display(scene_panel) sud midi0.53 -0.00 -0.85 est 7.0  0.00  0.93 -0.37 ouest 18.0 -0.18 -0.96 -0.20
light=[(1,(0.0, 1, -0.001))]
cs=CaribuScene(scene_panel,light=light)
raw,_=cs.run(simplify=True, infinite=False)
scene,_=cs.plot(raw["Ei"],0,1,0.1,display=True)

maille=maillage_sol_triangle(0.2,0.2,10,4)
pattern=((-0, -0, 10,10))
scene_tr=Scene(maille)
scene=Scene(panel)
scene.add(scene_tr)
Viewer.display(panel)
cs1=CaribuScene(scene,pattern=pattern)
raw,val=cs1.run(direct=True,infinite=True,screen_size=768)

scene,agg=cs1.plot(raw["default_band"]["Ei"],0,1,0.2,display=True)

from recup_meteo import solar_position

###### def solar_position (dataframe,latitude)
data_pvlib=coordinate_extraction(data_met)
data_pvlib["heures_dt"]=pd.to_datetime(data_pvlib["hour"],format ="%H:%M:%S")
data_gensky=solar_position(data_pvlib,47.23)

import matplotlib.pyplot as plt
figsize,axes=plt.subplots(nrows=2,ncols=1)
#axes[0].plot(data_pvlib["heures_dt"],data_pvlib["x"])
axes[0].plot(data_pvlib["heures_dt"],data_pvlib["y"])
#axes[1].plot(data_gensky["periode"],data_gensky["x"])
axes[1].plot(data_gensky["periode"],data_gensky["y"])

plt.show()

print(data_gensky.head(40))
print(data_pvlib)
print
"""


