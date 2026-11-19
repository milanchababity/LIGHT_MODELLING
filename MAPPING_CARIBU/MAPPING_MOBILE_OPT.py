from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import scene_consrtructor_contrl
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import copy

from matplotlib.patches import Rectangle
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo
from tqdm import tqdm

import pandas as pd 
import datetime
import multiprocessing
from mpl_toolkits.axes_grid1 import make_axes_locatable
from MAPPING_CARIBU.MODULE_TRACKING.solar_tracking_caribu import fonction_X,fonction_Y,type_panneau_orient_st
from MAPPING_CARIBU import MODULE_MAPPING
import os

# dict_panel_st ={
#     "orientation":"sud",
#     "longueur_p":3.54,
#     "largeur_p":4.03,
#     "resolution_p":0.4,
#     "nb_panel":4,
#     "nb_rangee":4,
#     "ecart_panel":3.54,
#     "ecart_rangee":9.5,
#     "hauteur_p":3.7,
#     "angle_p":30,
#     "type_panneau":"normal",
#     "st": True}


# panel,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel_st)
# soil=MODULE_MAPPING.soil_mesh_triangleV2(4,4,9.5,3.54,resol=0.1)
# scene=Scene(panel + soil)
# Viewer.display(scene)

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)
### information statut



# MODULE TRACKER SIMULATION 

