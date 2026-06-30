#### importation des modules #############################
import math 
import time,datetime
import logging
import os.path
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
import matplotlib.pyplot as plt
### information statut

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

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
    return maillage


#####
def survey_zone(ecart_rangee,orientation):
    zone_1 = Box(Vector3(0.1, 0.1, 0.001))
    rouge = Material(Color3(255,0, 0))
    geom0 = zone_1
    if orientation in ["sud","nord"]:  
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
    
    return[place_box0,place_box1,place_box2]

#####
"""
### 2 fonction maillage sol not necessary (optional) only use on modelling light sheltering on panel
### maillage panneau operationnel (version 2) = code fonctionnel 
def maillage_panneau(longueur_p, largeur_p, resolution_p=0.01,epais_p=0.001):
    maillage_panel = []
    
    # 1. Résolution
    step_x = resolution_p
    step_y = resolution_p

    # 2. Calcul du nombre de carreaux
    nb_carre_long = math.ceil(longueur_p / step_x)
    nb_carre_larg = math.ceil(largeur_p / step_y)

    # 3. Définition du pixel
    # On garde la Box standard (centrée par défaut)
    carreau_geom = Box(step_x/2, step_y/2, epais_p/2)

    # 4. Calcul du décalage global pour centrer le panneau sur (0,0)
    # On divise la dimension totale par 2
    offset_p_x = -(nb_carre_long * step_x) / 2
    offset_p_y = -(nb_carre_larg * step_y) / 2
    for i in range(nb_carre_long):
        for j in range(nb_carre_larg):
            # CALCUL CRUCIAL :
            # On part du bord (offset) + l'avancée (i * step)
            # + la DEMI-LARGEUR (step/2) pour que le CENTRE de la box soit au bon endroit.
            pos_x = offset_p_x + (i * step_x) + (step_x / 2)
            pos_y = offset_p_y + (j * step_y) + (step_y / 2)
            
            # On place le panneau (Translation)
            temp = Shape(Translated(Vector3(pos_x, pos_y, 0), carreau_geom))
            maillage_panel.append(temp)
    return maillage_panel

##creation des unites de panneaux with the first fonction (optional)
def creation_panel(longueur_p, largeur_p, resolution_p, nb_panel, nb_rangee, ecart_panel, ecart_rangee, hauteur_p, angle_p=0):
    # 1. On récupère les pixels centrés sur (0,0,0) via ta fonction de maillage
    panel_base = maillage_panneau(longueur_p, largeur_p, resolution_p)
    panel_mesh = []
    angle_radian = math.radians(angle_p)
    
    # Offsets pour centrer la GRILLE de panneaux dans la scène
    offset_x_global = -((nb_panel - 1) * ecart_panel) / 2
    offset_y_global = -((nb_rangee - 1) * ecart_rangee) / 2
    idx=1
    for i in range(nb_panel):
        for j in range(nb_rangee):
            pos_x_grille = offset_x_global + (i * ecart_panel)
            pos_y_grille = offset_y_global + (j * ecart_rangee)
            for pixel in panel_base:
                # A. Décalage de bord (Pivot) : On déplace le pixel pour que le bord du panneau soit à Y=0
                # On utilise .geometry car 'pixel' est une Shape
                pixel_au_bord = Translated(Vector3(0, -largeur_p/2, 0), pixel.geometry)
                # B. Inclinaison : Le pivot est maintenant sur le bord (Y=0)
                pixel_incline = AxisRotated(Vector3(1, 0, 0), angle_radian, pixel_au_bord)
                # C. Placement Final : On le monte à 'hauteur_p' et on le place dans la grille
                pixel_final = (Translated(Vector3(pos_x_grille, pos_y_grille, hauteur_p), pixel_incline))
                # On enregistre en tant que Shape pour Caribu
                panel_mesh.append(Shape(pixel_final))
    return panel_mesh

## ### creation des panneaux en parapluie (with mesh == optional ) slow down the calculation
def type_panneau_orient(params):
    ### params dicco
    orientation=params.get("orientation")
    type_panneau=params.get("type_panneau")
    longueur_p=params.get("longueur_p")
    largeur_p=params.get("largeur_p")
    resolution_p=params.get("resolution_p")
    nb_panel=params.get("nb_panel")
    nb_rangee=params.get("nb_rangee")
    ecart_panel=params.get("ecart_panel")
    ecart_rangee=params.get("ecart_rangee")
    hauteur_p=params.get("hauteur_p")
    angle_p=params.get("angle_p")
    
    # 1. On génère le premier versant (maillé et déjà placé en grille)
    panneau_init = creation_panel(longueur_p, largeur_p, resolution_p, nb_panel, nb_rangee, ecart_panel, ecart_rangee, hauteur_p, angle_p)
    mapping = {"sud": 0, "nord": math.pi, "est": math.pi/2, "ouest": -math.pi/2}
    angle_rot = mapping.get(orientation.lower(), 0)
    if type_panneau == "chapeau":
        # 2. On crée le versant opposé par rotation de 180° (PI)
        # On extrait .geometry de chaque pixel de panneau_init
        panneau_oppose = [Shape(AxisRotated(Vector3(0,0,1), math.pi, p.geometry)) for p in panneau_init]
        # 3. On fusionne les deux listes pour avoir le chapeau complet (tous les pixels)
        chapeau_complet = panneau_init + panneau_oppose
        # 4. On applique la rotation globale (Orientation Sud/Nord/...) à chaque pixel
        return [Shape(AxisRotated(Vector3(0,0,1), angle_rot, p.geometry)) for p in chapeau_complet]
    # Si ce n'est pas un chapeau, on oriente juste le premier versant
    return [Shape(AxisRotated(Vector3(0,0,1), angle_rot, p.geometry)) for p in panneau_init]
""" 

