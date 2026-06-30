# MODULES IMPORTATIONS
from openalea.caribu.CaribuScene import CaribuScene
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
from openalea.caribu.sky_tools import GetLightsSun,Sun,Gensun
# PYTHON INTERNAL IMPORTATIONS
import datetime
from pathlib import Path
import pandas as pd 
import math
from time import time 
from pathlib import Path
# MODULE INTERNAL IMPORTATIONS
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal,recup_meteo
from TURBID_MEDIUM.MODULES_TM_DOC.FONCTIONS_TM import separation_scene_AF,separation_scene_Autre_MIXTE,color,semis_alfalfa,centre_scene_scaled,extraction_infinite,rotation_scene 
from tqdm import tqdm
from multiprocessing import Pool
from copy import deepcopy


# Def log fonction

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

def caribus_scene_run (data_meteo,scene,pattern,name,annexe):
    debut=annexe.get("debut")
    fin=annexe.get("fin")
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    
    data_caribu=[]
    for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=43.34,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            cs=CaribuScene(scene,light=[light_caribu],pattern=pattern)
            _,agg=cs.run(infinite=False, simplify=True)
            dataframe_caribu=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[doy.date_time]*len(agg["Ei"].keys()),
                "values_Ei":agg["Ei"].values()
            }).set_index("Triangles")
            data_caribu.append(dataframe_caribu)  
    
    data_extract=pd.concat(data_caribu,axis=0,join="outer",ignore_index=False)
    datacaribu_direct_sum = (data_extract.groupby("Triangles")["values_Ei"]).sum().mul(0.0036).to_frame(name="values_Ei")
    
    cumul_Rd_diffuse=data_meteo["diffuse_radiation"].sum()
    
    sky=recup_meteo.modelize_sky(1)
    caribu_diffus=CaribuScene(scene=scene,light=sky,pattern=pattern)
    _,agg_diffus=caribu_diffus.run(simplify=True, infinite=False)
    data_diffuse=pd.DataFrame({
                "Triangles":agg_diffus["Ei"].keys(),
                #"times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
                "values_Ei_diffus":agg_diffus["Ei"].values()
            }).set_index("Triangles")
    
    data_diffuse["Ei_sum"]=data_diffuse["values_Ei_diffus"]*cumul_Rd_diffuse
    datacaribu_diffuse_sum = (data_diffuse.groupby("Triangles")["Ei_sum"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))

    data_caribu_direct_diffus_sum=pd.concat([datacaribu_direct_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    
    data_caribu_direct_diffus_sum = data_caribu_direct_diffus_sum.reset_index()
    
    data_caribu_direct_diffus_sum["Ei_total_mean"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])/len(day_of_year_len)
    data_caribu_direct_diffus_sum["Ei_total_cumul"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])
    
    data_mean=data_caribu_direct_diffus_sum.groupby("Triangles")["Ei_total_mean"].sum().reset_index()
    data_sum_sum=data_caribu_direct_diffus_sum.groupby("Triangles")["Ei_total_cumul"].sum().reset_index()
    
    with pd.ExcelWriter(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum{name}.xlsx",engine="openpyxl") as writer:
        data_caribu_direct_diffus_sum.to_excel(writer,sheet_name="DATABRUTE",index=False)
        data_mean.to_excel(writer,sheet_name="DATA RG MEAN",index=False)
        data_sum_sum.to_excel(writer,sheet_name="DATA RG CUMUL",index=False)
    
    data_mean["simulation"]=name
    data_sum_sum["simulation"]=name

    data_caribu_direct_diffus_sum.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum{name}.csv")
    
    return {"simulation":name,"mean":data_mean,"cumul":data_sum_sum}

def simulation_TM (scene,dict_panel_sud,dict_panel_est,dict_geom_param,name,alfalfa=True,choose=0,cover_rotated=False):
    """_summary_
    scene1: legume,sceen2=wheat and scene3=mixte
    0=legumen,1=wheat and 2= mixite
    """
    if alfalfa== True:
        scene_1,scene_2,scene_3=separation_scene_AF(scene) 
    else:
        scene_1,scene_2,scene_3=separation_scene_Autre_MIXTE(scene)
        
    choice=[scene_1,scene_2,scene_3]

    choisen_one=choice[choose]
    # forced id 
    scene_choisen=color(choisen_one,factor=0.01)
    if alfalfa==True:
        scene_centrated=scene_choisen
    else:
        scene_centrated=centre_scene_scaled(scene_choisen)
    
    # rotation for wheat-pea mock
    if cover_rotated==False:
        scene_to_duplicate=scene_centrated
    else:
        scene_to_duplicate=rotation_scene(scene_centrated)
    #scene _ panel
    panel_sud,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel_sud)
    panel_est,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel_est)
    
    #scene_duplication semis
    nb_rangee=dict_geom_param.get("nb_rangee")
    nb_plant=dict_geom_param.get("nb_plant")
    ecart_rangee=dict_geom_param.get("ecart_rangee")
    ecart_plant=dict_geom_param.get("ecart_plant")
    
    # scene ducplication
    scene_sud=semis_alfalfa(scene_to_duplicate,nb_rangee,ecart_rangee,nb_plant,ecart_plant,"sud")
    scene_sud.save(f"no_panel_sud_{name}.bgeom") # scene without panel
    scene_est=semis_alfalfa(scene_to_duplicate,nb_rangee,ecart_rangee,nb_plant,ecart_plant,"est")
    scene_est.save(f"no_panel_est_{name}.bgeom") # scene without panel
    
    
    # # log(f"choisen_one shapes : {len(choisen_one)}")
    # scene_choisen = color(choisen_one, factor=0.01)
    # # log(f"scene_choisen shapes : {len(scene_choisen)}")
    # scene_centrated = scene_choisen if alfalfa else centre_scene_scaled(scene_choisen)
    # # log(f"scene_centrated shapes : {len(scene_centrated)}")
    # scene_to_duplicate = scene_centrated if not cover_rotated else rotation_scene(scene_centrated)
    # # log(f"scene_to_duplicate shapes : {len(scene_to_duplicate)}")
    
    
    scene_merge_panel_sud=Scene()
    scene_merge_panel_sud.add(panel_sud)
    scene_merge_panel_sud.add(scene_sud)
    scene_merge_panel_sud.save(f"with_panel_sud_{name}.bgeom") # scene with panel
   
    scene_merge_panel_est=Scene()
    scene_merge_panel_est.add(panel_est)
    scene_merge_panel_est.add(scene_est)
    scene_merge_panel_est.save(f"with_panel_est_{name}.bgeom") # scene with panel 
    

    pattern_sud=extraction_infinite(scene_merge_panel_sud)
    pattern_est=extraction_infinite(scene_merge_panel_est)
    pattern_nop_sud=extraction_infinite(scene_sud)
    pattern_nop_est=extraction_infinite(scene_est)
    
    # name of scene 
    
    choices_label = {0: "grass", 1: "legume", 2: "mixte"}.get(choose, f"scene_{choose}")
    names = [
    f"{name}_{choices_label}_with_panel_sud",
    f"{name}_{choices_label}_with_panel_est",
    f"{name}_{choices_label}_no_panel_sud",
    f"{name}_{choices_label}_no_panel_est",]

    
    # scene_final=scene_direct_illumination(scene_merge_panel_sud,pattern_sud,data_meteo,names[0])
    
    # with Pool (processes=4) as pool:
    #      scene_final=pool.starmap(scene_direct_illumination, args)
    
    return [scene_merge_panel_sud,scene_merge_panel_est,scene_sud,scene_est],[pattern_sud,pattern_est,pattern_nop_sud,pattern_nop_est],names


