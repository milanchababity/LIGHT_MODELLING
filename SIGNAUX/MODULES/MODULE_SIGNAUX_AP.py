# modules importations openealea and externals
from ast import With
from multiprocessing import pool
import openalea.plantgl.all as pgl
from openalea.plantgl.all import *
from openalea.caribu.sky_tools import GetLightsSun,Sun,Gensun
import pandas as pd 
import math
from time import time 
from pathlib import Path
import datetime
import json
from SIGNAUX.MODULES.SIGNALS_FONCTIONS import *
from multiprocessing.pool import Pool
from openalea.caribu.CaribuScene import CaribuScene

#importation internals modules


# def Simulation_signaux(dicco_paneau,day_of_year,heure,latitude,path_bgeom,patern,panel=True,suffixe ="panel"):
#     log("loading parameters")
#     t1 = time()

#     bgeom_mixte_LD2=Scene(path_bgeom)
#     log("scene separation")
#     _,_,scene_mixteLD2=fonction_separation_scene_rc_rs(bgeom_mixte_LD2)
#     log("scene scaling and application color")

#     scene_2=color(scene_mixteLD2,factor=0.01) # factor 0.01 to downscaled at m to cm
#     log("scene panel")
#     panel,poteau=type_panneau_orient_univ(dicco_paneau)
#     scene_panel=Scene(panel)
    
#     log("merge scene panel an plant")
#     scene_final=Scene()
    
#     if panel==True:
#         scene_final.add(scene_panel)
#         scene_final.add(scene_2)
#     else:
#         scene_final.add(scene_2)
        
#     log("loading datatime and sun position")
#     Latitude= latitude
#     DOY=day_of_year
#     Heure=heure
#     s=Sun.Sun()
#     s._set_pos_astro(DOY,Heure,3.14/180*Latitude)
#     sun =  Gensun.Gensun()(1, DOY, Heure, Latitude)
#     sun = GetLightsSun.GetLightsSun(sun)
#     sun_str_split = sun.split(' ')
#     x=round(float(sun_str_split[1]),2)
#     y=round(float(sun_str_split[2]),2)
#     z=round(float(sun_str_split[3]),2)
#     light = [tuple((float(sun_str_split[0]),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
#     log("configuration infinite pamaterers")
#     infinite=(patern[0],patern[1],patern[2],patern[3]) # xmin, ymin, xmax, ymax for the infinite plane
#     #infinite=(-0.53,-0.155,0.53,0.155) # xmin, ymin, xmax, ymax for the infinite plane
#     log("optical proprieties parameters loading")
#     optique=get_optical_proprieties (scene_2,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel)
#     log("caribu scene creation")
#     caribu_radiosity_LD2=CaribuScene(scene_final,opt=optique,pattern=infinite)
    
#     log("caribu radiosity simulation with infinite plane and simplification")
#     _,aggLD22=caribu_radiosity_LD2.run(direct=False,simplify=True,infinite=True)
#     log("saving data on csv file")
#     data_rc_rs =pd.DataFrame({"Triangles":aggLD22["RC"]["Eabs"].keys(),
#                               "Valeur_abs_RC":aggLD22["RC"]["Eabs"].values(),
#                               "Valeur_Ei_RC":aggLD22["RC"]["Ei"].values(),
#                               "Valeur_eabs_RS":aggLD22["RS"]["Eabs"].values(),
#                               "Valeur_Ei_RS":aggLD22["RS"]["Ei"].values()}).set_index("Triangles")
    
#     data_rc_rs["rapport_rc/rs_eabs"]=data_rc_rs["Valeur_abs_RC"]/data_rc_rs["Valeur_eabs_RS"]
#     data_rc_rs["rapport_Ei"]=data_rc_rs["Valeur_Ei_RC"]/data_rc_rs["Valeur_Ei_RS"]
#     data_rc_rs["rapport_RS/RC_abs"]=data_rc_rs["Valeur_eabs_RS"]/data_rc_rs["Valeur_abs_RC"]
#     data_rc_rs["rapport_RS/RC_Ei"]=data_rc_rs["Valeur_Ei_RS"]/data_rc_rs["Valeur_Ei_RC"]
    
#     data_rc_rs.to_csv("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/MODULES/DATAFRAME_SIGNALS/data_rc_rs_" + suffixe + ".csv")
#     log("saving data on csv file")
#     data_rc_rs =pd.DataFrame({"Triangles":aggLD22["RC"]["Eabs"].keys(),
#                               "Valeur_abs_RC":aggLD22["RC"]["Eabs"].values(),
#                               "Valeur_Ei_RC":aggLD22["RC"]["Ei"].values(),
#                               "Valeur_eabs_RS":aggLD22["RS"]["Eabs"].values(),
#                               "Valeur_Ei_RS":aggLD22["RS"]["Ei"].values()}).set_index("Triangles")
    
