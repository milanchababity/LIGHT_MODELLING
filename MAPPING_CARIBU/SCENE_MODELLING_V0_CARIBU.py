#### importation des modules #############################
import math 
import time,datetime
import logging
import os.path
import numpy as np
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
import MODULE_SOLAR_METEO.SOLAR_POS_METEO as SOLAR_POS_METEO
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,ListedColormap
from MODULE_SOLAR_METEO.SOLAR_POS_METEO import coordinate_extraction
from MODULE_SOLAR_METEO.SOLAR_POS_METEO import fonction_cvt_light,calcul_azimut_elev,separate_date_hour,coordon_x_y_z,coordinate_extraction,z_caribu
from tqdm import tqdm
from functools import partial
import multiprocessing

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

### fonctions geometriques
## maillage version 2 operationelle 
"""
creation de maillage sol centre (0,0,0)
resolution=resolution du maillage 
longueur = longueur du sol
largeur= largeur du sol

"""
## maillage version 2 operationelle 
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
"""
def maillage_sol_centre(resol,longueur, largeur,ep=0.001):
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
""" 

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

##creation des unites de panneaux"
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

## ### creation des panneaux en parapluie et orientation exacte 
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

################################################# module annexe ##########################################
## fonction annexes d'importation de la position du soleil 
import math
import numpy as np
import pandas as pd
import pvlib as pv

#### get parameter azimuth and sun angulaire 
def convert_panda_datemine(data_test):
    ### extraction parameters
    start=data_test.get("start")
    end=data_test.get("end")
    tz=data_test.get("tz")
    ### creation datetime table with pandas
    times=pd.date_range(start,end,freq="15min",tz=tz)
    return times 

def calcul_azimut_elev(data_test):
    # extraction parameters
    latitude=data_test.get("latitude")
    longitude=data_test.get("longitude")
    start=data_test.get("start")
    end=data_test.get("end")
    tz=data_test.get("tz")
    ### datetime creation
    times = convert_panda_datemine(data_test)
    ### calcul solar_position
    data_angle=pv.solarposition.get_solarposition(times,latitude,longitude)
    return data_angle

##### create day and hour in panda dataframe
def separate_date_hour(dataframe):
    dataframe=dataframe.reset_index()
    dataframe.rename(columns={"index":"date_heure"},inplace=True)
    dataframe["date"]=dataframe["date_heure"].dt.date
    dataframe["hour"]=dataframe["date_heure"].dt.time
    dataframe["min"]=dataframe["date_heure"].dt.minute
    return dataframe

###calculation cartesians points
def coordon_x_y_z(dataframe):
    elevation=np.radians(dataframe["apparent_elevation"])
    azimuth=np.radians(dataframe["azimuth"])
    dataframe["x"] = np.cos(elevation) * np.sin(azimuth)
    dataframe["y"] = np.cos(elevation) * np.cos(azimuth)
    dataframe["z"] = np.sin(elevation)
    return dataframe
### computation of coordinates 
def coordinate_extraction(data_test):
    data_angle= calcul_azimut_elev(data_test)
    data_date_heure=separate_date_hour(data_angle)
    data_frame_xyz=coordon_x_y_z(data_date_heure)
    dataframe=data_frame_xyz[data_frame_xyz["z"]>0]
    datafinal=dataframe[["date_heure","hour","min","x","y","z"]]
    return datafinal
"""
def scene_illumination(objet_scene,data_date,plot=False):
    raw,aggr=[],[]
    scene_3D,values_3D =[],[]
    data_frame=pd.DataFrame()
    for index,row in tqdm(data_date.iterrows()):
        x,y,z=row["x"],row["y"],row["z"]
        light=[(1,(x,y,-z))]
        cs=CaribuScene(objet_scene,light)
        mes,cum=cs.run(simplify=True,infinite=False)
        agregate=list(cum["Ei"].values())
        pas_de_temps=row["date_heure"]
        data=data_frame.concat({pas_de_temps:agregate})
        raw.append(mes)
        aggr.append(cum)
        if plot:   
           plot_3d,value=cs.plot(mes["Ei"],0,1,0.2,display=False)
           scene_3D.append(plot_3d)
           values_3D.append(value)
    if plot:
        return raw,aggr,scene_3D,values_3D
    else:
        return raw,aggr
""" 

