import MAPPING_CARIBU.MODULE_SOLAR_METEO.SOLAR_POS_METEO as SOLAR_POS_METEO
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
from MAPPING_CARIBU.MODULE_TRACKING import solar_tracking_caribu        

import datetime
import time
import pandas as pd
from pathlib import Path
import math
#from data_analysis import data_analysis

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)


def solar_intensity(data_output):
    solar_i=[]
    for i in range(len(data_output)):
        intens= math.sin(math.pi*(i/len(data_output)))
        solar_i.append(intens)
    return solar_i
    
 
if __name__=="__main__":
    log("loading parameters")
    
    data_met={
    "start":"2025-05-03",
    "end":"2025-05-04",
    "tz":"Europe/Paris",
    "latitude":47.23,
    "longitude":3.30}
    # paramètres d'entrée du panneau
    
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
    
    params_panel_norm_ajour_sud={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":3.54,
    "largeur_p":3.49,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.64,
    "ecart_rangee":9.5,
    "hauteur_haut_p":4.05,
    "hauteur_bas_p":3.35,
    "panel_opacity":0.7,
    "angle_p":10}
    
    params_panel_track={
    "orientation":"est",
    "longueur_p":3.54,
    "largeur_p":4.03,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.64,
    "ecart_rangee":9.5,
    "hauteur_p":3.7,
    "angle_p":30}# angle vary according solar azimuth
    
    params_panel_chapeau_normal_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.54,
    "largeur_p":1.78,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.53,
    "ecart_rangee":9.5,
    "hauteur_haut_p":3.80,
    "hauteur_bas_p":3.30,
    "panel_opacity":1,
    "angle_p":12}
    
    params_panel_chapeau_ajoures_est={
    "orientation":"est",
    "type_panneau":"chapeau",
    "longueur_p":3.54,
    "largeur_p":1.78,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":4.64,
    "ecart_rangee":9.5,
    "hauteur_haut_p":3.80,
    "hauteur_bas_p":3.30,
    "panel_opacity":0.7,
    "angle_p":12}
    
    t1=time.time()
    params_sol={
        "resol":0.2,
        "longueur":46,
        "largeur":52,
        "ep":0.001}
    #path storage
    path=str(Path.cwd())
    
    # "
    """
    log("running simulation")
    log("solar_tracking simulation")
    solar_tr,scene_st,coordxy_st=solar_tracking_caribu.scene_carbi_run_stracking(params_sol,params_panel_track,data_met)
    solar_tr.to_csv(f"{path}\\outputs_simulation\\solar_tracking_test_45mn.csv")
    #coordxy_st.to_csv(f"{path}\\outputs_simulation\\coord_xy_st.csv")
    scene_st.save(f"{path}\\bgeom\\solar_tracking.bgeom")
    
    log("anti_tracking simulation")
    anti_tr,scene_at,coorxy_at=solar_tracking_caribu.scene_carbi_run_anti_tracking(params_sol,params_panel_track,data_met)
    anti_tr.to_csv(f"{path}\\outputs_simulation\\anti_tracking_test_45mn.csv")
    #coorxy_at.to_csv(f"{path}\\outpus_simulation\\coord_xy_at.csv")
    scene_at.save(f"{path}\\bgeom\\antitracking.bgeom")
    
    log("panel hat_est_ouest normal simulation")
    panel_hat_est,scene_panel_hat_normal_ouest,coord_xy_hat=scene_modelling_normal.scene_carbi_run(params_sol,params_panel_chapeau_normal_est,data_met)
    panel_hat_est.to_csv(f"{path}\\outputs_simulation\\panel_hat_est_45mn.csv")
    #coord_xy_hat.to_csv(f"{path}\\outpus_simulation\\coord_nor_ouest.csv")
    scene_panel_hat_normal_ouest.save(f"{path}\\bgeom\\chapeau_norm_est.bgeom")


    log("panel hat_est_ouest ajoures simulation")
    panel_hat_ajour,scene_panel_hat_ajou_ouest,coord_hat_aj_est=scene_modelling_normal.scene_carbi_run(params_sol,params_panel_chapeau_ajoures_est,data_met)
    panel_hat_ajour.to_csv(f"{path}\\outputs_simulation\\panel_hat_ajour_est_45mn.csv")
    #coord_hat_aj_est.to_csv(f"{path}\\outpus_simulation\\coord_xy_aj_est.csv")
    scene_panel_hat_ajou_ouest.save(f"{path}\\bgeom\\chapeau_ajou_est.bgeom")
"""
    log("panel normal_sud simulation")
    panel_normal_sud,scene_normal_sud,coord_n_sud=scene_modelling_normal.scene_carbi_run(params_sol,params_panel_norm_sud,data_met)
    panel_normal_sud.to_csv(f"C:\\Users\\mbabity\\Documents\\PlantGL\MAPPING_CARIBU\\OUTPUTS_MAPPING\\panel_normal_sud_5mn.csv")
    coord_n_sud.to_csv(f"C:\\Users\\mbabity\\Documents\\PlantGL\MAPPING_CARIBU\\OUTPUTS_MAPPING\\coord_xy_normal_sud_5mn.csv")
    scene_normal_sud.save(f"C:\\Users\\mbabity\\Documents\\PlantGL\MAPPING_CARIBU\\OUTPUTS_MAPPING\\scene_normal_sud_5mn.bgeom")

    #log("panel normal_sud_ajoure simulation")
    #panel_normal_ajour_sud,scene_ajou_sud,coord_sud_ajo=scene_modelling_normal.scene_carbi_run(params_sol,params_panel_norm_ajour_sud,data_met)
    #panel_normal_ajour_sud.to_csv(f"{path}\\outputs_simulation\\panel_normal_ajour_sud_carto.csv")
    #coord_sud_ajo.to_csv(f"{path}\\outpus_simulation\\coord_xy_aj_sud.csv")
    #scene_ajou_sud.save(f"{path}\\bgeom\\scene_ajou_sud.bgeom")
    
    # computation data 
    
    
    log("simulation finished")

    



    
        