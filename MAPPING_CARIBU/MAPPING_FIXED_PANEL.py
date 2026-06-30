from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
import matplotlib.pyplot as plt
from MAPPING_CARIBU import MODULE_MAPPING
import pickle

import numpy as np
import math
from matplotlib.patches import Rectangle
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo,scene_modelling_normal
from tqdm import tqdm
import meteo
import requests 
import json
import pandas as pd 
import datetime
from multiprocessing import Pool
import pickle


def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)
### information statut


### functions


# extrate coordonate scene_panels


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
        nb_pixel_x=math.ceil((ecart_rang+larg_y_p)/resol)
        nb_pixel_y=math.ceil((ecart_p + long_x_p)/resol)

    else:
        nb_pixel_x=math.ceil((ecart_p + long_x_p)/resol)
        nb_pixel_y=math.ceil((ecart_rang+larg_y_p)/resol)
    # central mesh
    pos_x_depart=-(nb_pixel_x-1)*resol_x/2
    pos_y_depart=-(nb_pixel_y-1)*resol_y/2
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


    
def plotting_outpluts(params,dict_soil,dict_date,name):
    log("loading parameters")
    
    # orientation = params.get("orientation").lower()
    # type_panneau = params.get("type_panneau")
    # longueur_p = params.get("longueur_p")# length according axe row panel
    # largeur_p = params.get("largeur_p")# length according axe between row
    # nb_panel = params.get("nb_panel")
    # nb_rangee = params.get("nb_rangee")
    # ecart_panel = params.get("ecart_panel") # near longueur_p
    # ecart_rangee = params.get("ecart_rangee")
    # hauteur_haut_p = params.get("hauteur_haut_p")
    # hauteur_bas_p = params.get("hauteur_bas_p")
    # angle_p = params.get("angle_p")
    panel_opacity=params.get("panel_opacity")# semi transparent panel
    
    ecart_panel_sol=dict_soil.get("ecart_panel")
    ecart_rangee_sol=dict_soil.get("ecart_rangee")
    longueur_panel=dict_soil.get("longeur_panel")
    largeur_panel=dict_soil.get("largeur_panel")
    orientation_sol=dict_soil.get("orientation")
    resolution=dict_soil.get("resolution")
    
    resolution=dict_soil.get("resolution")
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    tz=dict_date.get("tz")
    freq=dict_date.get("freq")
    latitude=dict_date.get("latitude")
    longitude=dict_date.get('longitude')

    
    log("soil mesh creation")
    scene_soil=soil_mesh_triangle(ecart_panel_sol,ecart_rangee_sol,longueur_panel,largeur_panel,orientation_sol,resolution)
    scene_panel_geom,_=scene_modelling_normal.type_panneau_orient_univ(params)
    
    log("panel scene creation")
    scene_panel=MODULE_MAPPING.get_panels(scene_panel_geom)
    
    
    
    direct=True if panel_opacity==1 else False # we ue raycasting when opacity==0 and mixed radiosity (reflectance and transmittance when opacity lower than 1)
    
    
    scene_caribu=Scene([scene_panel,scene_soil])
    # lightcalculated=recup_meteo.light_caribu(debut=debut,fin=fin,freq=freq,tz=tz,latitude=latitude)
    #data_meteo=recup_meteo.dayof_year_extraction(debut,fin,freq,tz)
    data_caribu=[]
    diffus_caribu=[]
    log("importation light position and data radiation")
    
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    # mean_Rd_diffuse=data_meteo_rd["diffuse_radiation"].mean()
    cumul_Rd_diffuse=data_meteo_rd["diffuse_radiation"].sum()
    
    log("getting optics parameters")
    opt_config = {"default_band": {}}
    for z in scene_soil:
        opt_config["default_band"][z.id] = (0.06, 0)
 
    for p in scene_panel_geom:
        opt_config["default_band"][p.id] = (0.06, 1 - panel_opacity)

    log("caribu on diffuse radiation")
    sky=recup_meteo.modelize_sky(1)
    diffus=CaribuScene(scene=scene_caribu,light=sky,opt=opt_config)
    _,agg_diffus=diffus.run(simplify=True, infinite=False,direct=direct)
    data_diffuse_calculate=pd.DataFrame({
                "Triangles":agg_diffus["Ei"].keys(),
                #"times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
                "values_Ei_diffus":agg_diffus["Ei"].values()
            }).set_index("Triangles")
    diffus_caribu.append(data_diffuse_calculate)
    
    # for ind,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
    #     sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
    #     diffus=CaribuScene(scene=scene_caribu,light=sky)
    #     _,agg_diffus=diffus.run(simplify=True, infinite=False)
    #     data_diffuse_calculate=pd.DataFrame({
    #             "Triangles":agg_diffus["Ei"].keys(),
    #             "times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
    #             "values_Ei_diffus":agg_diffus["Ei"].values()
    #         }).set_index("Triangles")
    #     diffus_caribu.append(data_diffuse_calculate)
        
    log("concatenate diffuse radiation")
    #data_diffus=pd.concat(diffus_caribu,axis=0,ignore_index=False,join="outer")
    data_diffuse_calculate["Ei_sum"]=data_diffuse_calculate["values_Ei_diffus"]*cumul_Rd_diffuse
    # data_diffuse_calculate["Ei_mean"]=data_diffuse_calculate["values_Ei_diffus"]*mean_Rd_diffuse
    
    log("converting diffus values")
    datacaribu_diffuse_sum = (data_diffuse_calculate.groupby("Triangles")["Ei_sum"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))
    # datacaribu_diffuse_mean = (data_diffuse_calculate.groupby("Triangles")["Ei_mean"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))
    
    log("direct running ")
    for ind,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu,_,_=recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        if light_caribu is not None:
            cs=CaribuScene(scene_caribu,light=[light_caribu],opt=opt_config)
            _,agg=cs.run(infinite=False, simplify=True, direct=direct)
            dataframe_caribu=pd.DataFrame({
                "Triangles":agg["Ei"].keys(),
                "horaire":[doy.date_time]*len(agg["Ei"].keys()),
                "values_Ei":agg["Ei"].values()
            }).set_index("Triangles")
            data_caribu.append(dataframe_caribu)         
    ## concatenate results 
    
    
    log("computing values direct_radiation ")
    data_extract=pd.concat(data_caribu,axis=0,join="outer",ignore_index=False)
    ##add values 
    log("caclulation of sum values Ei (direct + diffuse radiation) ")
    datacaribu_final_sum = (data_extract.groupby("Triangles")["values_Ei"]).sum().mul(0.0036).to_frame(name="values_Ei")
    
    log("concat direct + diffuse")
    data_caribu_direct_diffus_sum=pd.concat([datacaribu_final_sum,datacaribu_diffuse_sum],axis=1,join="outer",ignore_index=False)
    # data_caribu_direct_diffus_mean=pd.concat([datacaribu_final_sum,datacaribu_diffuse_mean],axis=1,join="outer",ignore_index=False)
    
    data_caribu_direct_diffus_sum = data_caribu_direct_diffus_sum.reset_index()
    # data_caribu_direct_diffus_mean= data_caribu_direct_diffus_mean.reset_index()
    
    log("somming direct + diffuse radiation")
    
    data_caribu_direct_diffus_sum["Ei_total_sum"]=(data_caribu_direct_diffus_sum["values_Ei"] + data_caribu_direct_diffus_sum["Values_Ei_finale"])/len(day_of_year_len)
    # data_caribu_direct_diffus_mean["Ei_total_mean"]=(data_caribu_direct_diffus_mean["values_Ei"] + data_caribu_direct_diffus_mean["Values_Ei_finale"])/len(day_of_year_len)
    
    # data_caribu_direct_diffus["Ei_total_sum"]=data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"]
    # data_caribu_direct_diffus["Ei_total_mean"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)
    
    log("saving dataframe")
    
    data_caribu_direct_diffus_sum.to_csv("data_caribu.csv")
    scene_save=cs.scene.generate_scene(None)
    scene_save.save("caribuscene.bgeom")

    log("saving data on computer ")

    triangles_,id_geom,_,_,_= cs.as_primitive()
    
    with open(f"MAPPING_CARIBU\\PKL_FILE\\triangle_prim_{name}.pkl","wb") as f:
        pickle.dump(triangles_,f)
    with open(f"MAPPING_CARIBU\\PKL_FILE\\id_primitive_{name}.pkl", "wb") as f:
        pickle.dump(id_geom,f)
    
    scene_caribu.save(f"MAPPING_CARIBU\\bgeom_USEFUL\\scene_{name}.bgeom")

    MODULE_MAPPING.mapping_2D (dataframe_panda=data_caribu_direct_diffus_sum,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_caribu,name=name)
    data_caribu_direct_diffus_sum.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\data_{name}.csv")
    log("mapping done successfully")
    return data_caribu_direct_diffus_sum