def SIMULATION_TRACKING(dict_panel,dict_soil,dict_date,name):
    # PANELS SET-UP 
    log("STEP 1/7 : UNPACKING INPUTS ")
    orientation=dict_panel.get("orientation")
    longueur_p=dict_panel.get("longueur_p")
    largeur_p=dict_panel.get("largeur_p")
    nb_panel=dict_panel.get("nb_panel")
    nb_rangee=dict_panel.get("nb_rangee")
    ecart_panel=dict_panel.get("ecart_panel")
    ecart_rangee=dict_panel.get("ecart_rangee")
    hauteur_p=dict_panel.get("hauteur_p")
    st=dict_panel.get("st")

    # SOILS MESHES INFORMATIONS
    nb_panel=dict_soil.get("nb_panel")
    nb_rangee=dict_soil.get("nb_rangee")
    largeur_panel=dict_soil.get("largeur_panel")
    orientation_sol=dict_soil.get("orientation")
    resolution=dict_soil.get("resolution")
    
    # SIMULATIONS ENVIRONNMENTS 
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    latitude=dict_date.get("latitude")
    longitude=dict_date.get('longitude')
    
    # SOIL MESH CREATION 
    def create_soil_scene():
        return MODULE_MAPPING.soil_mesh_triangleV2(nb_panel,nb_rangee,ecart_rangee,largeur_panel,orientation_sol,resolution)
    scene_soil=create_soil_scene()
    # scene_soil=MODULE_MAPPING.soil_mesh_triangleV2(nb_panel,nb_rangee,ecart_rangee,largeur_panel,orientation_sol,resolution)
    pattern_pv=(BoundingBox(scene_soil).getXMin(),BoundingBox(scene_soil).getYMin(),BoundingBox(scene_soil).getXMax(),BoundingBox(scene_soil).getYMax())
    
    
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    cumul_Rd_diffuse=data_meteo_rd["diffuse_radiation"].sum()
    
    # PANEL ORIENTATION EAST - WEST Azimuth 0 else Azimuth -90 or 90
    azimuth_angle ={
        "sud":0,
        "nord":180,
        "est":-90,
        "ouest":90
    }
    alpha_p=0
    
    data_diffus=[]
    data_direct=[]
    angle_calc=[]
    hours_diffus=[]
    hours_direct=[]
    scene_panneau=[]

    log("STEP 2/7 : SIMULATION DIRECT AND DIFUSE RADIATION BELOW THE PANEL")
    
    # 1 - SOLAR TRACKING 2- ANTI-TRACKING 3- HYBRIDE 
    
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))):
        
        sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=True)
        light_caribu_direct,_,_ =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            alpha_s,beta_s= solar_position_elev,solar_position_azim 
            
            B = fonction_Y(beta_s)
            A = fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)
                
            beta_p_final = np.clip(beta_p, -np.pi/4, np.pi/4) # to maintain rotation between (-pi/2 and pi/2)
            
            angle_calc.append(beta_p_final)
            hours_diffus.append(doy.decimal_hours)
            hours_direct.append(doy.decimal_hours)
            
            nouvelle_scene=Scene()
            scene_panel,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p_final)
            nouvelle_scene.add(scene_soil)
            nouvelle_scene.add(scene_panel)
            scene_panneau.append(nouvelle_scene)
            
            cs_diffus = CaribuScene(nouvelle_scene, light=sky,pattern=pattern_pv)
            _,aggregate_diffus=cs_diffus.run(simplify=True, infinite=True,direct=True)
            
            data_dif=pd.DataFrame({
                    "Triangles":aggregate_diffus["Ei"].keys(),
                    "horaire":[doy.decimal_hours]*len(aggregate_diffus["Ei"].keys()),
                    "values_Ei":aggregate_diffus["Ei"].values()
                }).set_index("Triangles")
            data_diffus.append(data_dif)
            
            cs_direct = CaribuScene(nouvelle_scene, light=[light_caribu_direct],pattern=pattern_pv)
            _,aggregate_direct=cs_direct.run(simplify=True, infinite=True,direct=True)
            data_caribu_direct=pd.DataFrame({
                    "Triangles":aggregate_direct["Ei"].keys(),
                    "horaire":[doy.date_time]*len(aggregate_direct["Ei"].keys()),
                    "values_Ei":aggregate_direct["Ei"].values()
                }).set_index("Triangles")
            
            data_direct.append(data_caribu_direct)
            
            triangles_,id_geom,_,_,_= cs_direct.as_primitive()
            nouvelle_scene.save(f"MAPPING_CARIBU/BGEOM/SCENE_Solar_tracking{str(doy.decimal_hours)}.bgeom") if st==True else nouvelle_scene.save(f"MAPPING_CARIBU/BGEOM/SCENE_Anti_tracking{str(doy.decimal_hours)}.bgeom") 

    inclinaison_beta=pd.DataFrame({"heure":hours_direct,
                                   "Angle_beta_radians":angle_calc,
                                   "Angle_beta_degre":[np.degrees(ele) for ele in angle_calc]}).to_excel("MAPPING_CARIBU/BGEOM/angle_calculated.xlsx")
    
    log("STEP 3/7: COMPUTING OUTPUTS SIMULATION ")
    # COMPILATION DIFFUSE RADIATION
    dataframe_diffus=pd.concat(data_diffus,axis=0,ignore_index=False,join="outer") 
    datacaribu_diffuse = (dataframe_diffus.groupby("Triangles")["values_Ei"].sum().to_frame(name="Values_Ei_finale"))
    
    # COMPILATION DIRECT RADIATION
    data_extract_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) 
    datacaribu_final_sum = (data_extract_direct.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei"))
    
    
    log("STEP 4/7: SIMULATION ON CONTROL SPOT DFFUSE RADIATION")
    # SIMULATION CONTROL ZONE 
    # 1 - DIFFUSE CONTROL SIMULATION
    sky_control=recup_meteo.modelize_sky(1)
    scene_control=scene_consrtructor_contrl(1)
    opt_conf_cont={"default_band":{scene_control[0].id:(0.06,0)}}
    pattern_contr=(BoundingBox(scene_control).getXMin(),BoundingBox(scene_control).getYMin(),BoundingBox(scene_control).getXMax(),BoundingBox(scene_control).getYMax())
    
    diffuse_control=CaribuScene(scene=scene_control,light=sky_control,opt=opt_conf_cont,pattern=pattern_contr)
    _,agg_control=diffuse_control.run(simplify=True,infinite=True,direct=True)
    dataframe_control_diffuse=pd.DataFrame({
                "Triangles":agg_control["Ei"].keys(),
                "values_Ei_diffus":agg_control["Ei"].values()
            }).set_index("Triangles")
    
    dataframe_control_diffuse["diffuse_radiation_value"]=dataframe_control_diffuse["values_Ei_diffus"]* cumul_Rd_diffuse
    
    log("STEP 5/7: SIMULATION ON CONTROL SPOT DIRECT RADIATION")
    
    # 2- DIRECT RADIATION SIMULATION
    data_control_direct=[]
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            control_direct=CaribuScene(scene_control,light=[light_caribu],opt=opt_conf_cont,pattern=pattern_contr)
            _,agg_cont_direct=control_direct.run(infinite=True, simplify=True, direct=True)
            dataframe_caribu_cont=pd.DataFrame({
                "Triangles":agg_cont_direct["Ei"].keys(),
                "horaire":[doy.date_time]*len(agg_cont_direct["Ei"].keys()),
                "values_Ei":agg_cont_direct["Ei"].values()
            }).set_index("Triangles")
            data_control_direct.append(dataframe_caribu_cont)
            
    data_direct_cont=pd.concat(data_control_direct,axis=0,join="outer",ignore_index=False)
    data_direct_cont_sum=(data_direct_cont.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei_control"))
    data_cont_final=pd.concat([data_direct_cont_sum,dataframe_control_diffuse],axis=1,join="outer",ignore_index=False)
    data_cont_final["values_totale"]=(data_cont_final["values_Ei_control"] + data_cont_final["diffuse_radiation_value"])/len(day_of_year_len)
    
    log("STEP 6/7: DATA MAPPING ")
    # CONCAT DIRECT AND DIFFUSE RADIATIONS
    data_caribu_direct_diffus=pd.concat([datacaribu_final_sum,datacaribu_diffuse],axis=1,join="outer",ignore_index=False)
    data_caribu_direct_diffus = data_caribu_direct_diffus.reset_index()
    data_caribu_direct_diffus["Ei_total_sum"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)

    # CREATE 3D SCENE FOR MAPPING 
    scene_demonstration,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=0)
    MODULE_MAPPING.mapping_2D (dataframe_panda=data_caribu_direct_diffus,data_contr=data_cont_final,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_demonstration,name=name)
    
    log("STEP 7/7: SIMULATION SUCCESSFULLY")
    data_caribu_direct_diffus.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\{name}.csv")
    return data_caribu_direct_diffus


def SIMULATION_TRACKING_HYBRID(dict_panel,dict_soil,dict_date,name):
    # PANELS SET-UP 
    log("STEP 1/7 : UNPACKING INPUTS ")
    orientation=dict_panel.get("orientation")
    longueur_p=dict_panel.get("longueur_p")
    largeur_p=dict_panel.get("largeur_p")
    nb_panel=dict_panel.get("nb_panel")
    nb_rangee=dict_panel.get("nb_rangee")
    ecart_panel=dict_panel.get("ecart_panel")
    ecart_rangee=dict_panel.get("ecart_rangee")
    hauteur_p=dict_panel.get("hauteur_p")
    st=dict_panel.get("st")

    # SOILS MESHES INFORMATIONS
    nb_panel=dict_soil.get("nb_panel")
    nb_rangee=dict_soil.get("nb_rangee")
    largeur_panel=dict_soil.get("largeur_panel")
    orientation_sol=dict_soil.get("orientation")
    resolution=dict_soil.get("resolution")
    
    # SIMULATIONS ENVIRONNMENTS 
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    latitude=dict_date.get("latitude")
    longitude=dict_date.get('longitude')
    
    # SOIL MESH CREATION 
    def create_soil_scene():
        return MODULE_MAPPING.soil_mesh_triangleV2(nb_panel,nb_rangee,ecart_rangee,largeur_panel,orientation_sol,resolution)
    scene_soil=create_soil_scene()
    # scene_soil=MODULE_MAPPING.soil_mesh_triangleV2(nb_panel,nb_rangee,ecart_rangee,largeur_panel,orientation_sol,resolution)
    pattern_pv=(BoundingBox(scene_soil).getXMin(),BoundingBox(scene_soil).getYMin(),BoundingBox(scene_soil).getXMax(),BoundingBox(scene_soil).getYMax())
    
    
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    cumul_Rd_diffuse=data_meteo_rd["diffuse_radiation"].sum()
    
    # PANEL ORIENTATION EAST - WEST Azimuth 0 else Azimuth -90 or 90
    azimuth_angle ={
        "sud":0,
        "nord":180,
        "est":-90,
        "ouest":90
    }
    alpha_p=0
    
    data_diffus=[]
    data_direct=[]
    angle_calc=[]
    hours_diffus=[]
    hours_direct=[]
    scene_panneau=[]

    log("STEP 2/7 : SIMULATION DIRECT AND DIFUSE RADIATION BELOW THE PANEL")
    
    # 1 - SOLAR TRACKING 2- ANTI-TRACKING 3- HYBRIDE 
    
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))):
        
        sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=True)
        light_caribu_direct,_,_ =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            alpha_s,beta_s= solar_position_elev,solar_position_azim 
            
            B = fonction_Y(beta_s)
            A = fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            
            # if int(doy.decimal_hours) in np.arange (5,11,1):
            #     beta_p=np.atan2(-A,B)
            # else:
            #     beta_p=np.atan2(B,A)
                
            if 5 <=int(doy.decimal_hours)<11:
                beta_p= beta_p=np.atan2(-A,B)
            else:
                beta_p=np.atan2(B,A)
                
                
            beta_p_final = np.clip(beta_p, -np.pi/4, np.pi/4) # to maintain rotation between (-pi/2 and pi/2)
            
            angle_calc.append(beta_p_final)
            hours_diffus.append(doy.decimal_hours)
            hours_direct.append(doy.decimal_hours)
            
            nouvelle_scene=Scene()
            scene_panel,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p_final)
            nouvelle_scene.add(scene_soil)
            nouvelle_scene.add(scene_panel)
            scene_panneau.append(nouvelle_scene)
            
            cs_diffus = CaribuScene(nouvelle_scene, light=sky,pattern=pattern_pv)
            _,aggregate_diffus=cs_diffus.run(simplify=True, infinite=True,direct=True)
            
            data_dif=pd.DataFrame({
                    "Triangles":aggregate_diffus["Ei"].keys(),
                    "horaire":[doy.decimal_hours]*len(aggregate_diffus["Ei"].keys()),
                    "values_Ei":aggregate_diffus["Ei"].values()
                }).set_index("Triangles")
            data_diffus.append(data_dif)
            
            cs_direct = CaribuScene(nouvelle_scene, light=[light_caribu_direct],pattern=pattern_pv)
            _,aggregate_direct=cs_direct.run(simplify=True, infinite=True,direct=True)
            data_caribu_direct=pd.DataFrame({
                    "Triangles":aggregate_direct["Ei"].keys(),
                    "horaire":[doy.date_time]*len(aggregate_direct["Ei"].keys()),
                    "values_Ei":aggregate_direct["Ei"].values()
                }).set_index("Triangles")
            
            data_direct.append(data_caribu_direct)
            
            triangles_,id_geom,_,_,_= cs_direct.as_primitive()
            nouvelle_scene.save(f"MAPPING_CARIBU/BGEOM/SCENE_Hybride{str(doy.decimal_hours)}.bgeom")
            
    inclinaison_beta=pd.DataFrame({"heure":hours_direct,
                                   "Angle_beta_radians":angle_calc,
                                   "Angle_beta_degre":[np.degrees(ele) for ele in angle_calc]}).to_excel("MAPPING_CARIBU/BGEOM/Angle_calculated_hybride.xlsx")
    
    log("STEP 3/7: COMPUTING OUTPUTS SIMULATION ")
    # COMPILATION DIFFUSE RADIATION
    dataframe_diffus=pd.concat(data_diffus,axis=0,ignore_index=False,join="outer") 
    datacaribu_diffuse = (dataframe_diffus.groupby("Triangles")["values_Ei"].sum().to_frame(name="Values_Ei_finale"))
    
    # COMPILATION DIRECT RADIATION
    data_extract_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) 
    datacaribu_final_sum = (data_extract_direct.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei"))
    
    
    log("STEP 4/7: SIMULATION ON CONTROL SPOT DFFUSE RADIATION")
    # SIMULATION CONTROL ZONE 
    # 1 - DIFFUSE CONTROL SIMULATION
    sky_control=recup_meteo.modelize_sky(1)
    scene_control=scene_consrtructor_contrl(1)
    opt_conf_cont={"default_band":{scene_control[0].id:(0.06,0)}}
    pattern_contr=(BoundingBox(scene_control).getXMin(),BoundingBox(scene_control).getYMin(),BoundingBox(scene_control).getXMax(),BoundingBox(scene_control).getYMax())
    
    diffuse_control=CaribuScene(scene=scene_control,light=sky_control,opt=opt_conf_cont,pattern=pattern_contr)
    _,agg_control=diffuse_control.run(simplify=True,infinite=True,direct=True)
    dataframe_control_diffuse=pd.DataFrame({
                "Triangles":agg_control["Ei"].keys(),
                "values_Ei_diffus":agg_control["Ei"].values()
            }).set_index("Triangles")
    
    dataframe_control_diffuse["diffuse_radiation_value"]=dataframe_control_diffuse["values_Ei_diffus"]* cumul_Rd_diffuse
    
    log("STEP 5/7: SIMULATION ON CONTROL SPOT DIRECT RADIATION")
    
    # 2- DIRECT RADIATION SIMULATION
    data_control_direct=[]
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            control_direct=CaribuScene(scene_control,light=[light_caribu],opt=opt_conf_cont,pattern=pattern_contr)
            _,agg_cont_direct=control_direct.run(infinite=True, simplify=True, direct=True)
            dataframe_caribu_cont=pd.DataFrame({
                "Triangles":agg_cont_direct["Ei"].keys(),
                "horaire":[doy.date_time]*len(agg_cont_direct["Ei"].keys()),
                "values_Ei":agg_cont_direct["Ei"].values()
            }).set_index("Triangles")
            data_control_direct.append(dataframe_caribu_cont)
            
    data_direct_cont=pd.concat(data_control_direct,axis=0,join="outer",ignore_index=False)
    data_direct_cont_sum=(data_direct_cont.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei_control"))
    data_cont_final=pd.concat([data_direct_cont_sum,dataframe_control_diffuse],axis=1,join="outer",ignore_index=False)
    data_cont_final["values_totale"]=(data_cont_final["values_Ei_control"] + data_cont_final["diffuse_radiation_value"])/len(day_of_year_len)
    
    log("STEP 6/7: DATA MAPPING ")
    # CONCAT DIRECT AND DIFFUSE RADIATIONS
    data_caribu_direct_diffus=pd.concat([datacaribu_final_sum,datacaribu_diffuse],axis=1,join="outer",ignore_index=False)
    data_caribu_direct_diffus = data_caribu_direct_diffus.reset_index()
    data_caribu_direct_diffus["Ei_total_sum"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)

    # CREATE 3D SCENE FOR MAPPING 
    scene_demonstration,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=0)
    MODULE_MAPPING.mapping_2D (dataframe_panda=data_caribu_direct_diffus,data_contr=data_cont_final,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_demonstration,name=name)
    
    log("STEP 7/7: SIMULATION SUCCESSFULLY")
    data_caribu_direct_diffus.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\{name}.csv")
    return data_caribu_direct_diffus


if __name__=="__main__":
    
    SOLAR_TRACKING ={
    "orientation":"est",
    "longueur_p":3.4,
    "largeur_p":3.52,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.4,
    "ecart_rangee":13,
    "hauteur_p":4,
    "angle_p":30,
    "st": True}
    
    ANTI_TRACKING ={
    "orientation":"est",
    "longueur_p":3.4,
    "largeur_p":3.52,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4, 
    "ecart_panel":3.4,
    "ecart_rangee":13,
    "hauteur_p":4,
    "angle_p":30,
    "st": False}
        
    SOIL_MESHES ={
        "nb_panel":4,
        "nb_rangee":4,
        "largeur_panel":3.52,
        "orientation":"est",
        "resolution":0.4}

    SIMULATION_1_HIVER={ # 21 DECEMBRE AU 19 MARS
    "debut":"2025-12-21",
    "fin":"2026-03-19",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 47.60, # Haute Saone
    "longitude": 6.8}
    
    SIMULATION_2_PRINTEMPS={ # 20 MARS AU 20 JUIN
    "debut":"2025-03-20",
    "fin":"2025-06-20",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 47.60, # Haute Saone
    "longitude": 6.8}
    
    SIMULATION_3_ETE={ # 21 JUIN AU 22 SEPTEMBRE
    "debut":"2025-06-21",
    "fin":"2025-09-22",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
    
    SIMULATION_3_AUTOMNE={ # 23 SEPTEMBRE AU 20 DECEMBRE
    "debut":"2025-09-23",
    "fin":"2025-12-20",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
    
    
    # process1 = multiprocessing.Process(
    #     target=SIMULATION_TRACKING,
    #     kwargs={"dict_panel":SOLAR_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_1_HIVER,"name":"SOLAR_TRACK_HIVER_2026"})
    # process2 = multiprocessing.Process(
    #     target=SIMULATION_TRACKING,
    #     kwargs={"dict_panel":ANTI_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_1_HIVER,"name":"ANTI_TRACK_HIVER_2026"})
    process3 = multiprocessing.Process(
        target=SIMULATION_TRACKING_HYBRID,
        kwargs={"dict_panel":ANTI_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_1_HIVER,"name":"HYBRID_TRACK_HIVER_2026"})
    
    process4 = multiprocessing.Process(
        target=SIMULATION_TRACKING,
        kwargs={"dict_panel":SOLAR_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_2_PRINTEMPS,"name":"SOLAR_TRACK_PRINT_2026"})
    process5 = multiprocessing.Process(
        target=SIMULATION_TRACKING,
        kwargs={"dict_panel":ANTI_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_2_PRINTEMPS,"name":"ANTI_TRACK_PRINT_2026"})
    process6 = multiprocessing.Process(
        target=SIMULATION_TRACKING_HYBRID,
        kwargs={"dict_panel":ANTI_TRACKING,"dict_soil":SOIL_MESHES,"dict_date":SIMULATION_2_PRINTEMPS,"name":"HYBRID_TRACK_PRINT_2026"})
    
    
    processes=[process3,process4,process5,process6] # process1,process2
    for proc in processes:
        proc.start()
    
    for proc in processes:
        proc.join()
    
    log('SIMULATION FINISHED SUCCESSEFULY')
        