## 2 creation panel without maillage (to accelerate the computation use this method)
def type_panneau_orient_st(orientation,longueur_p,largeur_p,nb_panel,nb_rangee,ecart_panel,ecart_rangee,hauteur_p,angle_p):
    """
    largeur_p= distance in y coordonate (row line)
    longeur_p= distance in x coordonate (range line)
    orientation = where the panel facing (north,south, east and west)
    hauteur_p: the elevation when the panel is set plate (0)
    
    """
    #### creation unit panel inclinate
    angle_rad=angle_p
    ##
    panel_final = []
    panel_unit = Box(Vector3(longueur_p/2, largeur_p/2, 0.001))
    # panel_incl = AxisRotated(Vector3(1,0,0), angle_rad, panel_unit)
    # panel_base = Translated(Vector3(0,0,hauteur_p), panel_incl)
    
    
    panel_incl = Translated(Vector3(0,0,hauteur_p), panel_unit)
    panel_base = AxisRotated(Vector3(1,0,0), angle_rad, panel_incl)
    
    poteau_init=[Cylinder(radius=0.05,height=hauteur_p)]
    panel_final_shape = [panel_base]
    pot_final=[]
    
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



#### function solar tracking and antitracking
""""
    alpha_s = sunelevation angle
    beta_s = sun angle azimutal 
    alpha_p= panel angle azimutal
    beta_p = the optimum angle for solar or anti tracking
"""
### function between angle panel and solar position
# first one used to figure out the betap of antitracking
def fonction_A_betap(alpha_s,beta_s,beta_p,alpha_p=0):
  return np.cos(beta_p)*((np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)))

def fonction_B_beta_p(beta_s,beta_p):
  return np.sin(beta_p)*(np.sin(beta_s))

## important for solving the equation 
def fonction_X(alpha_s,beta_s,alpha_p=0):
    return np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)
def fonction_Y (beta_s):
    return np.sin(beta_s)
    

## fonctions derivée use to determine the angle beta_p solar tracking
def fonction_A_beta_p_prime(alpha_s,beta_s,beta_p,alpha_p=0):
    -np.sin(beta_p)*((np.sin(alpha_s)*np.sin(beta_s)*np.sin(alpha_p)+np.cos(alpha_s)*np.cos(beta_s)*np.cos(alpha_p)))
    
def fonction_B_beta_p_prime(beta_s,beta_p):
    return np.cos(beta_p)*(np.sin(beta_s))