def computation_data (scene_final):

    data_frame_compilated=[]
    for ind, element in enumerate(scene_final):
            for i, el in enumerate(element):
                data=pd.DataFrame(el)
                data_frame_compilated.append(data)
    data_raw=pd.concat(data_frame_compilated,axis=0,ignore_index=False)
    data_raw.to_excel(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum_total.xlsx")
    data_raw.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum_total.csv")
    
    return data_raw
    
def scene_direct_illumination (scene_path,dict_panel_sud,dict_panel_est,dict_geom_param,data_meteo,name,alfalfa,choose,cover_rotated,annexe):
    scene=Scene(scene_path)
    # scene creation with and without panels and east and south orientation 

    scene_constructed,patterns,names=simulation_TM(scene,dict_panel_sud,dict_panel_est,dict_geom_param,name,alfalfa,choose,cover_rotated)
    
    # caribuscene simulation 

    south_with_panel=caribus_scene_run(data_meteo,scene_constructed[0],patterns[0],names[0],annexe)

    east_with_panel=caribus_scene_run(data_meteo,scene_constructed[1],patterns[1],names[1],annexe)

    south_control=caribus_scene_run(data_meteo,scene_constructed[2],patterns[2],names[2],annexe)

    east_control=caribus_scene_run(data_meteo,scene_constructed[3],patterns[3],names[3],annexe)

    
    return [south_with_panel,east_with_panel,south_control,east_control]
    
     
    
    


# def scene_direct_illumination (scene_path,pattern,data_meteo,dict_panel_sud,dict_panel_est,dict_geom_param,alfalfa,choose,cover_rotated,name):
#     scene=Scene(scene_path)
   
#     data_caribu=[]
#     for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
#         light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=43.34,intensity=doy.direct_radiation,diffuse=False)
#         if light_caribu is not None:
#             cs=CaribuScene(scene,light=[light_caribu],pattern=pattern)
#             _,agg=cs.run(infinite=False, simplify=True)
#             dataframe_caribu=pd.DataFrame({
#                 "Triangles":agg["Ei"].keys(),
#                 "horaire":[doy.date_time]*len(agg["Ei"].keys()),
#                 "values_Ei":agg["Ei"].values()
#             }).set_index("Triangles")
#             data_caribu.append(dataframe_caribu)  
            
#     data_extract=pd.concat(data_caribu,axis=0,join="outer",ignore_index=False)
#     datacaribu_direct_sum = (data_extract.groupby("Triangles")["values_Ei"]).sum().mul(0.0036).to_frame(name="values_Ei")

#     sky=recup_meteo.modelize_sky(1)

#     caribu_diffus=CaribuScene(scene=scene,light=sky,pattern=pattern)
    
#     _,agg_diffus=caribu_diffus.run(simplify=True, infinite=False)
#     data_diffuse=pd.DataFrame({
#                 "Triangles":agg_diffus["Ei"].keys(),
#                 #"times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
#                 "values_Ei_diffus":agg_diffus["Ei"].values()
#             }).set_index("Triangles")
    
#     data_diffuse["Ei_sum"]=data_diffuse["values_Ei_diffus"]*cumul_Rd_diffuse
#     datacaribu_diffuse_sum = (data_diffuse.groupby("Triangles")["Ei_sum"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))
    
#     data_caribu_direct_diffus_sum=pd.concat([datacaribu_direct_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    
#     data_caribu_direct_diffus_sum = data_caribu_direct_diffus_sum.reset_index()
    
#     data_caribu_direct_diffus_sum["Ei_total_mean"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])/len(day_of_year_len)
#     data_caribu_direct_diffus_sum["Ei_total_cumul"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])
    
#     data_mean=data_caribu_direct_diffus_sum.groupby("Triangles")["Ei_total_mean"].sum().reset_index()
#     data_sum_sum=data_caribu_direct_diffus_sum.groupby("Triangles")["Ei_total_cumul"].sum().reset_index()
    
#     with pd.ExcelWriter(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum{name}.xlsx",engine="openpyxl") as writer:
#         data_caribu_direct_diffus_sum.to_excel(writer,sheet_name="DATABRUTE",index=False)
#         data_mean.to_excel(writer,sheet_name="DATA RG MEAN",index=False)
#         data_sum_sum.to_excel(writer,sheet_name="DATA RG CUMUL",index=False)
    
#     data_mean["simulation"]=name
#     data_sum_sum["simulation"]=name

#     data_caribu_direct_diffus_sum.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/data_caribu_direct_diffus_sum{name}.csv")
    
#     return {"simulation":name,"mean":data_mean,"cumul":data_sum_sum}



    
# ss=Scene(r"no_panel_est_HD1_mixte.bgeom")
# Viewer.display(ss)

# data=extraction_infinite(ss)
# print(data)


# code execution
if __name__=="__main__":
    
    log("MOADING PARAMETERS")
    params_panel_couvert_HD_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.93,
    "largeur_p":0.97,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_couvert_LD_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ### panel width
    "largeur_p":1.14,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_couvert_HD_est={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.93,
    "largeur_p":0.485,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":12} # angle beta_p (tilt)
    
    params_panel_couvert_LD_est={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ### panel width
    "largeur_p":0.57,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":12} # angle beta_p (tilt)
    
    log(" DATA METEO LOADING ")
    dict_date={
        "debut":"2025-09-21",
        "fin":"2025-09-21"
    }
    
    latitude,longitude,debut,fin=43.34, 0.122,"2025-09-21","2025-09-21"
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    geom_param_alfalfa_HD={
    "nb_rangee":9,
    "nb_plant":3,
    "ecart_rangee":0.3,
    "ecart_plant":0.31
    }
    
    geom_param_alfalfa_LD={
    "nb_rangee":3,
    "nb_plant":3,
    "ecart_rangee":1.06,
    "ecart_plant":0.34
    }
    
    log("SCENE IMPORTATION FIRST MIXTURE ")
    
    bgeom_alfalfa_HD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom"
    bgeom_alfalfa_HD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom"
    bgeom_alfalfa_LD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD1-asso-luz.bgeom"
    bgeom_alfalfa_LD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom"
    
    
    log("SIMULATION ALFALFA_FESCUE MIXTURE WITH AND WITHOUT PANEL HD1 MOCK-UP")
    FINAL_RESULT= []
    
    ALFAHD1_mixte=(bgeom_alfalfa_HD1,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD1_mixte",True,2,False,dict_date)
    ALFAHD1_fes=(bgeom_alfalfa_HD1,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD1_fescue",True,1,False,dict_date)
    ALFAHD1_alfa=(bgeom_alfalfa_HD1,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD1_fescue",True,1,False,dict_date)
    
    ALFAHD2_mixte=(bgeom_alfalfa_HD2,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD2_mixte",True,2,False,dict_date)
    ALFAHD2_fes=(bgeom_alfalfa_HD2,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD2_fescue",True,1,False,dict_date)
    ALFAHD2_alf=(bgeom_alfalfa_HD2,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD2_alfalfa",True,0,False,dict_date)
    
    ALFALD1_mixte=(bgeom_alfalfa_LD1,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD1_mixte",True,2,False,dict_date)
    ALFALD1_fes=(bgeom_alfalfa_LD1,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD1_fescue",True,1,False,dict_date)
    ALFALD1_alf=(bgeom_alfalfa_LD1,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD1_alfalfa",True,0,False,dict_date)
    
    ALFA_LD2_mixte=(bgeom_alfalfa_LD2,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD2_mixte",True,2,False,dict_date)
    ALFA_LD2_fes=(bgeom_alfalfa_LD2,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD2_fescue",True,1,False,dict_date)
    ALFA_LD2_alf= (bgeom_alfalfa_LD2,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD2_alfalfa",True,0,False,dict_date)
    
    
    
    log("STARTING FIRST SIMULATION FOR AFLAFA FESCUE MIXTURE")
    arg_alfa_1=[ALFAHD1_mixte,ALFAHD1_fes,ALFAHD1_alfa,ALFAHD2_mixte,ALFAHD2_fes,ALFAHD2_alf]
    arg_alfa_2=[ ALFALD1_mixte,ALFALD1_fes,ALFALD1_alf,ALFA_LD2_mixte,ALFA_LD2_fes,ALFA_LD2_alf]
    
    log("STARTING FIRST SIMULATION FOR AFLAFA HIGH DENSITY")
    with Pool (processes=6) as pool:
        Results_alfa1= pool.starmap(scene_direct_illumination,arg_alfa_1)
    FINAL_RESULT.append(Results_alfa1)
    
    log("STARTING FIRST SIMULATION FOR AFLAFA LOW DENSITY")
    with Pool (processes=6) as pool:
        Results_alfa2= pool.starmap(scene_direct_illumination,arg_alfa_2)
    FINAL_RESULT.append(Results_alfa2)

  
    # log ("SIMULATION FESCU-CLOVER MIXTURE WITH AND WITHOUT PANEL WITH ")
    
    # params_fescue_clover_sud={
    # "orientation":"sud",
    # "type_panneau":"normal",
    # "longueur_p":1, ### panel width
    # "largeur_p":0.98,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":10} # angle beta_p (tilt)
    
    # params_fescue_clover_est={
    # "orientation":"est",
    # "type_panneau":"chapeau",
    # "longueur_p":1, ### panel width
    # "largeur_p":0.49,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":12} # angle beta_p (tilt)
    
    # geom_param_fescue_clover={
    # "nb_rangee":16,
    # "nb_plant":10,
    # "ecart_rangee":0.17,
    # "ecart_plant":0.1}
    
    # log("LOADING BGEOM REPOSITORY")
    # bgeom_as05c1=r'PAR_FSPM\Fescue-Clover\Scene\as05c1.bgeom'# MIXT 1
    # bgeom_as2c1=r"PAR_FSPM\Fescue-Clover\Scene\as2c1.bgeom" # MIXT 2
    # bgeom_as3c1=r"PAR_FSPM\Fescue-Clover\Scene\as3c1.bgeom" # MIXT 3
    
    # log("SIMULATION ")
    # result_as05c1_mixte=(bgeom_as05c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as05c1_mixte",False,2,False,dict_date)
    # result_fescue_as05c1=(bgeom_as05c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as05c1_fescue",False,1,False,dict_date)
    # result_clover_as05c1=(bgeom_as05c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as05c1_clover",False,0,False,dict_date)
    
    # result_as2c1_mixte=(bgeom_as2c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as2c1_mixte",False,2,False,dict_date)
    # result_fescue_as2c1=(bgeom_as2c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as2c1_fescue",False,1,False,dict_date)
    # result_clover_as2c1=(bgeom_as2c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as2c1_clover",False,0,False,dict_date)
    
    # result_as3c1_mixte=(bgeom_as3c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as3c1_mixte",False,2,False,dict_date)
    # result_fescue_as3c1=(bgeom_as3c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as3c1_fescue",False,1,False,dict_date)
    # result_clover_as3c1=(bgeom_as3c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as3c1_clover",False,0,False,dict_date)
    
    
    # args_firs_sum=[result_as05c1_mixte,result_fescue_as05c1,result_clover_as05c1,result_as2c1_mixte,result_fescue_as2c1,result_clover_as2c1,result_as3c1_mixte,result_fescue_as3c1,result_clover_as3c1]
    
    # log("STARTING FIRST SIMULATION FOR 9 SIMULTANEOUSLY")
    # with Pool(processes=9) as pool:
    #     Results_Fescue_clover= pool.starmap(scene_direct_illumination,args_firs_sum)
    # FINAL_RESULT.append(Results_Fescue_clover) 
    
    # log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT PANEL")
    
    # params_WHEAT_PEA_300_sud={
    # "orientation":"sud",
    # "type_panneau":"normal",
    # "longueur_p":1.02, ### panel width
    # "largeur_p":1.03,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":10} # angle beta_p (tilt)
    
    # params_WHEAT_PEA_300_est={
    # "orientation":"est",
    # "type_panneau":"chapeau",
    # "longueur_p":1.02, ### panel width
    # "largeur_p":0.515,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":12} # angle beta_p (tilt)
    
    # params_WHEAT_PEA_1100_sud={
    # "orientation":"sud",
    # "type_panneau":"normal",
    # "longueur_p":1.02, ### panel width
    # "largeur_p":0.98,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":10} # angle beta_p (tilt)
    
    # params_WHEAT_PEA_1100_est={
    # "orientation":"est",
    # "type_panneau":"chapeau",
    # "longueur_p":1.02, ### panel width
    # "largeur_p":0.49,# panel length
    # "resolution_p":0.4, # for the mesh when use mesh panel fonction
    # "nb_panel":1, # the standard for simulation
    # "nb_rangee":1, # the standard for simulation
    # "ecart_panel":3.64,# about panel width to concatenate two panels
    # "ecart_rangee":2.5, # dtistance between two divide(piqué)
    # "hauteur_haut_p":2, # panel heigth max
    # "hauteur_bas_p":2, # panel heigth min
    # "panel_opacity":1, # beyon 1 for panel semitransparent
    # "angle_p":12} # angle beta_p (tilt)
    
    # geom_param_WHEAT_PEA_300={
    # "nb_rangee":7,
    # "nb_plant":3,
    # "ecart_rangee":0.41,
    # "ecart_plant":0.34}
    
    # geom_param_WHEAT_PEA_1100={
    # "nb_rangee":7,
    # "nb_plant":3,
    # "ecart_rangee":0.39,
    # "ecart_plant":0.34}
    
    # log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT LOADING BGEOM PARAMETERS")
    
    # bgeom_300_DD=r"PAR_FSPM\Wheat-Pea\Scene\T2-1-170210.bgeom" # MIXT 2
    # bgeom_1100_DD=r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom" # MIXT 3
    
    # log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT 300 AND 1100DD")
    # result_300_DD_mixte=(bgeom_300_DD,params_WHEAT_PEA_300_sud,params_WHEAT_PEA_300_est,geom_param_WHEAT_PEA_300,data_meteo_rd,"300_DD_mixte",False,2,True,dict_date)
    # result_WHEAT_300_DD=(bgeom_300_DD,params_fescue_clover_sud,params_fescue_clover_est,geom_param_WHEAT_PEA_300,data_meteo_rd,"WHEAT_300_DD",False,1,True,dict_date)
        
    # result_PEA_300_DD=(bgeom_300_DD,params_fescue_clover_sud,params_fescue_clover_est,geom_param_WHEAT_PEA_300,data_meteo_rd,"PEA_300_DD",False,0,True,dict_date)
    # result_1100_DD_mixte=(bgeom_1100_DD,params_WHEAT_PEA_1100_sud,params_WHEAT_PEA_1100_est,geom_param_WHEAT_PEA_1100,data_meteo_rd,"300_DD_mixte",False,2,True,dict_date)

    # result_WHEAT_1100_DD=(bgeom_1100_DD,params_WHEAT_PEA_1100_sud,params_WHEAT_PEA_1100_est,geom_param_WHEAT_PEA_1100,data_meteo_rd,"WHEAT_300_DD",False,1,True,dict_date)
    # result_PEA_1100_DD=(bgeom_1100_DD,params_WHEAT_PEA_1100_sud,params_WHEAT_PEA_1100_est,geom_param_WHEAT_PEA_1100,data_meteo_rd,"PEA_300_DD",False,0,True,dict_date)
    
    # args_wp=[result_300_DD_mixte,result_WHEAT_300_DD,result_PEA_300_DD,result_1100_DD_mixte,result_WHEAT_1100_DD,result_PEA_1100_DD]
    
    # log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT 1100 DD WITH 6 PROCESS SIMULTANEOUSLY")
    
    # with Pool(processes=6) as pool:
    #     Results_pea_wheat= pool.starmap(scene_direct_illumination,args_wp)
    # FINAL_RESULT.append(Results_pea_wheat) 
    
    # log("COMPUTATION RESULTS FROM ALL SIMULATIONS ")
    
    # data=computation_data(FINAL_RESULT)
    
    log("SIMULATION TERMINATED")

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    