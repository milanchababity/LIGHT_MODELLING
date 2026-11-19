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

def simulation_panel_mobile(dict_panel,dict_soil,dict_date,name):
    # PANELS SET-UP 
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
        "est":0,
        "ouest":180,
        "sud":-90,
        "nord":90
    }
    alpha_p=azimuth_angle.get(orientation)
    
    data_diffus=[]
    data_direct=[]
    angle_calc=[]
    hours_diffus=[]
    hours_direct=[]
    scene_panneau=[]
    
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))):
        nouvelle_scene = create_soil_scene()
        sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=True)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            
            alpha_s,beta_s= solar_position_elev,solar_position_azim 
            B = fonction_Y(beta_s)
            A = fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)
                
            beta_p = np.clip(beta_p, -np.pi/2, np.pi/2) # to maintain rotation between (-pi/2 and pi/2)
            
            angle_calc.append(beta_p)
            hours_diffus.append(doy.decimal_hours)
            
            scene_panel,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            
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
        
    dataframe_diffus=pd.concat(data_diffus,axis=0,ignore_index=False,join="outer") 
     
    # datacaribu_diffuse = (dataframe_diffus.groupby("Triangles")["values_Ei"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))
    datacaribu_diffuse = (dataframe_diffus.groupby("Triangles")["values_Ei"].sum().to_frame(name="Values_Ei_finale"))
    
    for _,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu_direct,solar_position,angle_azimuth =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        ok=0
        
        if (light_caribu_direct is not None and solar_position is not None and angle_azimuth is not None):
            alpha_s,beta_s= solar_position,angle_azimuth  
             
            B=fonction_Y(beta_s)
            A=fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)
                
            beta_p = np.clip(beta_p, -np.pi/2, np.pi/2)

            angle_calc.append(beta_p)

            hours_direct.append(doy.decimal_hours)
            
            scene_panel_direct,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            
            scene_final=create_soil_scene()
            scene_final.add(scene_panel_direct)
            scene_panneau.append(scene_final)
            
            cs_direct = CaribuScene(scene_final, light=[light_caribu_direct],pattern=pattern_pv)
            _,aggregate_direct=cs_direct.run(simplify=True, infinite=True,direct=True)
            data_caribu_direct=pd.DataFrame({
                    "Triangles":aggregate_direct["Ei"].keys(),
                    "horaire":[doy.date_time]*len(aggregate_direct["Ei"].keys()),
                    "values_Ei":aggregate_direct["Ei"].values()
                }).set_index("Triangles")
            
            data_direct.append(data_caribu_direct)
            if ok==0:
                triangles_,id_geom,_,_,_= cs_direct.as_primitive()
                scene_final.save(f"SCENE_{ok}.bgeom")
            ok+=1
    
    log("CONTROL SCENE CONTROL SIMULATION")
    sky_control=recup_meteo.modelize_sky(1)
    scene_control=scene_consrtructor_contrl(1)
    opt_conf_cont={"default_band":{scene_control[0].id:(0.06,0)}}
    pattern_contr=(BoundingBox(scene_control).getXMin(),BoundingBox(scene_control).getYMin(),BoundingBox(scene_control).getXMax(),BoundingBox(scene_control).getYMax())
    
    diffuse_control=CaribuScene(scene=scene_control,light=sky_control,opt=opt_conf_cont,pattern=pattern_contr)
    _,agg_control=diffuse_control.run(simplify=True,infinite=True,direct=True)
    dataframe_control_diffuse=pd.DataFrame({
                "Triangles":agg_control["Ei"].keys(),
                #"times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
                "values_Ei_diffus":agg_control["Ei"].values()
            }).set_index("Triangles")
    
    dataframe_control_diffuse["diffuse_radiation_value"]=dataframe_control_diffuse["values_Ei_diffus"]* cumul_Rd_diffuse
    
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
    
    data_extract_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) 
    
    # datacaribu_final_sum = (data_extract_direct.groupby("Triangles")["values_Ei"].sum().mul(0.0036).to_frame(name="values_Ei"))
    datacaribu_final_sum = (data_extract_direct.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei"))
   
    data_caribu_direct_diffus=pd.concat([datacaribu_final_sum,datacaribu_diffuse],axis=1,join="outer",ignore_index=False)
    data_caribu_direct_diffus = data_caribu_direct_diffus.reset_index()

    data_caribu_direct_diffus["Ei_total_sum"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)

    scene_demonstration,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=0)
    
    MODULE_MAPPING.mapping_2D (dataframe_panda=data_caribu_direct_diffus,data_contr=data_cont_final,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_demonstration,name=name)
    log("MAPPING DONE SUCCESSFULY")
    data_caribu_direct_diffus.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\{name}.csv")
    return data_caribu_direct_diffus


if __name__=="__main__":
    
    dict_panel_st ={
    "orientation":"est",
    "longueur_p":3.54,
    "largeur_p":4.03,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.54,
    "ecart_rangee":12,
    "hauteur_p":3.7,
    "angle_p":30,
    "st": True}
    
    dict_panel_at ={
    "orientation":"est",
    "longueur_p":3.54,
    "largeur_p":4.03,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4, 
    "ecart_panel":3.54,
    "ecart_rangee":12,
    "hauteur_p":3.7,
    "angle_p":30,
    "st": False}
        
    dict_soil_st ={
        "nb_panel":4,
        "nb_rangee":4,
        "largeur_panel":3.54,
        "orientation":"est",
        "resolution":0.5}

    dict_date_test_janv={
    "debut":"2025-06-16",
    "fin":"2025-06-16",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
    
    dict_date_test_mars={
    "debut":"2025-09-02",
    "fin":"2025-09-02",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}

    process1 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_st,"dict_soil":dict_soil_st,"dict_date":dict_date_test_janv,"name":"janv_solar_trak"})
    process2 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_at,"dict_soil":dict_soil_st,"dict_date":dict_date_test_janv,"name":"janv_anti_track"})
    process3 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_st,"dict_soil":dict_soil_st,"dict_date":dict_date_test_mars,"name":"mai_solar_track"})
    process4 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_at,"dict_soil":dict_soil_st,"dict_date":dict_date_test_mars,"name":"anti_track_mai"})
    
    
    process1.start()
    process2.start()
    process3.start()
    process4.start()


    process1.join()
    process2.join()
    process3.join()
    process4.join()
    

    log('ending')
        