#### programming as oop for solar tracking and antitracking
"""
for the solar tracking, the equation was derived and the angle beta was obtain when the 
equation i set to equal zero
the angle is between [-pi/2 and pi/2] pi/2 earlier in the morning and -pi/2 before the sun goes down

for the antitracking, we simply solve the main fonction to equal zero

"""
### function extraction data triangles
def extraction(triangle, groupe):
    tot = []
    for gliste in triangle:
        tot.append(gliste[0][0:2])
    df_groupe = pd.DataFrame(groupe, columns=['ID_Groupe'])
    df_coords = pd.DataFrame(tot, columns=['X', 'Y'])
    data = pd.concat([df_groupe, df_coords], axis=1)
    data_groupe=data.groupby("ID_Groupe").mean()
    return data_groupe

####
def scene_carbi_run_stracking(params_sol,params_panel,data_date):
    from openalea.plantgl.all import Scene
    from openalea.caribu.CaribuScene import CaribuScene
    log("upload parameters")
    orientation=params_panel.get("orientation")
    longueur_p=params_panel.get("longueur_p")
    largeur_p=params_panel.get("largeur_p")
    nb_panel=params_panel.get("nb_panel")
    nb_rangee=params_panel.get("nb_rangee")
    ecart_panel=params_panel.get("ecart_panel")
    ecart_rangee=params_panel.get("ecart_rangee")
    hauteur_p=params_panel.get("hauteur_p")
    ###### fonction solar tracking
    log("extracting data")
    data_ele_azim=coordinate_extraction(data_date)
    #scene_sol=maillage_sol_fonct(params_sol)
    zone_survey=survey_zone(ecart_rangee,orientation)
    scene_sol =Scene(zone_survey)
    scene_s=Scene(scene_sol)
    alpha_p=0
    doc=[]
    angle_calc=[]
    hours=[]
    scene_panneau=[]
    log("beginning itteration")
    t1=time.time()
    for ind, row in enumerate(tqdm(data_ele_azim.itertuples(), total=len(data_ele_azim))):
        light = [(1,(row.x,row.y,row.z))]
        alpha_s,beta_s= np.radians(row.apparent_elevation),np.radians(row.azimuth)
        B=fonction_Y(beta_s)
        A=fonction_X(alpha_s,beta_s,alpha_p=alpha_p)
        ## methods of caclulation of angle betap

        # method 2 use the pattern of method 1 but more rapidly
        beta_p=np.atan2(B,A) 
        # take into account de sun position 
        #if row.x > 0:   # morning
        #   beta_p = -abs(beta_p)
        #else:       # afternoon
        #  beta_p = abs(beta_p)
        angle_calc.append(beta_p)
        hours.append(row.hour)
        ### scene_modelling
        scene_panel,poteau=type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
        scene_pot=Scene(poteau)
        scene_p=Scene(scene_panel)
        scene_p.add(scene_s)
        scene_p.add(scene_pot)
        scene_panneau.append(scene_p)
        cs = CaribuScene(scene_p, light)
        _,aggregate=cs.run(simplify=True, infinite=False)
        dict_values=pd.DataFrame({"Triangles":list(aggregate["Ei"].keys()),"hours":[row.hour] * len(aggregate["Ei"]),"Ei":list(aggregate["Ei"].values())}).set_index("Triangles")
        doc.append(dict_values)
    log("extracting triangles and ids objects")
    tri,grp,_,_,_=cs.as_primitive()
    log("concatenation of all data")
    data_st=pd.concat(doc,axis=0,join="outer",ignore_index=False)
    coord_x_y= extraction(tri,grp)
    #data_final=pd.merge(coord_x_y,data_extract,left_index=True,right_index=True,how="left")
    data_degree=[np.degrees(angle)for angle in angle_calc]
    angle_st=pd.DataFrame({"hours":hours,"angle_radians":angle_calc,"angle_degrees":data_degree}).set_index("hours")
    t2=time.time()
    temp=t2-t1
    log(temp/10)
    log("simulation sucessefully")
    return data_st,scene_panneau[0],coord_x_y