###### clusterring ombrage 


# params_panel_norm_sud={
#     "orientation":"sud",
#     "type_panneau":"normal",
#     "longueur_p":3.54, ### panel width
#     "largeur_p":3.47,# panel length
#     "resolution_p":0.4, # for the mesh when use mesh panel fonction
#     "nb_panel":4, # the standard for simulation
#     "nb_rangee":4, # the standard for simulation
#     "ecart_panel":3.64,# about panel width to concatenate two panels
#     "ecart_rangee":9.5, # dtistance between two divide(piqué)
#     "hauteur_haut_p":4.05, # panel heigth max
#     "hauteur_bas_p":3.35, # panel heigth min
#     "panel_opacity":1, # beyon 1 for panel semitransparent
#     "angle_p":10} # angle beta_p (tilt)


# dict_soil_test_sud={
#     "ecart_panel":20,
#     "ecart_rangee":25,
#     "longeur_panel":1,
#     "largeur_panel":9,
#     "orientation":"sud",
#     "resolution":0.5,
#     "panel_opacity":1}

# log("loading date for simulation")
# dict_date_test_mai={
#     "debut":"2025-09-01",
#     "fin":"2025-09-02",
#     "tz":"Europe/Paris",
#     "freq":"1h",
#     "latitude": 43.34,
#     "longitude": 0.122}



