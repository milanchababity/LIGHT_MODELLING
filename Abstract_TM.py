# importation data
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.visualisation import py_canview
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.caribu.caributriangleset import CaribuTriangleSet
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
from pathlib import Path
from normal_panel import scene_modelling_normal
from MODULE_SOLAR_METEO.SOLAR_POS_METEO import coordinate_extraction
import pandas as pd 
import math
from time import time 
from pathlib import Path
from tqdm import tqdm
import datetime
from openalea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)



## fonction 
    # mixte fescue_alfalfa
bgeom_mixte_HD1=Scene(r"C:\Users\mbabity\Documents\PlantGL\RC_RS_plant_v1_rs.bgeom")
Viewer.display(bgeom_mixte_HD1)

#fonction separated scene 
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


def can_to_scene(str_file):
    run=CaribuScene(str_file)
    run_scene=run.scene
    scene_final=run_scene.generate_scene(None)
    return scene_final

def scaled_fonction(scene,factor=0.1):
    scale_list=[]
    for obj in scene:
        scaled_final=Shape(pgl.Scaled((factor,factor,factor),obj.geometry),id=obj.id)
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

def rotation_scene(scene_init):
    x=[]
    for shape in scene_init:
        ob=AxisRotated(Vector3(0,0,1),math.pi/2,shape.geometry)
        obj_col=Shape(ob,Material(Color3(34, 139, 34)),id=shape.id)
        x.append(obj_col)
    return Scene(x)


## conbinaison des deux fonction
def semis_alfalfa(scene_init, nb_rangee, ecart_rangee, nb_plant, ecart_plant,orientation):
    alfalfa_sowing = []
    if orientation in ["est","ouest"]:
        start_x = -((nb_rangee - 1) * ecart_rangee) / 2
        start_y = -((nb_plant - 1) * ecart_plant) / 2
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (r * ecart_rangee)
                current_y = start_y + (p * ecart_plant)
                for objet in scene_init:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=Shape(data_scaled,id=objet.id)
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
                    data_final=Shape(data_scaled,id=objet.id)
                    alfalfa_sowing.append(data_final)

    return Scene(alfalfa_sowing)