## fonction for antitracking
def scene_carbi_run_anti_tracking(params_sol,params_panel,data_date):
    from openalea.plantgl.all import Scene
    from openalea.caribu.CaribuScene import CaribuScene
    log("data extraction ")
    orientation=params_panel.get("orientation")
    longueur_p=params_panel.get("longueur_p")
    largeur_p=params_panel.get("largeur_p")
    nb_panel=params_panel.get("nb_panel")
    nb_rangee=params_panel.get("nb_rangee")
    ecart_panel=params_panel.get("ecart_panel")
    ecart_rangee=params_panel.get("ecart_rangee")
    hauteur_p=params_panel.get("hauteur_p")
    ###### fonction solar tracking
    log("getting coordonate (x,y,z)")
    data_ele_azim=coordinate_extraction(data_date)
    #scene_sol=maillage_sol_fonct(params_sol)
    survey_spo=survey_zone(ecart_rangee,orientation)
    scene_sol=Scene(survey_spo)
    scene_s=Scene(scene_sol)
    alpha_p=0
    doc=[]
    angle_calc=[]
    hours=[]
    scene_paneau=[]
    t1=time.time()
    for ind, row in enumerate(tqdm(data_ele_azim.itertuples(), total=len(data_ele_azim))):
        light = [(1,(row.x,row.y,row.z))]
        alpha_s,beta_s=np.radians(row.apparent_elevation),np.radians(row.azimuth)
        #alpha_s,beta_s= math.radians(row["apparent_elevation"]),math.radians(row["azimuth"])
        B=fonction_Y(beta_s)
        A=fonction_X(alpha_s,beta_s,alpha_p=alpha_p)
        beta_p=np.atan2(-A,B)
        #if row.x > 0:   # morning
        #  beta_p = abs(beta_p)
        #else:       # afternoon
        #  beta_p = -abs(beta_p)
        #extraction angle
        angle_calc.append(beta_p)
        hours.append(row.hour)
        ### scene_modelling
        scene_panel,poteau=type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
        scene_pot=Scene(poteau)
        scene_p=Scene(scene_panel)
        scene_p.add(scene_s)
        scene_p.add(scene_pot)
        scene_paneau.append(scene_p)
        cs = CaribuScene(scene_p, light)
        _,aggregate=cs.run(simplify=True, infinite=False)
        dict_values=pd.DataFrame({"Triangles":list(aggregate["Ei"].keys()),"hours":[row.hour] * len(aggregate["Ei"]),"Ei":list(aggregate["Ei"].values())}).set_index("Triangles")
        doc.append(dict_values)
    log("extracting triangles and ids objects")
    tri,grp,_,_,_=cs.as_primitive()
    log("concatenation of all data")
    data_extract=pd.concat(doc,axis=0,join="outer",ignore_index=False)
    coord_x_y= extraction(tri,grp)
    #data_final=pd.merge(coord_x_y,data_extract,left_index=True,right_index=True,how="left")
    data_degree=[np.degrees(angle)for angle in angle_calc]
    angle_anti_tracking=pd.DataFrame({"hours":hours,"angle_radians":angle_calc,"angle_degrees":data_degree}).set_index("hours")
    t2=time.time()
    temp=t2-t1
    log(temp/10)
    log("simulation sucessefully")
    return data_extract,scene_paneau[0],coord_x_y

    #data_coord=pd.concat([coord_x_y,data_final],axis=1,join="inner",ignore_index=False)
####### codingggg
data_met={
    "start":"2025-03-03",
    "end":"2025-03-04",
    "tz":"Europe/Paris",
    "latitude":47.23,
    "longitude":3.30,}
    # paramètres d'entrée du panneau
params_panel={
    "orientation":"est",
    "type_panneau":"normal",
    "longueur_p":1.7,
    "largeur_p":1.5,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":2,
    "ecart_rangee":2,
    "hauteur_p":3,
    "angle_p":30}
    ### paramètres d'entrée du sol
params_sol={
        "resol":0.1,
        "longueur":1,
        "largeur":2,
        "ep":0.001}
    

### ############################################# for plotting 
def extraction_plotting_inter(data,nb_division):
    data_groupe=data.groupby("Triangles")
    data_final=[]
    for i in range (nb_division):
        data_final.append(data_groupe.get_group(i))
    return(data_final)
#####################################################


   
        