#### automatisation de caribu
###" fonction de lancement automatisé de CARIBU avec un objet scene creer "

#### fonction de subdivisiion pour le multiprocessing " à ameliorer "
def subdivide_date_measure(data, nb_processing=4):
    process_total = len(data) // nb_processing
    # On crée une liste de DataFrames
    chunks=[pd.DataFrame(data.iloc[:process_total]),
    pd.DataFrame(data.iloc[process_total:2*process_total]),
    pd.DataFrame(data.iloc[2*process_total:3*process_total]),
    pd.DataFrame(data.iloc[3*process_total:])]
    return chunks # Renvoie une liste de 4 DataFrames

# methode d'extraction des données en tableau pandas ""

### scene sans mutiprocess
"""
def scene_carbi_run(caribuscene,data_date):
    data_final =[]
    for index, row in tqdm(data_date.iterrows(), total=len(data_date)):
        x, y, z = row["x"], row["y"], row["z"]
        light = [(1, (x, y, -z))]
        cs = CaribuScene(caribuscene, light)
        _,aggregate=cs.run(simplify=True, infinite=False)
        triangles=list(aggregate["Ei"].keys())
        values=list(aggregate["Ei"].values())
        data=pd.DataFrame({"Triangles":triangles,row["hour"]:values})
        data.set_index("Triangles", inplace=True)
        data_final.append(data)
    data_totale=pd.concat(data_final,axis=1,join="outer",ignore_index=False)
    return data_totale
""" 
#### scene avec multiporcess works_v1
"""
def scene_carbi_run(params_sol,params_panel,data_date):
    from openalea.plantgl.all import Scene
    from openalea.caribu.CaribuScene import CaribuScene
    scene=Scene()
    sol=maillage_sol_fonct(params_sol)
    geom_panel=type_panneau_orient(params_panel)
    scene_panel=Scene(geom_panel)
    scene_sol=Scene(sol)
    scene.add(scene_sol)
    scene.add(scene_panel)
    doc=[]
    count=0
    for ind, row in tqdm(data_date.iterrows(), total=len(data_date)):
        x, y, z = row["x"], row["y"], row["z"]
        light = [(1, (x, y, -z))]
        cs = CaribuScene(scene, light)
        _,aggregate=cs.run(simplify=True, infinite=False)
        triangles=list(aggregate["Ei"].keys())
        values=list(aggregate["Ei"].values())
        dict_values=pd.DataFrame({"Triangles":triangles,row["hour"]:values})
        dict_values.set_index("Triangles",inplace=True)
        doc.append(dict_values)
    data_final=pd.concat(doc,axis=1,join="outer",ignore_index=False)
    return data_final
""" 
#### scene avec multiporcess works_v2 (optimisation de dataframe)
def scene_carbi_run(params_sol,params_panel,data_date):
    from openalea.plantgl.all import Scene
    from openalea.caribu.CaribuScene import CaribuScene
    scene=Scene()
    sol=maillage_sol_fonct(params_sol)
    geom_panel=type_panneau_orient(params_panel)
    scene_panel=Scene(geom_panel)
    scene_sol=Scene(sol)
    scene.add(scene_sol)
    scene.add(scene_panel)
    doc=[]
    count=0
    for ind, row in tqdm(data_date.iterrows(), total=len(data_date)):
        x, y, z = row["x"], row["y"], row["z"]
        light = [(1, (x, y, -z))]
        cs = CaribuScene(scene, light)
        _,aggregate=cs.run(simplify=True, infinite=False)
        dict_values=pd.DataFrame({"Triangles":list(aggregate["Ei"].keys()),row["hour"]:list(aggregate["Ei"].values())}).set_index("Triangles")
        doc.append(dict_values)
    data_final=pd.concat(doc,axis=1,join="outer",ignore_index=False)
    return data_final

 #####################################  
