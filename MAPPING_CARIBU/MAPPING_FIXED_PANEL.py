from openalea.caribu.CaribuScene import CaribuScene,domain_mesh
from openalea.plantgl.all import *
import matplotlib.pyplot as plt
from MAPPING_CARIBU import MODULE_MAPPING
import pickle
import numpy as np
import math
from matplotlib.patches import Rectangle
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo,scene_modelling_normal
from tqdm import tqdm

import pandas as pd 
import datetime
from multiprocessing import Pool
import pickle
import os 


def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)


# fonction extraction x,y,z of scene 
def extraction_x_y(primitive_triangle):
    """_summary_
    Args:
        primitive_triangle (_type_): _from primitive geometry we extract (x1,x2,x3) and (y1,y2,y3)_
    Returns:
        _type_: _description_
    """
    coord_x=[]
    coord_y=[]
    for element in primitive_triangle:
        if element[0][2] == 0:
            x=(element[0][0],element[1][0],element[2][0])
            y=(element[0][1],element[1][1],element[2][1])
            coord_x.append(x)
            coord_y.append(y)
    return coord_x,coord_y


### plotting triangles 
def plotting_triangle(coord_x,coord_y):
    triangle=[]
    fig,axe=plt.subplots(figsize=(10,10))
    for i in range(len(coord_x)):
        add=tri.Triangulation(coord_x[i],coord_y[i])
        triangle.append(add)
        axe.triplot(add)
    axe.autoscale_view()
    axe.set_aspect('equal')
    return axe,triangle

### importation module sol normal panel

def soil_mesh_triangle(ecart_p,ecart_rang,long_x_p,larg_y_p,orientation="sud",resol=0.01):
    """_summary_
    Args:
        ecart_p (_type_): _panle ecart_
        ecart_rang (_type_): _rang distance_
        long_x_p (_type_): _panel length_
        larg_y_p (_type_): _panel width_
        orientation (str, optional): _description_. Defaults to "sud".
        resol (float, optional): _description_. Defaults to 0.01.
    Returns:
        _type_: _description_
    """
    resol_x=resol
    resol_y=resol
    points =[Vector3(-resol_x/2,-resol_y/2,0),Vector3(resol_x/2,-resol_y/2,0),Vector3(resol_x/2,resol_y/2,0),Vector3(-resol_x/2,resol_y/2,0)]
    sommet=[(0,1,2),(0,2,3)]
    triangle_unit=TriangleSet(points,sommet)
    
    if orientation =="sud":
        nb_pixel_x=math.ceil((ecart_rang + larg_y_p)/resol)
        nb_pixel_y=math.ceil((ecart_p + long_x_p)/resol)

    else:
        nb_pixel_x=math.ceil((ecart_p + long_x_p)/resol)
        nb_pixel_y=math.ceil((ecart_rang + larg_y_p)/resol)
    # central mesh
    pos_x_depart=-(nb_pixel_x-1)* resol_x/2
    pos_y_depart=-(nb_pixel_y-1)* resol_y/2
    id_sol=0
    maillage=[]
    for i in range(nb_pixel_x):
        for j in range(nb_pixel_y):
            x_final = pos_x_depart + (resol_x * i)
            y_final = pos_y_depart + (resol_y * j)
            objet=Shape(Translated(Vector3(x_final,y_final,0),triangle_unit),id=id_sol)
            maillage.append(objet)
            id_sol+=1
    maillage_col=[Shape(maille.geometry, Material(Color3(255,255,255)), id=maille.id) for maille in maillage]
    return Scene(maillage_col)