#     data_rc_rs["rapport_rc/rs_eabs"]=data_rc_rs["Valeur_abs_RC"]/data_rc_rs["Valeur_eabs_RS"]
#     data_rc_rs["rapport_Ei"]=data_rc_rs["Valeur_Ei_RC"]/data_rc_rs["Valeur_Ei_RS"]
#     data_rc_rs["rapport_RS/RC_abs"]=data_rc_rs["Valeur_eabs_RS"]/data_rc_rs["Valeur_abs_RC"]
#     data_rc_rs["rapport_RS/RC_Ei"]=data_rc_rs["Valeur_Ei_RS"]/data_rc_rs["Valeur_Ei_RC"]
    
#     data_rc_rs.to_csv("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/MODULES/DATAFRAME_SIGNALS/data_rc_rs_" + suffixe + ".csv")
    
#     log("mapping Rc/RS ratio")
    
#     id=list(aggLD22["RC"]["Eabs"].keys())
#     Rc_Eabs=list(aggLD22["RC"]["Eabs"].values())
#     Rs_Eabs=list(aggLD22["RS"]["Eabs"].values())
#     ratio_Eabs_Rc_Rs = [Rc / Rs if Rs != 0 else 0 for Rc, Rs in zip(Rc_Eabs, Rs_Eabs)]
#     aggLD22["Ratio_Rc_Rs"] = dict(zip(id, ratio_Eabs_Rc_Rs))
    
#     log("saving data on json file")
#     simulation_Rc_Rs_panel="C:/Users/mbabity/Documents/PlantGL/SIGNAUX/OUTPUTS_DICCT/simulation_Rc_Rs_" + suffixe + ".json"
#     with open (simulation_Rc_Rs_panel,"w",encoding="utf-8") as f:
#         json.dump(aggLD22,f,indent=4,ensure_ascii=False)
    
#     log("scene mapping ratio Rc/RS, RC Eabs and RS Eabs")
    
#     scene_rc,_=caribu_radiosity_LD2.plot(aggLD22["RC"]["Eabs"],None,None,None,False)   
#     scene_rs,_=caribu_radiosity_LD2.plot(aggLD22["RS"]["Eabs"],None,None,None,False)
#     scene_ratio_rc_rs,_=caribu_radiosity_LD2.plot(aggLD22["Ratio_Rc_Rs"],None,None,None,False)
    
    
#     if scene_rc is not None:
#         log("Saving scene_rc_" + suffixe + ".bgeom")
#         scene_rc.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_rc_" + suffixe + ".bgeom")
#     else:
#         log("scene rc empty")
        
#     if scene_rs is not None:
#         log("Saving scene_rs_" + suffixe + ".bgeom")
#         scene_rs.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_rs_" + suffixe + ".bgeom") 
#     else:
#         log("scene rs empty")
        
#     if scene_ratio_rc_rs is not None:
#         log("Saving scene_ratio_rc_rs_" + suffixe + ".bgeom")
#         scene_ratio_rc_rs.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_ratio_rc_rs_" + suffixe + ".bgeom")
#     else:
#         log("scene ratio rc/rs empty")
#     t2= time()
#     log('simulation completed for panel')
#     print(f"time taken: {t2 - t1:.2f} seconds".format(t2 - t1))


if __name__=="__main__":
    log("LOADING PARAMETERS")
    t1=time()
    
    annexe_sud={
    "debut":"2025-09-21",
    "fin":"2025-09-21",
    "tz":"Europe/Paris",
    "freq":"1h",
    "x_coord_max":0.06,
    "y_coord_max":0.62,
    "x_coord_min":1.30,
    "y_coord_min":-4.74,
    "x_coord_int":6.77,
    "y_coord_int":-1.71,
    
    "latitude": 46.433331, # lusginan"
    "longitude": 0.116670} # lusginan
    
    annexe_est={
    "debut":"2025-09-21",
    "fin":"2025-09-21",
    "tz":"Europe/Paris",
    "freq":"1h",
    "x_coord_max":-0.18,
    "y_coord_max":-6.77,
    "x_coord_min":5.20,
    "y_coord_min":2.26,
    "x_coord_int":-0.27,
    "y_coord_int":1.15,
    
    "latitude": 46.433331, # lusginan"
    "longitude": 0.116670} # lusginan
    

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
    
    log("SCENE LOGING")
    HD1_AF=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom"
    HD2_AF=r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom"
    LD1_AF=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD1-asso-luz.bgeom"
    LD2_AF=r"PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom"

    
    log("PARAMS LOADING")
    params_ALFALFAF=[(HD1_AF,params_panel_norm_sud,params_panel_norm_chapeau_est,0,annexe_sud,annexe_est,"HD1_AF"),(HD2_AF,params_panel_norm_sud,params_panel_norm_chapeau_est,0,annexe_sud,annexe_est,"HD2_AF"),(LD1_AF,params_panel_norm_sud,params_panel_norm_chapeau_est,0,annexe_sud,annexe_est,"LD1_AF"),(LD2_AF,params_panel_norm_sud,params_panel_norm_chapeau_est,0,annexe_sud,annexe_est,"LD2_AF")]
    
    log("SIMULATION STARTING")
    with Pool(processes=4) as pool:
        data_final=pool.starmap(Simulation_signaux, params_ALFALFAF)
        
    log("SIMULATION COMPLETED")
        
        


    

    
    
    
    

    



    
    
    
    