# ajour = plotting_outpluts(params_panel_norm_sud,dict_soil_test_sud,dict_date_test_mai,"normal_sud")

# def worker_scene(dict_panel,id_panels,dict_soil,dict_date,name):
#     scene_panel,_=scene_modelling_normal.type_panneau_orient_univ(dict_panel)
#     plotting_outpluts(scene_panel,id_panels=id_panels,dict_soil=dict_soil,dict_date=dict_date,name=name)

# s=Scene(r"caribuscene.bgeom")
# Viewer.display(s)
# path_est = Scene(r"MAPPING_CARIBU\OUTPUTS_MAPPING\scene_normal_EST_5mn.bgeom")
# Viewer.display(path_est)
# scene_soil=soil_mesh_triangle(20,25,1,9,"est",0.5)
# scene_panel=MODULE_MAPPING.get_panels(path_est)
# scene_final=Scene()
# scene_final.add(scene_soil)
# scene_final.add(scene_panel)
# scene_caribu=Scene([scene_panel,scene_soil])
# Viewer.display(scene_final)


if __name__=="__main__":
    log("loading soil mesh")
    
    dict_soil_test_est={
    "ecart_panel":20,
    "ecart_rangee":35,
    "longeur_panel":4,
    "largeur_panel":9,
    "orientation":"est",
    "resolution":0.5,
    "panel_opacity":1}
    
    dict_soil_test_sud={
    "ecart_panel":20,
    "ecart_rangee":25,
    "longeur_panel":1,
    "largeur_panel":9,
    "orientation":"sud",
    "resolution":0.5,
    "panel_opacity":1}


    log("loading date for simulation")
    dict_date_test_mai={
    "debut":"2025-09-01",
    "fin":"2025-09-02",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
    
    log("loading panel parameters")
    
    params_panel_norm_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":3.54, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4.05, # panel heigth max
    "hauteur_bas_p":3.35, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    
    params_panel_norm_chapeau_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.54, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4.05, # panel heigth max
    "hauteur_bas_p":3.35, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_ajoures_normal_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":3.54, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4.05, # panel heigth max
    "hauteur_bas_p":3.35, # panel heigth min
    "panel_opacity":0.5, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
    params_panel_ajoures_chapeau_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.54, ### panel width
    "largeur_p":3.47,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":4, # the standard for simulation
    "nb_rangee":4, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":9.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4.05, # panel heigth max
    "hauteur_bas_p":3.35, # panel heigth min
    "panel_opacity":0.5, # beyon 1 for panel semitransparent
    "angle_p":10} # angle beta_p (tilt)
    
        
    log("loading arguments parameters")
    parameters = [(params_panel_norm_sud,dict_soil_test_sud,dict_date_test_mai,"normal_sud"),
            (params_panel_norm_chapeau_est,dict_soil_test_est,dict_date_test_mai,"normal_chapeau_est"),
            (params_panel_ajoures_normal_sud,dict_soil_test_sud,dict_date_test_mai,"ajoures_panel_sud"),
            (params_panel_ajoures_chapeau_est,dict_soil_test_est,dict_date_test_mai,"ajoures_panel_est")]
    
    log("starting mutltiprocess")

    with Pool (processes=4) as pool:
        mapping_fixed_panel=pool.starmap(plotting_outpluts,parameters)
        
    for element in mapping_fixed_panel:
        element.to_csv(f"data_radiation{element}.csv")

    log('simulation successfuly ...................')
        



