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
    
    data_direct=[]
    for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=43.34,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            cs=CaribuScene(scene,light=[light_caribu],pattern=pattern)
            _,agg=cs.run(infinite=False, simplify=True)
            dataframe_caribu=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[doy.hours]*len(agg["Ei"].keys()),
                "values_Ei_direct":agg["Ei"].values()
            }).set_index("Triangles")
            data_direct.append(dataframe_caribu)  
    
    dataframe_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) # dataframe output
    datacaribu_direct_sum = (dataframe_direct.groupby("Triangles")["values_Ei_direct"]).sum().to_frame(name="values_Ei_direct")
    
    for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=43.34,intensity=doy.direct_radiation,diffuse=False)
        sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
        if (light_caribu is not None) and (sky is not None):
            caribu_diffus=CaribuScene(scene,light=sky,pattern=pattern)
            _,agg=caribu_diffus.run(infinite=False, simplify=True)
            dataframe_caribu_diffus=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[doy.hours]*len(agg["Ei"].keys()),
                "values_Ei_diffus":agg["Ei"].values(),
            }).set_index("Triangles")
            data_diffuse.append(dataframe_caribu_diffus)  
            
    dataframe_diffuse=pd.concat(data_diffuse,axis=0,join="outer",ignore_index=False)
    datacaribu_diffuse_sum = (dataframe_diffuse.groupby("Triangles")["values_Ei_diffus"]).sum().to_frame(name="values_Ei_diffus")

    # data computation 
    # data cumul 
    data_computation_sum=pd.concat([datacaribu_direct_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    data_computation_sum["Ei_total_cumul"]=(data_computation_sum["values_Ei_direct"] + data_computation_sum["values_Ei_diffus"])
    data_computation_sum["Treatments"]=name
    
    
    dataframe_computation=pd.concat([dataframe_direct,dataframe_diffuse],axis=1,join="outer",ignore_index=False)
    dataframe_computation["Ei_total_radiation"]=(dataframe_computation["values_Ei_direct"] + dataframe_computation["values_Ei_diffus"])
    dataframe_computation["Treatments"]=name
    data_computation_sum.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/summary{name}.csv")
    dataframe_computation.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/dataframe{name}.csv")
    
    return dataframe_computation,data_computation_sum


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
    scene_sud.save(f"TURBID_MEDIUM/BGEOM_TM/no_panel_sud_{name}.bgeom") # scene without panel
    scene_est=semis_alfalfa(scene_to_duplicate,nb_rangee,ecart_rangee,nb_plant,ecart_plant,"est")
    scene_est.save(f"TURBID_MEDIUM/BGEOM_TM/no_panel_est_{name}.bgeom") # scene without panel
    
    
    scene_merge_panel_sud=Scene()
    scene_merge_panel_sud.add(panel_sud)
    scene_merge_panel_sud.add(scene_sud)
    scene_merge_panel_sud.save(f"TURBID_MEDIUM/BGEOM_TM/with_panel_sud_{name}.bgeom") # scene with panel
   
    scene_merge_panel_est=Scene()
    scene_merge_panel_est.add(panel_est)
    scene_merge_panel_est.add(scene_est)
    scene_merge_panel_est.save(f"TURBID_MEDIUM/BGEOM_TM/with_panel_est_{name}.bgeom") # scene with panel 
    

    pattern_sud=extraction_infinite(scene_merge_panel_sud)
    pattern_est=extraction_infinite(scene_merge_panel_est)
    pattern_nop_sud=extraction_infinite(scene_sud)
    pattern_nop_est=extraction_infinite(scene_est)
    
    names = [
    f"{name}_P_SOUTH",
    f"{name}_P_EAST",
    f"{name}_SUD",
    f"{name}_EAST"]
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
    dataframe_P_SOUTH,datasum_P_SOUTH=caribus_scene_run(data_meteo,scene_constructed[0],patterns[0],names[0],annexe)
    dataframe_P_EAST,datasum_P_EAST=caribus_scene_run(data_meteo,scene_constructed[1],patterns[1],names[1],annexe)
    dataframe_SOUTH,datasum_SOUTH=caribus_scene_run(data_meteo,scene_constructed[2],patterns[2],names[2],annexe)
    dataframe_EAST,datasum_EAST=caribus_scene_run(data_meteo,scene_constructed[3],patterns[3],names[3],annexe)

    return [dataframe_P_SOUTH,dataframe_P_EAST,dataframe_SOUTH,dataframe_EAST],[datasum_P_SOUTH,datasum_P_EAST,datasum_SOUTH,datasum_EAST]
    
def dataframe_computation(dataframe,datasum):
    final_dataframe=pd.concat(dataframe,axis=0,join="outer",ignore_index=False)
    final_data_sum=pd.concat(datasum,axis=0,join="outer",ignore_index=False)
    final_dataframe.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/FINAL_DATAFRAME.csv")
    final_data_sum.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/FINAL_SUMMARY.csv")
    return final_dataframe, final_data_sum

scene1=Scene(r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACT\with_panel_sud_WP_300.bgeom")
Viewer.display(scene1)


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
    "orientation":"est",
    "type_panneau":"chapeau",
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
    "orientation":"est",
    "type_panneau":"chapeau",
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
    latitude,longitude,debut,fin=43.34, 0.122,"2025-06-21","2025-06-21"
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    print("direct_radiation :",data_meteo_rd["direct_radiation"].sum())
    print("diffuse_radiation: ", data_meteo_rd["diffuse_radiation"].sum())
    
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
    DATAFRAME= []
    DATASUMMARY=[]
    
    ALFA_HD1_mixte=(bgeom_alfalfa_HD1,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD1",True,2,False,dict_date)
    ALFA_HD2_mixte=(bgeom_alfalfa_HD2,params_panel_couvert_HD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_HD,data_meteo_rd,"HD2",True,2,False,dict_date)
    ALFA_LD1_mixte=(bgeom_alfalfa_LD1,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD1",True,2,False,dict_date)
    ALFA_LD2_mixte=(bgeom_alfalfa_LD2,params_panel_couvert_LD_sud,params_panel_couvert_HD_est,geom_param_alfalfa_LD,data_meteo_rd,"LD2",True,2,False,dict_date)
   
    # ARGS_ALFA=[ALFA_HD1_mixte,ALFA_HD2_mixte,ALFA_LD1_mixte,ALFA_LD2_mixte]
    
    # log("STARTING FIRST SIMULATION ALFALFA FESCUE MIXTURE WITH AND WITHOUT PANEL")
    # with Pool (processes=4) as pool:
    #     Results_alfa= pool.starmap(scene_direct_illumination,ARGS_ALFA)
        
    # for el in Results_alfa:
    #     DATAFRAME.extend(el[0])
    #     DATASUMMARY.extend(el[1])
        
    log("SIMULATION WHEAT_PEA MIXTURE WITH AND WITHOUT PANEL")
    
    params_WHEAT_PEA_300_sud ={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ### panel width
    "largeur_p":1.03,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10
     } # angle beta_p (tilt)
    
    params_WHEAT_PEA_300_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":1.02, ### panel width
    "largeur_p":0.515,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":12} # angle beta_p (tilt)
    
    params_WHEAT_PEA_1100_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ### panel width
    "largeur_p":0.98,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_WHEAT_PEA_1100_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":1.02, ### panel width
    "largeur_p":0.49,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":12} # angle beta_p (tilt)
    
    geom_param_WHEAT_PEA_300={
    "nb_rangee":7,
    "nb_plant":3,
    "ecart_rangee":0.41,
    "ecart_plant":0.34}
    
    geom_param_WHEAT_PEA_1100={
    "nb_rangee":7,
    "nb_plant":3,
    "ecart_rangee":0.39,
    "ecart_plant":0.34}
    
    bgeom_300_DD=r"PAR_FSPM\Wheat-Pea\Scene\T2-1-170210.bgeom" # MIXT 2
    bgeom_1100_DD=r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom" # MIXT 3
    
    log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT 300 AND 1100DD")
    result_300_DD_mixte=(bgeom_300_DD,params_WHEAT_PEA_300_sud,params_WHEAT_PEA_300_est,geom_param_WHEAT_PEA_300,data_meteo_rd,"WP_300",False,2,True,dict_date)
    result_1100_DD_mixte=(bgeom_1100_DD,params_WHEAT_PEA_1100_sud,params_WHEAT_PEA_1100_est,geom_param_WHEAT_PEA_1100,data_meteo_rd,"WP_1100",False,2,True,dict_date)
    
    ARGWP=[result_300_DD_mixte,result_1100_DD_mixte]
    
    with Pool(processes=2) as pool:
        Results_pea_wheat= pool.starmap(scene_direct_illumination,ARGWP)
        
    for el in Results_pea_wheat:
        DATAFRAME.extend(el[0])
        DATASUMMARY.extend(el[1])
    
    log ("SIMULATION FESCU-CLOVER MIXTURE WITH AND WITHOUT PANEL WITH ")
    
    params_fescue_clover_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1, ### panel width
    "largeur_p":0.98,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_fescue_clover_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":1, ### panel width
    "largeur_p":0.49,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":2, # panel heigth max
    "hauteur_bas_p":2, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":12} # angle beta_p (tilt)
    
    geom_param_fescue_clover={
    "nb_rangee":16,
    "nb_plant":10,
    "ecart_rangee":0.17,
    "ecart_plant":0.1}
    
    # log("LOADING BGEOM REPOSITORY")
    # bgeom_as3c1=r"PAR_FSPM\Fescue-Clover\Scene\as3c1.bgeom" # MIXT 2
    # bgeom_as3c3=r"PAR_FSPM\Fescue-Clover\Scene\as3c3.bgeom" # MIXT 3
    
    # log("SIMULATION ")
    # result_as3c1_mixte=(bgeom_as3c1,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as3c1",False,2,False,dict_date)
    # result_as3c3_mixte=(bgeom_as3c3,params_fescue_clover_sud,params_fescue_clover_est,geom_param_fescue_clover,data_meteo_rd,"as3c3",False,2,False,dict_date)
    # ARGS_FESCUE_CLOVER=[result_as3c1_mixte,result_as3c3_mixte]
    
    # log("STARTING FIRST SIMULATION FOR 3 SIMULTANEOUSLY")
    # with Pool(processes=2) as pool:
    #     Results_Fescue_clover= pool.starmap(scene_direct_illumination,ARGS_FESCUE_CLOVER)
        
    # for el in Results_Fescue_clover:
    #     DATAFRAME.extend(el[0])
    #     DATASUMMARY.extend(el[1])
    
    log("COMPUTATION DATA SIMULATIONS")

    _,_=dataframe_computation(DATAFRAME,DATASUMMARY)

    log("SIMULATION TERMINATED")

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    