def FIXED_SIMULATION_V1(params,dict_soil,dict_date,name):
    log("STEP 1/9: CHARGING PARAMETERS SIMULATION")
    
    panel_opacity=params.get("panel_opacity")
    resolution=dict_soil.get("resolution")
    
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    tz=dict_date.get("tz")
    freq=dict_date.get("freq")
    latitude=dict_date.get("latitude")
    longitude=dict_date.get('longitude')
    
    
    nb_panel=params.get("nb_panel")
    nb_rangee=params.get("nb_rangee")
    ecart_rangee=params.get("ecart_rangee")
    orientation=params.get("orientation")
    largeur_p=params.get("largeur_p")
    
    
    log("STEP 2/9: SOIL AND PANEL SCENE CREATION")
    scene_soil= MODULE_MAPPING.soil_mesh_triangleV2(nb_panel,nb_rangee,ecart_rangee,largeur_p,orientation,resolution)
    scene_panel_geom,_=scene_modelling_normal.type_panneau_orient_univ(params)
    
    direct=True if panel_opacity==1 else False # we ue raycasting when opacity==0 and mixed radiosity (reflectance and transmittance when opacity lower than 1)
    scene_caribu=Scene([scene_panel_geom,scene_soil])
    pattern_pv= (BoundingBox(scene_soil).getXMin(),BoundingBox(scene_soil).getYMin(),BoundingBox(scene_soil).getXMax(),BoundingBox(scene_soil).getYMax())

    data_caribu=[]
  
    log("STEP 3/9: DATA METEO FORECASTING")
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    cumul_Rd_diffuse=data_meteo_rd["diffuse_radiation"].sum()
    
    log("STEP 4/9: OPTICALS PARAMETERS CONFIGURATIONS")
    opt_config = {"default_band": {}}
    
    for z in scene_soil:
        opt_config["default_band"][z.id] = (0.06, 0)
 
    for p in scene_panel_geom:
        opt_config["default_band"][p.id] = (0.06, 1 - panel_opacity)

    log("STEP 5/9: SIMULATION DIFFUSE RADIATION")
    sky=recup_meteo.modelize_sky(1)
    diffus=CaribuScene(scene=scene_caribu,light=sky,opt=opt_config,pattern=pattern_pv)
    _,agg_diffus=diffus.run(simplify=True, infinite=True,direct=direct)
    data_diffuse_calculate=pd.DataFrame({
                "Triangles":agg_diffus["Ei"].keys(),
                "values_Ei_diffus":agg_diffus["Ei"].values()
            }).set_index("Triangles")
 
    log("STEP 6/9: COMPUTATION DIFFUSE RADIATIONS")
    data_diffuse_calculate["Ei_sum"] = (data_diffuse_calculate["values_Ei_diffus"] * cumul_Rd_diffuse) 
    datacaribu_diffuse_sum = (data_diffuse_calculate.groupby("Triangles")["Ei_sum"].sum().to_frame(name="Values_Ei_finale"))
    
    log("STEP 7/9: COMPUTATION DIRECT RADIATION ")
    for _ , doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            cs=CaribuScene(scene_caribu,light=[light_caribu],opt=opt_config,pattern=pattern_pv)
            _,agg=cs.run(infinite=True, simplify=True, direct=direct)
            dataframe_caribu=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[doy.date_time]*len(agg["Ei"].keys()),
                "values_Ei":agg["Ei"].values()
            }).set_index("Triangles")
            data_caribu.append(dataframe_caribu)  
            
    data_extract=pd.concat(data_caribu,axis=0,join="outer",ignore_index=False)  
    datacaribu_final_sum = (data_extract.groupby("Triangles")["values_Ei"]).sum().to_frame(name="values_Ei") 
    data_caribu_direct_diffus_sum=pd.concat([datacaribu_final_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    data_caribu_direct_diffus_sum = data_caribu_direct_diffus_sum.reset_index() 
    data_caribu_direct_diffus_sum["Ei_total_sum"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])/len(day_of_year_len)   

    log("STEP 8/9: SIMULATION DIRECT AND DIFFUSE CONTROL SPOT")
    scene_control=scene_modelling_normal.scene_consrtructor_contrl(1)
    opt_conf_cont={"default_band":{scene_control[0].id:(0.06,0)}}
    pattern_contr=(BoundingBox(scene_control).getXMin(),BoundingBox(scene_control).getYMin(),BoundingBox(scene_control).getXMax(),BoundingBox(scene_control).getYMax())
    diffuse_control=CaribuScene(scene=scene_control,light=sky,opt=opt_conf_cont,pattern=pattern_contr)
    _,agg_control=diffuse_control.run(simplify=True,infinite=True,direct=True)
    dataframe_control_diffuse=pd.DataFrame({
                "Triangles":agg_control["Ei"].keys(),
                "values_Ei_diffus":agg_control["Ei"].values()
            }).set_index("Triangles")
    
    dataframe_control_diffuse["diffuse_radiation_value"]=(dataframe_control_diffuse["values_Ei_diffus"] * cumul_Rd_diffuse)/len(day_of_year_len)
    
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
            
    log("STEP 9/9: COMPUTING OUTPUTS SIMULATION")
    triangles_,id_geom,_,_,_= cs.as_primitive()
    
    data_direct_cont=pd.concat(data_control_direct,axis=0,join="outer",ignore_index=False)
    data_direct_cont_sum=(data_direct_cont.groupby("Triangles")["values_Ei"].sum().to_frame(name="values_Ei_control"))
    data_cont_final=pd.concat([data_direct_cont_sum,dataframe_control_diffuse],axis=1,join="outer",ignore_index=False)
    data_cont_final["values_totale"]=(data_cont_final["values_Ei_control"] + data_cont_final["diffuse_radiation_value"])/ len(day_of_year_len)
    
    scene_caribu.save("FIXED_PANEL.bgeom")

    # CREATE 3D SCENE FOR MAPPING 
    MODULE_MAPPING.mapping_2D(dataframe_panda=data_caribu_direct_diffus_sum,data_contr=data_cont_final,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_caribu,name=name)
    
    log(" SIMULATION SUCCESSFULLY")
    
    data_caribu_direct_diffus_sum.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\{name}.csv")

    return data_caribu_direct_diffus_sum




if __name__=="__main__":

    dict_soil_st ={
        "nb_panel":4,
        "nb_rangee":4,
        "largeur_panel":3.54,
        "orientation":"est",
        "resolution":0.5}

    dict_date_test_mai={
    "debut":"2025-06-25",
    "fin":"2025-06-25",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 46.433331, # lusginan"
    "longitude": 0.116670} # lusginan
    
    params_panel_norm_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":3.2, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.2,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_p":3.25,
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_norm_chapeau_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.2, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.2,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_p":3.25,
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_ajoures_normal_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":3.2, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.2,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_p":3.25,
    "panel_opacity":0.5, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_ajoures_chapeau_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.2, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.2,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_p":3.25,
    "panel_opacity":0.5, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
        
    # log("loading arguments parameters")
    # parameters = [(params_panel_norm_sud,dict_soil_test_sud,dict_date_test_mai,"normal_sud"),
    #         (params_panel_norm_chapeau_est,dict_soil_test_est,dict_date_test_mai,"normal_chapeau_est"),
    #         (params_panel_ajoures_normal_sud,dict_soil_test_sud,dict_date_test_mai,"ajoures_panel_sud"),
    #         (params_panel_ajoures_chapeau_est,dict_soil_test_est,dict_date_test_mai,"ajoures_panel_est")]
    
    # log("starting mutltiprocess")

    # with Pool (processes=4) as pool:
    #     mapping_fixed_panel=pool.starmap(plotting_outpluts,parameters)
        
    # for element in mapping_fixed_panel:
    #     element.to_csv(f"data_radiation{element}.csv")
    log("starting simulation for normal panel")
    mapping_south_panel=FIXED_SIMULATION_V1(params_panel_norm_sud,dict_soil_st,dict_date_test_mai,"FIXED_SUD_TEST")
    
    # # log("starting simulation for normal panel chapeau")
    # # mapping_east_panel=plotting_outpluts(params_panel_norm_chapeau_est,dict_soil_test_est,dict_date_test_mai,"normal_chapeau_est")

    # log('simulation successfuly ...................')
        