if __name__=="__main__":

    log("parameters loading")

    assollement={
    "nb_rangee":4,
    "nb_plant":4,
    "ecart_rangee":1,
    "ecart_plant":0.5,
    "orientation_panel":"sud"}

    params_panel_couvert_HD={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.99,
    "largeur_p":0.9,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    params_panel_couvert_LD={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.85, ### panel width
    "largeur_p":0.93,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    data_met={
    "start":"2025-05-21",
    "end":"2025-05-22",
    "tz":"Europe/Paris",
    "latitude":46.43,
    "longitude":3.30}
    # paramètres d'entrée du panneau
     
    log("scene importation")
    t1=time()
    log("get light")
    
    latitude= 46.43
    DOY=172
    heure=10
    s=Sun.Sun()
    s._set_pos_astro(DOY,heure,3.14/180*latitude)
    sun =  Gensun.Gensun()(1, DOY, heure, latitude)
    sun = GetLightsSun.GetLightsSun(sun)
    sun_str_split = sun.split(' ')
    x=round(float(sun_str_split[1]),2)
    y=round(float(sun_str_split[2]),2)
    z=round(float(sun_str_split[3]),2)
    light = [tuple((float(sun_str_split[0]),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
    
    log("scene uploading bgeom file")
    bgeom_mixte_HD1=Scene(r"C:\Users\mbabity\Documents\PlantGL\PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom")
    bgeom_mixte_HD2=Scene(r"C:\Users\mbabity\Documents\PlantGL\PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom")
    bgeom_mixte_LD1=Scene(r"C:\Users\mbabity\Documents\PlantGL\PAR_FSPM\Fescue-Alfalfa\Scene\LD1-asso-luz.bgeom")
    bgeom_mixte_LD2=Scene(r'C:\Users\mbabity\Documents\PlantGL\PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom')
    
    log("scene_id creation")
    _,_,scene_mixteHD1=fonction_separation_scene(bgeom_mixte_HD1)
    _,_,scene_mixteHD2=fonction_separation_scene(bgeom_mixte_HD2)
    _,_,scene_mixteLD1=fonction_separation_scene(bgeom_mixte_LD1)
    _,_,scene_mixteLD2=fonction_separation_scene(bgeom_mixte_LD2)
    
    log("Scaling scene ")
    scene_HD1_scaled= color (scene_mixteHD1,factor=0.01)
    scene_HD2_scaled=color (scene_mixteHD2,factor=0.01)
    scene_LD1_scaled=color (scene_mixteLD1,factor=0.01)
    scene_LD2_scaled=color (scene_mixteLD2,factor=0.01)
    
    log("scene panel_modelling")
    panel_HD,poteau=scene_modelling_normal.type_panneau_orient_univ(params_panel_couvert_HD)
    panel_LD,poteau=scene_modelling_normal.type_panneau_orient_univ(params_panel_couvert_LD)
   
    scene_panel_HD=Scene(panel_HD)
    scene_panel_LD=Scene(panel_LD)
    
    scene_HD1=Scene()
    scene_HD2=Scene()
    scene_LD1=Scene()
    scene_LD2=Scene()
    
    log("chargement panel scene")
    scene_HD1.add(scene_panel_HD)
    scene_HD2.add(scene_panel_HD)
    scene_LD1.add(scene_panel_LD)
    scene_LD2.add(scene_panel_HD)
    
    log("scene alfalfa duplication")
    
    hd1=semis_alfalfa(scene_HD1_scaled,8,0.31,3,0.30,"sud")
    log("hd2")
    hd2=semis_alfalfa(scene_HD2_scaled,8,0.31,3,0.30,"sud")
    log("hd3")
    ld1=semis_alfalfa(scene_LD1_scaled,2,1.06,3,0.30,"sud")
    log("hd4")
    ld2=semis_alfalfa(scene_LD2_scaled,2,1.06,3,0.30,"sud")
    
    log("final scene wwith panel")
    scene_HD1.add(hd1)
    scene_HD2.add(hd2)
    scene_LD1.add(ld1)
    scene_LD2.add(ld2)
    log("pattern")
    infinite_HD=(-0.45,-1.24,0.45,1.24)
    infinite_LD=(-0.465,-1.06,0.465,1.06)

    log("caribu simulation with panel")
    caribu_radiosity_HD1=CaribuScene(scene_HD1,light=light)#pattern=infinite_HD)
    log("caribu simulation hd1")
    caribu_radiosity_HD2=CaribuScene(scene_HD2,light=light)#,pattern=infinite_HD) 
    log("caribu simulation hd3")
    caribu_radiosity_LD1=CaribuScene(scene_LD1,light=light)#,pattern=infinite_LD) 
    log("caribu simulation hd4")
    caribu_radiosity_LD2=CaribuScene(scene_LD2,light=light)#,pattern=infinite_LD) 
    
    
    log("caribu simulation without panel")
    caribu_radiosity_HD11=CaribuScene(hd1,light=light)#,pattern=infinite_HD) #
    caribu_radiosity_HD22=CaribuScene(hd2,light=light)#,pattern=infinite_HD) # 
    caribu_radiosity_LD11=CaribuScene(ld1,light=light)#,pattern=infinite_LD) #
    caribu_radiosity_LD22=CaribuScene(ld2,light=light)#,pattern=infinite_LD) #
    
    path=str(Path.cwd())
    log("runing caribu with all scene vertical")
    log("hd1 simulation with panel ")
    
    _,aggHD1=caribu_radiosity_HD1.run(simplify=True,infinite=False)#,screen_size=12800)
    data_rawHD1=pd.DataFrame({"points":list(aggHD1["Ei"].keys()),"valuers_Ei":list(aggHD1["Ei"].values())})
    data_rawHD1.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawHD1_panel_vf_10H.csv")
    log("hd2 simulation with panel")
    _,aggHD2=caribu_radiosity_HD2.run(simplify=True,infinite=False)
    data_rawHD2=pd.DataFrame({"points":list(aggHD2["Ei"].keys()),"valuers_Ei":list(aggHD2["Ei"].values())})
    data_rawHD2.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawHD2_panel_vf_10H.csv")
    log("ld1 simulation wit panel")
    #scene_HD2,_=caribu_radiosity_HD2.plot(aggHD2["Ei"],0,1,0.1,False)
    #scene_HD2.save("scene_HD2_panel.bgeom")
    
    _,aggLD1=caribu_radiosity_LD1.run(simplify=True,infinite=False)#,screen_size=12800)
    data_rawLD1=pd.DataFrame({"points":list(aggLD1["Ei"].keys()),"valuers_Ei":list(aggLD1["Ei"].values())})
    data_rawLD1.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawLD1_panel_vf_screen_10H.csv")
    log("ld2 simulation with panel")
    _,aggLD2=caribu_radiosity_LD2.run(simplify=True,infinite=False)
    data_rawLD2=pd.DataFrame({"points":list(aggLD2["Ei"].keys()),"valuers_Ei":list(aggLD2["Ei"].values())})
    
    #data_rawLD2.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawLD2_panel_vf_10H.csv")
    #scene_LD2,_=caribu_radiosity_LD2.plot(aggLD2["Ei"],0,1,0.1,False)
    #scene_LD2.save("scene_LD2_panel.bgeom")
    
    log("hd1 simulation without panel")
    
    _,aggHD11=caribu_radiosity_HD11.run(simplify=True,infinite=False)
    data_rawHD11=pd.DataFrame({"points":list(aggHD11["Ei"].keys()),"valuers_Ei":list(aggHD11["Ei"].values())})
    data_rawHD11.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawHD11_plant_vf_unique.csv")
    log("hd2 simulation without panel")
    
    _,aggHD22=caribu_radiosity_HD22.run(simplify=True,infinite=False)
    data_rawHD22=pd.DataFrame({"points":list(aggHD22["Ei"].keys()),"valuers_Ei":list(aggHD22["Ei"].values())})
    data_rawHD22.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawHD22_plant_unique.csv")
    log("ld1 simulation without panel")
    #scene_HD22,_=caribu_radiosity_HD22.plot(aggHD22["Ei"],0,1,0.1,False)
    #scene_HD22.save("scene_HD22_plant.bgeom")
    
    _,aggLD11=caribu_radiosity_LD11.run(simplify=True,infinite=False)
    data_rawLD11=pd.DataFrame({"points":list(aggLD11["Ei"].keys()),"valuers_Ei":list(aggLD11["Ei"].values())})
    #data_rawLD11.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawLD11_plant_vf_10H.csv")
    log("ld2 simulation without panel")
    
    _,aggLD22=caribu_radiosity_LD22.run(simplify=True,infinite=False)
    data_rawLD22=pd.DataFrame({"points":list(aggLD22["Ei"].keys()),"valuers_Ei":list(aggLD22["Ei"].values())})
    data_rawLD22.to_csv(f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\data_rawLD22_plant_vf_10H.csv")
    

    # 1. Liste de tous vos DataFrames créés précédemment
    dfs = [
    data_rawHD1, data_rawHD2, data_rawLD1, data_rawLD2,
    data_rawHD11, data_rawHD22, data_rawLD11, data_rawLD22
    ]

# 2. Liste des noms correspondants pour les colonnes
    noms = [
    "HD1_panel", "HD2_panel", "LD1_panel", "LD2_panel",
    "HD1_plant", "HD2_plant", "LD1_plant", "LD2_plant"
    ]

    final_df = data_rawHD1.rename(columns={"valuers_Ei": noms[0]})

    for df, nom in zip(dfs[1:], noms[1:]):
    # On ne garde que la colonne 'points' et 'valuers_Ei' (renommée)
        temp_df = df[["points", "valuers_Ei"]].rename(columns={"valuers_Ei": nom})
    # Fusion sur la colonne 'points' (on utilise 'outer' pour ne perdre aucune donnée)
        final_df = pd.merge(final_df, temp_df, on="points", how="outer")

    # 5. Enregistrement en Excel
    output_path = f"{path}\\OUTPUTS_ABSTRACT\\TURBID_MEDIUM_LIGHT\\COMPILATION_SIMULATIONS.xlsx"
    final_df.to_excel(output_path, index=False)

    log(f"Compilation terminée ! Fichier sauvegardé sous : {output_path}")
    
    #scene_LD22,_=caribu_radiosity_LD22.plot(aggLD22["Ei"],0,1,0.1,False)
    #scene_LD22.save("scene_HD22_plant.bgeom")

    t2=time()
    elapsed = int((int((t2 - t1) * 10) / 10)/60)
    log(elapsed)
    





