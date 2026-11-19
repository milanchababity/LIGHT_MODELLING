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
from TURBID_MEDIUM.MODULES_TM_DOC.FONCTIONS_TM import separation_scene_AF,separation_scene_Autre_MIXTE,color,semis_alfalfa,centre_scene_scaled,extraction_infinite,rotation_scene,scaled_fonction 
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
    heure_decimal=[10]
    doy = data_meteo.iloc[2]["day_of_year"]
    
    sky = recup_meteo.modelize_sky(1)
    caribu_diffuse=CaribuScene(scene,light=sky,pattern=pattern)
    _,agg_diffuse=caribu_diffuse.run(simplify=True,infinite=True)
    data_frame_diffus=pd.DataFrame({
                "Triangles":agg_diffuse["Ei"].keys(),
                "values_Eabs_brute": agg_diffuse["Ei"].values()}).set_index("Triangles")
    
    data_diffuse_list=[]
    for h in tqdm(heure_decimal, total=len(heure_decimal)):
    # for ind, doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))):
        # if doy.diffuse_radiation > 0:
        data=data_frame_diffus.copy()
        data["values_Eabs_diffus"]=data["values_Eabs_brute"]*1
        data["horaire"]=h
        data_diffuse_list.append(data)
    
    dataframe_diffuse = pd.concat(data_diffuse_list,axis=0,ignore_index=False).reset_index().set_index(["Triangles","horaire"])
    
    datacaribu_diffuse_sum=(dataframe_diffuse.groupby("Triangles") ["values_Eabs_diffus"]).sum().to_frame("values_Eabs_diffus_tot")
        
    
    for h in tqdm(heure_decimal, total=len(heure_decimal)):
    # for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy,heure_decimaux=h,latitude=47.64,intensity=1 ,diffuse=False) 
        if light_caribu is not None:
            cs=CaribuScene(scene,light=[light_caribu],pattern=pattern)
            _,agg=cs.run(infinite=True, simplify=True)
            dataframe_caribu=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[h]*len(agg["Ei"].keys()),
                "values_Eabs_direct":agg["Ei"].values()
            }).set_index(["Triangles","horaire"])
            data_direct.append(dataframe_caribu)  
    
    dataframe_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) # dataframe output
    datacaribu_direct_sum = (dataframe_direct.groupby("Triangles")["values_Eabs_direct"]).sum().to_frame(name="values_Eabs_direct")

 
    # data_diffuse=[]
    # for ind,doy in enumerate(tqdm(data_meteo.itertuples(),total=len(data_meteo))): 
    #     light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=43.34,intensity=doy.direct_radiation,diffuse=False)
    #     sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
    #     if (light_caribu is not None) and (sky is not None):
    #         caribu_diffus=CaribuScene(scene,light=sky,pattern=pattern)
    #         _,agg=caribu_diffus.run(infinite=False, simplify=True)
    #         dataframe_caribu_diffus=pd.DataFrame({
    #             "Triangles":agg["Ei"].keys(),
    #             "horaire":[doy.hours]*len(agg["Ei"].keys()),
    #             "values_Ei_diffus":agg["Ei"].values(),
    #         }).set_index("Triangles")
    #         data_diffuse.append(dataframe_caribu_diffus)  
            
    # dataframe_diffuse=pd.concat(data_diffuse,axis=0,join="outer",ignore_index=False)
    # datacaribu_diffuse_sum = (dataframe_diffuse.groupby("Triangles")["values_Ei_diffus"]).sum().to_frame(name="values_Ei_diffus")

    # data computation 
    
    data_computation_sum=pd.concat([datacaribu_direct_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    data_computation_sum["Ei_total_cumul"]=(data_computation_sum["values_Eabs_direct"] + data_computation_sum["values_Eabs_diffus_tot"])
    data_computation_sum["Treatments"]=name
    
    dataframe_computation=pd.concat([dataframe_direct,dataframe_diffuse],axis=1,join="outer",ignore_index=False)
    dataframe_computation["Eabs_total_radiation"]=(dataframe_computation["values_Eabs_direct"] + dataframe_computation["values_Eabs_diffus"])
    dataframe_computation["Treatments"]=name
    data_computation_sum.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/summary{name}.csv")
    dataframe_computation.to_csv(f"TURBID_MEDIUM/OUTPUTS_TM/dataframe{name}.csv")
    
    return dataframe_computation,data_computation_sum


def simulation_TM (scene,dict_panel_plat_sud,dict_geom_param,name,alfalfa=True,choose=2,cover_rotated=False):
    """_summary_
    scene1: legume,sceen2=wheat and scene3=mixte
    0=legumen,1=wheat and 2= mixite
    """
    if alfalfa== True:
        scene_1,scene_2,scene_3=separation_scene_AF(scene) 
    else:
        scene_1,scene_2,scene_3,scene_sol=separation_scene_Autre_MIXTE(scene)
        
    choice=[scene_1,scene_2,scene_3]

    choisen_one=choice[choose]
    # forced id 
    scene_choisen=color(choisen_one,factor=0.01)
    
    if alfalfa==True:
        scene_centrated=scene_choisen
    else:
        scene_sol_scaled=color(scene_sol,0.01)
        scene_centrated=centre_scene_scaled(scene_choisen,scene_sol_scaled)
    
    # rotation for wheat-pea mock-up
    if cover_rotated==False:
        scene_to_duplicate=scene_centrated
    else:
        scene_to_duplicate=rotation_scene(scene_centrated)
    #scene _ panel sud à plat
    panel_sud,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel_plat_sud)
    # panel_est,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel_est)
    
    #scene_duplication semis
    nb_rangee=dict_geom_param.get("nb_rangee")
    nb_plant=dict_geom_param.get("nb_plant")
    ecart_rangee=dict_geom_param.get("ecart_rangee")
    ecart_plant=dict_geom_param.get("ecart_plant")
    
    # scene ducplication
    scene_sud=semis_alfalfa(scene_to_duplicate,nb_rangee,ecart_rangee,nb_plant,ecart_plant,"sud")
    scene_sud.save(f"OUTPUTS_ABSTRACT/TURBID_MEDIUM_LIGHT/ABSTRACT/no_panel_sud_{name}.bgeom") # scene without panel
    # scene_est=semis_alfalfa(scene_to_duplicate,nb_rangee,ecart_rangee,nb_plant,ecart_plant,"est")
    # scene_est.save(f"TURBID_MEDIUM/BGEOM_TM/no_panel_EST_{name}.bgeom") # scene without panel
    
    
    scene_merge_panel_sud=Scene()
    scene_merge_panel_sud.add(panel_sud)
    scene_merge_panel_sud.add(scene_sud)
    scene_merge_panel_sud.save(f"OUTPUTS_ABSTRACT/TURBID_MEDIUM_LIGHT/ABSTRACT/with_panel_sud_{name}.bgeom") # scene with panel
   
    # scene_merge_panel_est=Scene()
    # scene_merge_panel_est.add(panel_est)
    # scene_merge_panel_est.add(scene_est)
    # scene_merge_panel_est.save(f"TURBID_MEDIUM/BGEOM_TM/with_panel_EST_{name}.bgeom") # scene with panel 
    

    pattern_sud=extraction_infinite(scene_merge_panel_sud)
    # pattern_est=extraction_infinite(scene_merge_panel_est)
    pattern_nop_sud=extraction_infinite(scene_sud)
    # pattern_nop_est=extraction_infinite(scene_est)
    
    names = [f"{name}_P_SUD",f"{name}_NO_SUD"]
    return [scene_merge_panel_sud,scene_sud],[pattern_sud,pattern_nop_sud],names


##################################################################

def pattern_extraction(scene_path,list_name, type="0"):
    
    def x_y_position(scene,name):
        
        x_min=BoundingBox(scene).getXMin()
        x_max=BoundingBox(scene).getXMax()
        y_min=BoundingBox(scene).getYMin()
        y_max=BoundingBox(scene).getYMax()
        z_min=BoundingBox(scene).getZMin()
        z_max=BoundingBox(scene).getZMax()
        data = pd.DataFrame([{"x_min": x_min,"x_max": x_max,"y_min": y_min,"y_max": y_max,"z_min": z_min,"z_max": z_max,"labels": name}])
        return data
    
    data_final_spec1=[]
    data_final_spec2=[]
    data_final_mixte=[]
    
    for i in range(len(scene_path)):
        scene=Scene(scene_path[i])
        name=list_name[i]
        
        if type ==0: 
            scene1,scene2,scene_mixte=separation_scene_AF(scene)
            scene_scaled_luz,scene_scaled_alf,scene_scaled_mixte=color(scene1,0.01),color(scene2,0.01),color(scene_mixte,0.01)
        
        else:
            scene_int1,scene2_scene_int_2,scene_mixte_int=separation_scene_Autre_MIXTE(scene)
            scene__1,scene__2,scene__3=color(scene_int1,0.01),color(scene2_scene_int_2,0.01),color(scene_mixte_int,0.01)     
            scene_scaled_luz,scene_scaled_alf,scene_scaled_mixte=centre_scene_scaled(scene__1),centre_scene_scaled(scene__2),centre_scene_scaled(scene__3) 
            
        data=x_y_position(scene_scaled_luz,name)
        data1=x_y_position(scene_scaled_alf,name)
        data2=x_y_position(scene_scaled_mixte,name)
        data_final_spec1.append(data)
        data_final_spec2.append(data1)
        data_final_mixte.append(data2)
    
    SPECIE_1=pd.concat(data_final_spec1,axis=0,ignore_index=False,join="outer")
    SPECIE_2=pd.concat(data_final_spec2,axis=0,ignore_index=False,join="outer")
    SPECIE_3=pd.concat(data_final_mixte,axis=0,ignore_index=False,join="outer")
    
    return SPECIE_1,SPECIE_2,SPECIE_3
    

# HD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom"
# HD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom"
# LD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD1-asso-luz.bgeom"
# LD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom"

# HD=[HD1,HD2,LD1,LD2]
# list_name=["HD1","HD2","LD1","LD2"]

# SP1,SP2,SP3=pattern_extraction(HD,list_name,0)


# # WHEAT PEA PREPARATION
# bgeom_300_DD=r"PAR_FSPM\Wheat-Pea\Scene\T2-1-170210.bgeom" # MIXT 2
# bgeom_1100_DD=r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom" # MIXT 3

# WP=[bgeom_300_DD,bgeom_1100_DD]
# list_wp=["MIXT_300_WP","MIX_1100_PW"]
# PEA,WHEAT,WP_MIXTE=pattern_extraction(WP,list_wp,1)

# #FESCUE_CLOVER

# bgeom_as3c1=r"PAR_FSPM\Fescue-Clover\Scene\as3c1.bgeom" # MIXT 2
# bgeom_as3c3=r"PAR_FSPM\Fescue-Clover\Scene\as3c3.bgeom" # MIXT 3
# FS_CLV=[bgeom_as3c1,bgeom_as3c3]
# list_fesc=["AS3C1","AS3C3"]

# CLOV,FESC,MIX_CL_F=pattern_extraction(FS_CLV,list_fesc,1)


# with pd.ExcelWriter("pattern_results.xlsx", engine="openpyxl") as writer:
#     SP1.to_excel(writer, sheet_name="ALFALFA", index=False)
#     SP2.to_excel(writer, sheet_name="FESCUE", index=False)
#     SP3.to_excel(writer, sheet_name="MIXTE_ALFA_FESCUE", index=False)
#     PEA.to_excel(writer, sheet_name="PEA", index=False)
#     WHEAT.to_excel(writer, sheet_name="WHEAT", index=False)
#     WP_MIXTE.to_excel(writer, sheet_name="MIXTE_WHEAT_PEA", index=False)
#     CLOV.to_excel(writer, sheet_name="CLOV", index=False)
#     FESC.to_excel(writer, sheet_name="FESC_CL", index=False)
#     MIX_CL_F.to_excel(writer, sheet_name="MIXTE_FESCUE_CLOVER", index=False)
    
    

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
    
# def scene_direct_illumination(scene_path,dict_panel_sud,dict_geom_param,data_meteo,name,alfalfa,choose,cover_rotated,annexe):
#     scene=Scene(scene_path)
#     # scene creation with and without panels and east and south orientation 
    
    
#     scene_constructed,patterns,names=simulation_TM(scene,dict_panel_sud,dict_geom_param,name,alfalfa,choose,cover_rotated)
#     # caribuscene simulation 
#     dataframe_P_SOUTH,datasum_P_SOUTH=caribus_scene_run(data_meteo,scene_constructed[0],patterns[0],names[0],annexe)
#     dataframe_NOP_SOUTH,datasum_NOP_SOUTH=caribus_scene_run(data_meteo,scene_constructed[1],patterns[1],names[1],annexe)
#     # dataframe_SOUTH,datasum_SOUTH=caribus_scene_run(data_meteo,scene_constructed[2],patterns[2],names[2],annexe)
#     # dataframe_EAST,datasum_EAST=caribus_scene_run(data_meteo,scene_constructed[3],patterns[3],names[3],annexe)

#     return [dataframe_P_SOUTH,dataframe_NOP_SOUTH],[datasum_P_SOUTH,datasum_NOP_SOUTH]
    

def scene_direct_illumination(scene_path,dict_panel_sud,dict_geom_param,data_meteo,name,alfalfa,choose,cover_rotated,annexe,pattern):
    scene=Scene(scene_path)
    # scene creation with and without panels and east and south orientation 
    
    scene_constructed,_,names=simulation_TM(scene,dict_panel_sud,dict_geom_param,name,alfalfa,choose,cover_rotated)
    # caribuscene simulation 
    dataframe_P_SOUTH,datasum_P_SOUTH=caribus_scene_run(data_meteo,scene_constructed[0],pattern,names[0],annexe)
    dataframe_NOP_SOUTH,datasum_NOP_SOUTH=caribus_scene_run(data_meteo,scene_constructed[1],pattern,names[1],annexe)
    # dataframe_P_EAST,datasum_P_EAST=caribus_scene_run(data_meteo,scene_constructed[0],patterns[0],names[0],annexe)
    # dataframe_NOP_EAST,datasum_NOP_EAST=caribus_scene_run(data_meteo,scene_constructed[1],patterns[1],names[1],annexe)

    return [dataframe_P_SOUTH,dataframe_NOP_SOUTH],[datasum_P_SOUTH,datasum_NOP_SOUTH]


def dataframe_computation(dataframe,datasum):
    final_dataframe=pd.concat(dataframe,axis=0,join="outer",ignore_index=False)
    final_data_sum=pd.concat(datasum,axis=0,join="outer",ignore_index=False)
    final_dataframe.to_csv(f"OUTPUTS_ABSTRACT/TURBID_MEDIUM_LIGHT/ABSTRACT/3D_SIMULATION_RAW_SUD_10DEG.csv")
    final_data_sum.to_csv(f"OUTPUTS_ABSTRACT/TURBID_MEDIUM_LIGHT/ABSTRACT/3D_SIMULATION_SUM_SUD_10DEG.csv")
    return final_dataframe, final_data_sum


# x=Shape(Box(Vector3(1,1,0)))
# Viewer.display(x)
# print(dir(Point3Array))


# # # A list of the coordinates of the square


# scene_couvert=Scene(r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACT\with_panel_sud_LD1_SUD_10DEG.bgeom")
# # ###########################################################
# scene_alfalfa=Scene(r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom")

# bgeom_1100_DD=r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom" # MIXT 3


# log("MOADING PARAMETERS")
# params_panel_couvert_HD_sud={
#     "orientation":"sud",
#     "type_panneau":"normal",
#     "longueur_p":0.34, # Y panel
#     "largeur_p":0.38,# X panel
#     "resolution_p":0.4, # for the mesh when use mesh panel fonction
#     "nb_panel":1, # the standard for simulation
#     "nb_rangee":1, # the standard for simulation
#     "ecart_panel":3.64,# about panel width to concatenate two panels
#     "ecart_rangee":2.5, # dtistance between two divide(piqué)
#     "hauteur_haut_p":4, # panel heigth max 4.05
#     "hauteur_bas_p":4,
#     "hauteur": 4,  # panel heigth min 3.35
#     "panel_opacity":1, # beyon 1 for panel semitransparent
#     "angle_p":0} # angle beta_p (tilt)

# pattern_HD=(-1.35,-0.47,1.35,0.47)
# pattern_HD_maquette=(-0.150,-0.155,0.150,0.155)
# panneau_1,_=scene_modelling_normal.type_panneau_orient_univ(params_panel_couvert_HD_sud)
# light_caribu,_,_ =recup_meteo.light_caribu(172,17,47.64,1,False)


# x_min=-0.53#BoundingBox(scene_test).getXMin()
# x_max=0.53#BoundingBox(scene_test).getXMax()
# y_min=-0.17#BoundingBox(scene_test).getYMin()
# y_max=0.17#BoundingBox(scene_test).getYMax()


# pattern_test=(x_min,y_min,x_max,y_max) #
# points=[Vector3(x_max,y_min,0),Vector3(x_min,y_min,0),Vector3(x_min,y_max,0),Vector3(x_max,y_max,0)]
# sommet=[(0,1,2),(0,2,3)]
# mesh0=Shape(TriangleSet(points,sommet),id=0)

# # scene_test.add(panneau_1)
# bgeom_alfalfa_HD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom"

# scene_couvert=Scene(bgeom_alfalfa_HD2)
# espe1,espe2,scene_cv=separation_scene_AF(scene_couvert)

# esp1_scaled=color(espe1,0.01) # clover 
# esp2_scaled=color(espe2,0.01)

# zmaxesp1,zminesp1=BoundingBox(esp1_scaled).getZMax(),BoundingBox(esp1_scaled).getZMin()
# zmaxesp2,zminesp2=BoundingBox(esp2_scaled).getZMax(),BoundingBox(esp2_scaled).getZMin()

# print(f"esp1 zmax {zmaxesp1}, esp1 zmin {zminesp1}")
# print(f"esp2 zmax {zmaxesp2}, esp2 zmin {zminesp2}")

# scaled_scene=color(scene_cv,0.01)
# duplicate=semis_alfalfa(scaled_scene,3,1.06,3,0.34,"sud")

# # scene_cv_scaled,soil_scaled=color(scene_cv,0.01),color(sol,0.01)
# # scene_centrated=centre_scene_scaled(scene_cv_scaled,soil_scaled)

# # scene_rotation=rotation_scene(scene_centrated)

# scene_test=Scene()
# scene_test.add(mesh0)
# # scene_test.add(panneau_1)
# scene_test.add(scaled_scene)
# # scene_test.add(duplicate)


#     # "nb_rangee":16,
#     # "nb_plant":10,
#     # "ecart_rangee":0.17,
#     # "ecart_plant":0.1}

# run=CaribuScene(scene=scene_test,light=[light_caribu],pattern=pattern_test)
# ra,agg=run.run(simplify=True,infinite=True)
# sce,value=run.plot(agg["Ei"],0,1,0.2,False)
# Viewer.display(sce)
# print(agg["Ei"])



# bgeom_as3c1=r"PAR_FSPM\Fescue-Clover\Scene\as05c1.bgeom" # MIXT 2
# bgeom_as3c3=r"PAR_FSPM\Fescue-Clover\Scene\as05c3.bgeom" # MIXT 3

# Scene_05c1=Scene(bgeom_as3c1)
# Scene_05c3=Scene(bgeom_as3c3)


# espe1,espe2,scene_cv,_=separation_scene_Autre_MIXTE(Scene_05c3)


# esp1_scaled=color(espe1,0.01) # clover 
# esp2_scaled=color(espe2,0.01)

# zmaxesp1,zminesp1=BoundingBox(esp1_scaled).getZMax(),BoundingBox(esp1_scaled).getZMin()
# zmaxesp2,zminesp2=BoundingBox(esp2_scaled).getZMax(),BoundingBox(esp2_scaled).getZMin()

# print(zmaxesp1,zmaxesp2)





if __name__=="__main__":
    
    log("MOADING PARAMETERS")
    params_panel_couvert_HD_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.11, # Y panel
    "largeur_p":0.30,# X panel
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max 4.05
    "hauteur_bas_p":4,
    "hauteur": 4,  # panel heigth min 3.35
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    params_panel_couvert_LD_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ### Ypanel
    "largeur_p":1.14,# X panel
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":3,
    "hauteur":4, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    params_panel_couvert_HD_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":0.93,
    "largeur_p":0.485,# Half panel width
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
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
    "hauteur_haut_p":4,
    "hauteur":4,# panel heigth max
    "hauteur_bas_p":4, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    log(" DATA METEO LOADING ")
    dict_date={
        "debut":"2025-09-21",
        "fin":"2025-09-21"
    }
    latitude,longitude,debut,fin=47.64, 3.256,"2025-06-21","2025-06-21" # localisation entrains-sur-Nouhain
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    data_meteo_rd.to_excel("meteo_data.xlsx",index=False)
    
    
    geom_param_alfalfa_HD={
    "nb_rangee":9,
    "nb_plant":3,
    "ecart_rangee":0.30,
    "ecart_plant":0.31
    }
    
    geom_param_alfalfa_LD={
    "nb_rangee":3,
    "nb_plant":3,
    "ecart_rangee":1.06,
    "ecart_plant":0.34
    }
    
    pattern_LD=(-1.59,-0.51,1.59,0.51)
    pattern_HD=(-1.35,-0.47,1.35,0.47)
    
    log("SCENE IMPORTATION FIRST MIXTURE ")
    
    bgeom_alfalfa_HD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom"
    bgeom_alfalfa_HD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom"
    bgeom_alfalfa_LD1=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD1-asso-luz.bgeom"
    bgeom_alfalfa_LD2=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom"
    
    
    log("SIMULATION ALFALFA_FESCUE MIXTURE WITH AND WITHOUT PANEL HD1 MOCK-UP")
    DATAFRAME= []
    DATASUMMARY=[]

    
    ALFA_HD1_mixte=(bgeom_alfalfa_HD1,params_panel_couvert_HD_sud,geom_param_alfalfa_HD,data_meteo_rd,"HD1_SUD_10DEG",True,2,False,dict_date,pattern_HD)
    ALFA_HD2_mixte=(bgeom_alfalfa_HD2,params_panel_couvert_HD_sud,geom_param_alfalfa_HD,data_meteo_rd,"HD2_SUD_10DEG",True,2,False,dict_date,pattern_HD)
    ALFA_LD1_mixte=(bgeom_alfalfa_LD1,params_panel_couvert_LD_sud,geom_param_alfalfa_LD,data_meteo_rd,"LD1_SUD_10DEG",True,2,False,dict_date,pattern_LD)
    ALFA_LD2_mixte=(bgeom_alfalfa_LD2,params_panel_couvert_LD_sud,geom_param_alfalfa_LD,data_meteo_rd,"LD2_SUD_10DEG",True,2,False,dict_date,pattern_LD)
   
    ARGS_ALFA=[ALFA_HD1_mixte,ALFA_HD2_mixte,ALFA_LD1_mixte,ALFA_LD2_mixte]
    
    log("STARTING FIRST SIMULATION ALFALFA FESCUE MIXTURE WITH AND WITHOUT PANEL")
    with Pool (processes=4) as pool:
        Results_alfa= pool.starmap(scene_direct_illumination,ARGS_ALFA)
        
    for el in Results_alfa:
        DATAFRAME.extend(el[0])
        DATASUMMARY.extend(el[1])
        
    log("SIMULATION WHEAT_PEA MIXTURE WITH AND WITHOUT PANEL")
    
    params_WHEAT_PEA_300_sud ={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":1.02, ###Y panel
    "largeur_p":0.98,# X panel
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
    "panel_opacity":1, # below 1 for panel semitransparent
    "angle_p":10
     } # angle beta_p (tilt)
    
    params_WHEAT_PEA_300_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":1.02, ### panel width
    "largeur_p":0.49,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_WHEAT_PEA_1100_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.84, ### panel width
    "largeur_p":0.98,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_WHEAT_PEA_1100_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":0.84, ### panel width
    "largeur_p":0.49,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    geom_param_WHEAT_PEA_300={
    "nb_rangee":8,
    "nb_plant":3,
    "ecart_rangee":0.34,
    "ecart_plant":0.34}
    
    geom_param_WHEAT_PEA_1100={
    "nb_rangee":8,
    "nb_plant":3,
    "ecart_rangee":0.34,
    "ecart_plant":0.42}
    
    pattern_WP_300=(-1.36,-0.51,1.36,0.51)
    pattern_WP_1100=(-1.36,-0.42,1.36,0.42)
    
    bgeom_300_DD=r"PAR_FSPM\Wheat-Pea\Scene\T2-1-170210.bgeom" # MIXT 2
    bgeom_1100_DD=r"PAR_FSPM\Wheat-Pea\Scene\T3-1-310310.bgeom" # MIXT 3
    
    log("SIMULATION WHEA-PEA MIXTURE WITH AND WITHOUT 300 AND 1100DD")
    result_300_DD_mixte=(bgeom_300_DD,params_WHEAT_PEA_300_sud,geom_param_WHEAT_PEA_300,data_meteo_rd,"WP_300_SUD_10DEG",False,2,True,dict_date,pattern_WP_300)
    result_1100_DD_mixte=(bgeom_1100_DD,params_WHEAT_PEA_1100_sud,geom_param_WHEAT_PEA_1100,data_meteo_rd,"WP_1100_SUD_10DEG",False,2,True,dict_date,pattern_WP_1100)
    
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
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4,
    "hauteur":4,# panel heigth min
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
    "hauteur_haut_p":4,
    "hauteur":4,# panel heigth max
    "hauteur_bas_p":4, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    geom_param_fescue_clover={
    "nb_rangee":16,
    "nb_plant":10,
    "ecart_rangee":0.17,
    "ecart_plant":0.1}
    
    log("LOADING BGEOM REPOSITORY")
    bgeom_as3c1=r"PAR_FSPM\Fescue-Clover\Scene\as05c1.bgeom" # MIXT 2
    bgeom_as3c3=r"PAR_FSPM\Fescue-Clover\Scene\as05c3.bgeom" # MIXT 3
    
    pattern_AS05C1=(-1.36,-0.50,1.36,0.50)
    pattern_AS05C3=(-1.36,-0.50,1.36,0.50)
    
    log("SIMULATION ")
    result_as3c1_mixte=(bgeom_as3c1,params_fescue_clover_sud,geom_param_fescue_clover,data_meteo_rd,"AS3C1_SUD_10DEG",False,2,False,dict_date,pattern_AS05C1)
    result_as3c3_mixte=(bgeom_as3c3,params_fescue_clover_sud,geom_param_fescue_clover,data_meteo_rd,"AS3C3_SUD_10DEG",False,2,False,dict_date,pattern_AS05C3)
    ARGS_FESCUE_CLOVER=[result_as3c1_mixte,result_as3c3_mixte]
    
    log("STARTING FIRST SIMULATION FOR 3 SIMULTANEOUSLY")
    with Pool(processes=2) as pool:
        Results_Fescue_clover= pool.starmap(scene_direct_illumination,ARGS_FESCUE_CLOVER)
        
    for el in Results_Fescue_clover:
        DATAFRAME.extend(el[0])
        DATASUMMARY.extend(el[1])
    
    log("COMPUTATION DATA SIMULATIONS")

    _,_=dataframe_computation(DATAFRAME,DATASUMMARY)

    log("SIMULATION TERMINATED")

    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    