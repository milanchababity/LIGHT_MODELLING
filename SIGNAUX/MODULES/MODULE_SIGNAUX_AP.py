# modules importations openealea and externals
from openalea.caribu.CaribuScene import CaribuScene
import openalea.plantgl.all as pgl
from openalea.plantgl.all import *
from openalea.caribu.sky_tools import GetLightsSun,Sun,Gensun
import pandas as pd 
import math
from time import time 
from pathlib import Path
import datetime
import json
#importation internals modules
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import type_panneau_orient_univ
from SIGNAUX.MODULES.SIGNALS_FONCTIONS import fonction_separation_scene_rc_rs,color,get_optical_proprieties,forcing_id_scene,rotation_scene,centre_scene_scaled
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo

## log fonction
def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)
def extraction_infinite(scene):
    xmax=BoundingBox(scene).getXMax()
    xmin=BoundingBox(scene).getXMin()
    ymax=BoundingBox(scene).getYMax()
    ymin=BoundingBox(scene).getYMin()
    zmax=BoundingBox(scene).getZMax()
    zmin=BoundingBox(scene).getZMin()
    
    return (xmin,ymin,xmax,ymax)


params_panel_couvert={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.31, ### panel width
    "largeur_p":0.424,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)

def constructor_scene(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte):
    canopy={0:"alfalfa-fescue",1:"wheat-pea",2:"fescue-clover"}

    scene_init=Scene(scene_path)
    scene_id_force=forcing_id_scene(scene_init)
    scene_scaled=color(scene_id_force,factor=0.01)
    
    if canopy.get(mixte)==0:
        scene_sud=scene_scaled
        scene_est=rotation_scene(scene_scaled)
    elif canopy.get(mixte)==2:
        scene_centrated=centre_scene_scaled(scene_scaled) 
        scene_sud=scene_centrated
        scene_est=rotation_scene(scene_centrated)
    elif canopy.get(mixte)==1:
        scene_centrated=centre_scene_scaled(scene_scaled)
        scene_sud=rotation_scene(scene_scaled)
        scene_est=scene_centrated
    
    #merge de scene  
    scene_panel_sud,_=type_panneau_orient_univ(dicco_paneau_sud)
    scene_panel_est,_=type_panneau_orient_univ(dicco_paneau_est)
    
    scene_final_sud=Scene()
    scene_final_sud.add(scene_panel_sud)
    scene_final_sud.add(scene_sud)
    
    scene_final_est=Scene()
    scene_final_est.add(scene_panel_est)
    scene_final_est.add(scene_est)
    
    infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel=extraction_infinite(scene_final_sud),extraction_infinite(scene_final_est),extraction_infinite(scene_sud),extraction_infinite(scene_est)
    # gettind optique properties
    optique_panel_sud =get_optical_proprieties(infi_sud_with_panel,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel_sud)
    optique_panel_est=get_optical_proprieties(infi_est_with_panel,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel_est)
    optique_no_panel_sud=get_optical_proprieties(infi_sud_no_panel,0.1,0.07,"RC",0.41,0.43,"RS",None)
    optique_no_panel_est=get_optical_proprieties(infi_est_no_panel,0.1,0.07,"RC",0.41,0.43,"RS",None)
        
    return [scene_final_sud,scene_final_est,scene_sud,scene_est],[infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel],[optique_panel_sud,optique_panel_est,optique_no_panel_sud,optique_no_panel_est]


def computation_data_agg(aggLD22,aggLD21,suffixe,caribuscene,name):
    
    def data_framing(aggegate):
        data_rc_rs =pd.DataFrame({"Triangles":aggegate["RC"]["Eabs"].keys(),
                                "Valeur_abs_RC":aggegate["RC"]["Eabs"].values(),
                                "Valeur_Ei_RC":aggegate["RC"]["Ei"].values(),
                                "Valeur_eabs_RS":aggegate["RS"]["Eabs"].values(),
                                "Valeur_Ei_RS":aggegate["RS"]["Ei"].values()}).set_index("Triangles")
        
        data_rc_rs["rapport_rc/rs_eabs"]=data_rc_rs["Valeur_abs_RC"]/data_rc_rs["Valeur_eabs_RS"]
        data_rc_rs["rapport_Ei"]=data_rc_rs["Valeur_Ei_RC"]/data_rc_rs["Valeur_Ei_RS"]
        data_rc_rs["rapport_RS/RC_abs"]=data_rc_rs["Valeur_eabs_RS"]/data_rc_rs["Valeur_abs_RC"]
        data_rc_rs["rapport_RS/RC_Ei"]=data_rc_rs["Valeur_Ei_RS"]/data_rc_rs["Valeur_Ei_RC"]
        return data_rc_rs

    data_direct=data_framing(aggLD22)
    data_diffuse=data_framing(aggLD21)
    data_final=data_direct+ data_diffuse
    
    agg_final = {"RC": 
        {"Eabs": data_final["Valeur_abs_RC"].to_dict(),"Ei": data_final["Valeur_Ei_RC"].to_dict()},
    "RS": 
        {"Eabs": data_final["Valeur_eabs_RS"].to_dict(),"Ei": data_final["Valeur_Ei_RS"].to_dict()},
    "RC/RS": 
        {"Eabs": data_final["rapport_rc/rs_eabs"].to_dict(),"Ei": data_final["rapport_Ei"].to_dict()},
    "RS/RC": 
        {"Eabs": data_final["rapport_RS/RC_abs"].to_dict(),"Ei": data_final["rapport_RS/RC_Ei"].to_dict()}}

  
    data_final.to_csv("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/MODULES/DATAFRAME_SIGNALS/data_rc_rs_" + suffixe + ".csv")
    
    scene_rc,_=caribuscene.plot(agg_final["RC"]["Eabs"],None,None,None,False)   
    scene_rs,_=caribuscene.plot(agg_final["RS"]["Eabs"],None,None,None,False)
    scene_ratio_rc_rs,_=caribuscene.plot(agg_final["RC/RS"]["Eabs"],None,None,None,False)
    
    #saving
    scene_rc.save(f"SCENE_RC_{name}.bgeom")
    scene_rs.save(f"SCENE_RS_{name}.bgeom")
    scene_ratio_rc_rs.save(f"SCENE_RC/RS_{name}.bgeom")
    return data_final
    
    
