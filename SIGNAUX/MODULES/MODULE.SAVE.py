# importation data
# modules importations openealea and externals
from openalea.caribu.CaribuScene import CaribuScene
import openalea.plantgl.all as pgl
from openalea.plantgl.all import *
from openalea.caribu.sky_tools import GetLightsSun,Sun,Gensun
import pandas as pd 

from time import time 
from pathlib import Path
import datetime
import json
#importation internals modules

from SIGNAUX.MODULES.SIGNALS_FONCTIONS import fonction_separation_scene_rc_rs,color,get_optical_proprieties

## log fonction

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)
    
    

#code execution   
if __name__=="__main__":
    log("loading parameters")
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
    path=str(Path.cwd())
    
    t1 = time()
    log("importation bgeom file")
    bgeom_mixte_LD2=Scene(r'C:\Users\mbabity\Documents\PlantGL\PAR_FSPM\Fescue-Alfalfa\Scene\LD2-asso-luz.bgeom')
    
    log("scene separation")
    _,_,scene_mixteLD2=fonction_separation_scene_rc_rs(bgeom_mixte_LD2)
    
    log("scene scaling and application color")

    scene_2=color(scene_mixteLD2,factor=0.01) # factor 0.01 to downscaled at m to cm

    log("merge scene panel an plant")
    scene_final=Scene()
    scene_final.add(scene_2)
    
    log("loading datatime and sun position")
    latitude= 46.43
    DOY=172
    heure=12
    s=Sun.Sun()
    s._set_pos_astro(DOY,heure,3.14/180*latitude)
    sun =  Gensun.Gensun()(1, DOY, heure, latitude)
    sun = GetLightsSun.GetLightsSun(sun)
    sun_str_split = sun.split(' ')
    x=round(float(sun_str_split[1]),2)
    y=round(float(sun_str_split[2]),2)
    z=round(float(sun_str_split[3]),2)
    light = [tuple((float(sun_str_split[0]),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
    
    log("configuration infinite pamaterers")
    infinite=(-0.53,-0.155,0.53,0.155) # xmin, ymin, xmax, ymax for the infinite plane
    
    log("optical proprieties parameters loading")
    optique=get_optical_proprieties(scene_2,0.1,0.07,"RC",0.41,0.43,"RS",None)
    
    log("caribu scene creation")
    caribu_radiosity_LD2=CaribuScene(scene_final,opt=optique,pattern=infinite)
    
    log("caribu radiosity simulation with infinite plane and simplification")
    _,aggLD22=caribu_radiosity_LD2.run(direct=False,simplify=True,infinite=True)
    
    log("saving data on csv file")
    data_rc_rs =pd.DataFrame({"Triangles":aggLD22["RC"]["Eabs"].keys(),
                              "Valeur_abs_RC":aggLD22["RC"]["Eabs"].values(),
                              "Valeur_Ei_RC":aggLD22["RC"]["Ei"].values(),
                              "Valeur_eabs_RS":aggLD22["RS"]["Eabs"].values(),
                              "Valeur_Ei_RS":aggLD22["RS"]["Ei"].values()}).set_index("Triangles")
    
    data_rc_rs["rapport_rc/rs_eabs"]=data_rc_rs["Valeur_abs_RC"]/data_rc_rs["Valeur_eabs_RS"]
    data_rc_rs["rapport_Ei"]=data_rc_rs["Valeur_Ei_RC"]/data_rc_rs["Valeur_Ei_RS"]
    data_rc_rs["rapport_RS/RC_abs"]=data_rc_rs["Valeur_eabs_RS"]/data_rc_rs["Valeur_abs_RC"]
    data_rc_rs["rapport_RS/RC_Ei"]=data_rc_rs["Valeur_Ei_RS"]/data_rc_rs["Valeur_Ei_RC"]
    
    data_rc_rs.to_csv("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/MODULES/DATAFRAME_SIGNALS/data_rc_rs_plant.csv")
    
    log("mapping Rc/RS ratio")
    
    id=list(aggLD22["RC"]["Eabs"].keys())
    Rc_Eabs=list(aggLD22["RC"]["Eabs"].values())
    Rs_Eabs=list(aggLD22["RS"]["Eabs"].values())
    ratio_Eabs_Rc_Rs = [Rc / Rs if Rs != 0 else 0 for Rc, Rs in zip(Rc_Eabs, Rs_Eabs)]
    aggLD22["Ratio_Rc_Rs"] = dict(zip(id, ratio_Eabs_Rc_Rs))
    
    log("saving data on json file")
    simulation_Rc_Rs_panel="C:/Users/mbabity/Documents/PlantGL/SIGNAUX/OUTPUTS_DICCT/simulation_Rc_Rs_plant.json"
    with open (simulation_Rc_Rs_panel,"w",encoding="utf-8") as f:
        json.dump(aggLD22,f,indent=4,ensure_ascii=False)
    
    log("scene mapping ratio Rc/RS, RC Eabs and RS Eabs")
    
    scene_rc,_=caribu_radiosity_LD2.plot(aggLD22["RC"]["Eabs"],None,None,None,False)   
    scene_rs,_=caribu_radiosity_LD2.plot(aggLD22["RS"]["Eabs"],None,None,None,False)
    scene_ratio_rc_rs,_=caribu_radiosity_LD2.plot(aggLD22["Ratio_Rc_Rs"],None,None,None,False)
    
    
    if scene_rc is not None:
        log("Saving scene_rc_panel.bgeom")
        scene_rc.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_rc_plant.bgeom")
    else:
        log("scene rc empty")
        
    if scene_rs is not None:
        log("Saving scene_rs_panel.bgeom")
        scene_rs.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_rs_plant.bgeom") 
    else:
        log("scene rs empty")
        
    if scene_ratio_rc_rs is not None:
        log("Saving scene_ratio_rc_rs_panel.bgeom")
        scene_ratio_rc_rs.save("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/BGEOM_SIGNAL_SIMULATION/scene_ratio_rc_rs_plant.bgeom")
    else:
        log("scene ratio rc/rs empty")
    t2= time()
    log('simulation completed for plant')
    print(f"time taken: {t2 - t1:.2f} seconds".format(t2 - t1))
        
    
    
    
    