"""
def scene_illumination(objet_scene, data_date, plot=False):
    raw, aggr = [], []
    scene_3D, values_3D = [], []
    # Récupérer les IDs fixes depuis la première exécution
    premier_row = data_date.iloc[0]
    x, y, z = premier_row["x"], premier_row["y"], premier_row["z"]
    light = [(1, (x, y, -z))]
    cs = CaribuScene(objet_scene, light)
    _, cum = cs.run(simplify=True, infinite=False)
    id_shape = list(cum["Ei"].keys())  # IDs fixes
    # Liste pour stocker les lignes du DataFrame
    data_lignes = []
    for index, row in tqdm(data_date.iterrows(), total=len(data_date)):
        x, y, z = row["x"], row["y"], row["z"]
        light = [(1, (x, y, -z))]
        cs = CaribuScene(objet_scene, light)
        mes, cum = cs.run(simplify=True, infinite=False)
        agregate = list(cum["Ei"].values())
        # Ajouter une ligne avec date_heure + valeurs
        ligne = {"date_heure": row["date_heure"]}
        ligne.update({id_shape[i]: agregate[i] for i in range(len(id_shape))})
        data_lignes.append(ligne)
        raw.append(mes)
        aggr.append(cum)
        if plot:
            plot_3d, value = cs.plot(mes["Ei"], 0, 1, 0.2, display=False)
            scene_3D.append(plot_3d)
            values_3D.append(value)
    # Construire le DataFrame final
    data = pd.DataFrame(data_lignes)

    if plot:
        return raw, aggr, scene_3D, values_3D, data
    else:
        return raw, aggr, data
"""
"""
data_met={
    "start":"2025-05-06",
    "end":"2025-05-07",
    "tz":"Europe/Paris",
    "latitude":47.23,
    "longitude":3.30,
}
params_panel={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.7,
    "largeur_p":1.5,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":2,
    "ecart_rangee":4,
    "hauteur_p":3,
    "angle_p":30
}
params_sol={
    "resolution_p":0.1,
    "longueur_sol":6,
    "largeur_sol":10,
    "epaisseur_sol":0.01,
}

    log("scene création")
    panel =type_panneau_orient (params_panel)
    scene_panel=Scene(panel)
    sol=maillage_sol_fonct(params_sol)
    scene_sol=Scene(sol)
    scene=Scene()
    scene.add(scene_sol)
    scene.add(scene_panel)
    with multiprocessing.Pool(processes=4) as pool:
        resulat=pool.starmap(scene_carbi_run,[(params_sol,params_panel,chunk) for chunk in chunks])
"""
################################################################################################
#bloc d'execution principale
if __name__=="__main__":
    ##data inputs
    data_met={
    "start":"2025-03-06",
    "end":"2025-03-07",
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
    "ecart_panel":2.5,
    "ecart_rangee":4,
    "hauteur_p":3,
    "angle_p":30}
    ### paramètres d'entrée du sol
    params_sol={
        "resol":0.5,
        "longueur":1,
        "largeur":2,
        "ep":0.001
        }
    ### appel des fonctions
    t1=time.time()
    log("enregistrement de données paramétriques")
    data=coordinate_extraction(data_met)
    chunks=subdivide_date_measure(data, nb_processing=4)
    log("importation de période de simulation succès")
    log("lancement du multiprocessing ")
    with multiprocessing.Pool(processes=4) as pool:
        resultat=pool.starmap(scene_carbi_run,[(params_sol,params_panel,chunk) for chunk in chunks])
    log("computation data")
    data_final_2=pd.concat(resultat,axis=1,join="outer",ignore_index=False)
    log("simulation terminée")
    t2=time.time()
    duree_de_simul=int((t2-t1)*10)/10
    data_final_2.to_csv("data_simulate.csv",index= True)
    log(duree_de_simul)
    