def Simulation_signaux(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte,data_meteo,annexe,name):
    latitude =annexe.get("latitude")
    longitude= annexe.get("longitude")
    debut=annexe.get("debut")
    fin=annexe.get("fin")
    scene,pattern,optical=constructor_scene(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte)
    data_meteo=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    data_select=data_meteo[data_meteo["decimal_hours"]==12]
    direct_radiation=data_select["direct_radiation"].values[0]
    diffuse_radiation=data_select["diffuse_radiation"].values[0]
    doy=data_select["day_of_year"].values[0]
    heure_dec=data_select["decimal_hours"].values[0]
    
    
    sky=recup_meteo.modelize_sky(diffuse_radiation)
    
    def light_position(doy,heure,latitude):
        DOY=doy
        Heure=heure
        s=Sun.Sun()
        s._set_pos_astro(DOY,Heure,3.14/180*latitude)
        sun =  Gensun.Gensun()(1, DOY, Heure, latitude)
        sun = GetLightsSun.GetLightsSun(sun)
        sun_str_split = sun.split(' ')
        x=round(float(sun_str_split[1]),2)
        y=round(float(sun_str_split[2]),2)
        z=round(float(sun_str_split[3]),2)
        light = [tuple((float(direct_radiation),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
        return light
    
    light_direct=light_position(doy,heure_dec,latitude)

    def caribu_runing(scene,light,sky,opt,pattern):
        caribu_radiosity_diffus=CaribuScene(scene=scene,light=sky,opt=opt,pattern=pattern)
        _,agg_diffuse=caribu_radiosity_diffus(infinite=True,simplify=True,direct=False)
        caribu_radiosity_dir=CaribuScene(scene=scene,light=light,opt=opt,pattern=pattern)
        _,agg_direct=caribu_radiosity_dir(infinite=True,simplify=True,direct=False)
        return agg_diffuse,agg_direct,caribu_radiosity_dir
    
    #log("SIMULATION SCENE WITH PANEL EAST")
    agg_diffus_sud,agg_direct_sud,mapper=caribu_runing(scene=scene[0],light=light_direct,sky=sky,opt=optical[0],pattern=pattern[0])
    #log("SIMULATION SCENE WITH PANEL EAST")
    agg_diffus_est,agg_direct_est,_=caribu_runing(scene=scene[1],light=light_direct,sky=sky,opt=optical[1],pattern=pattern[1])
    #log("SIMULATION SCENE WITHOUT PANEL SOUTH")
    agg_diffus_sud_nop,agg_direct_sud_nop,_=caribu_runing(scene=scene[2],light=light_direct,sky=sky,opt=optical[2],pattern=pattern[2])
    #log("SIMULATION SCENE WITOUT PANEL EAST")
    agg_diffus_est_nop,agg_direct_est_nop,_=caribu_runing(scene=scene[3],light=light_direct,sky=sky,opt=optical[3],pattern=pattern[3])
    
    # computation data 
    scene_sud_panel=computation_data_agg(agg_diffus_sud,agg_direct_sud,"panel_sud",mapper,name)
    scene_est_panel=computation_data_agg(agg_diffus_est,agg_direct_est,"panel_est",mapper,name)
    scene_sud_no_panel=computation_data_agg(agg_diffus_sud_nop,agg_direct_sud_nop,"nop_panel_sud",mapper,name)
    scene_est_no_panel=computation_data_agg(agg_diffus_est_nop,agg_direct_est_nop,"nop_panel_est",mapper,name)
    
    return scene_sud_panel,scene_est_panel,scene_sud_no_panel,scene_est_no_panel
    




    


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
        
    params_panel_couvert_LD={
        "orientation":"sud",
        "type_panneau":"normal",
        "longueur_p":0.31, ### panel width
        "largeur_p":0.424,# panel length
        "resolution_p":0.4, # for the mesh when use mesh panel fonction
        "nb_panel":1, # the standard for simulation
        "nb_rangee":1, # the standard for simulation
        "ecart_panel":3.64,# about panel width to concatenate two panels
        "ecart_rangee":2.5, # dtistance between two divide(piqué)
        "hauteur_haut_p":4, # panel heigth max
        "hauteur_bas_p":4, # panel heigth min
        "panel_opacity":1, # beyon 1 for panel semitransparent
        "angle_p":0} # angle beta_p (tilt)
    
    params_panel_couvert_LD={
        "orientation":"est",
        "type_panneau":"chapeau",
        "longueur_p":0.31, ### panel width
        "largeur_p":0.212,# panel length
        "resolution_p":0.4, # for the mesh when use mesh panel fonction
        "nb_panel":1, # the standard for simulation
        "nb_rangee":1, # the standard for simulation
        "ecart_panel":3.64,# about panel width to concatenate two panels
        "ecart_rangee":2.5, # dtistance between two divide(piqué)
        "hauteur_haut_p":4, # panel heigth max
        "hauteur_bas_p":4, # panel heigth min
        "panel_opacity":1, # beyon 1 for panel semitransparent
        "angle_p":0} # angle beta_p (tilt)
    
    



    
    
    
    