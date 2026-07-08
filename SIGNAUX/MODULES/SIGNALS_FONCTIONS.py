# importation data
from lightvegemanager.src import lightvegemanager
from openalea.plantgl.all import *
from pathlib import Path
import pandas as pd 
import math
from time import time 
import datetime
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import type_panneau_orient_univ
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo

from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun,GenSky
from openalea.caribu import plantgl_adaptor
from openalea.caribu.plantgl_adaptor import *
from openalea.caribu.CaribuScene import CaribuScene


def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

### transformed can file to scene plantgl
def can_to_scene(str_file):
    run=CaribuScene(str_file)
    run_scene=run.scene
    scene_final=run_scene.generate_scene(None)
    return scene_final

# use this fonction to fixe shape geometry downscaling
def color(scene, factor=0.01):
    scale_file = scaled_fonction(scene, factor)
    scale_f = []
    for obj in scale_file:
        new_shape = Shape(
            obj.geometry, 
            Material(Color3(34, 139, 34)), 
            id=obj.id
        )
        scale_f.append(new_shape) 
    return Scene(scale_f)


## duplicate mock ups for all scene surface 
def semis_alfalfa_rc_rs(scene_init, nb_rangee, ecart_rangee, nb_plant, ecart_plant,orientation):
    alfalfa_sowing = []
    id_plant=0
    if orientation in ["sud","nord"]:
        start_x = -((nb_rangee - 1) * ecart_rangee) / 2
        start_y = -((nb_plant - 1) * ecart_plant) / 2
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (r * ecart_rangee)
                current_y = start_y + (p * ecart_plant)
                for objet in scene_init:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=Shape(data_scaled,id=id_plant)
                    alfalfa_sowing.append(data_final)
                    id_plant+=1

    else:
        scene_int=rotation_scene(scene_init)
        start_y = -((nb_rangee - 1) * ecart_rangee) / 2
        start_x = -((nb_plant - 1) * ecart_plant) / 2 
        for r in range(nb_rangee):
            for p in range(nb_plant):
                current_x = start_x + (p * ecart_plant)
                current_y = start_y + (r * ecart_rangee)
                for objet in scene_int:
                    data_scaled = Translated(Vector3(current_x, current_y, 0), objet.geometry)
                    data_final=Shape(data_scaled,id=id_plant)
                    alfalfa_sowing.append(data_final)
                    id_plant+=1
                    
    return Scene(alfalfa_sowing)

#########################################################################################
#fonction separated scene to put the same id for each species (step 1)
def fonction_separation_scene(scene):
    luz=[]
    fet=[]
    scene_final=Scene()
    for shp in scene:
        if shp.geometry.getName()=="100000000000":
            shape_luz=Shape(shp.geometry,id=0)
            luz.append(shape_luz)
        else:
            shape_fet=Shape(shp.geometry,id=1000)
            fet.append(shape_fet)
    scene_luz=Scene(luz)
    scene_fet=Scene(fet)
    scene_final.add(scene_luz)
    scene_final.add(scene_fet)
    return scene_luz,scene_fet,scene_final

# def fonction_separation_scene_rc_rs(scene):
#     luz=[]
#     fet=[]
#     scene_final=Scene()
#     id_luz=100000000
#     id_fet=0
#     for shp in scene:
#         if shp.geometry.getName()=="100000000000":
#             shape_luz=Shape(shp.geometry,id=id_luz)
#             luz.append(shape_luz)
#             id_luz+=1
#         else:
#             shape_fet=Shape(shp.geometry,id=id_fet)
#             fet.append(shape_fet)
#             id_fet+=1
#     scene_luz=Scene(luz)
#     scene_fet=Scene(fet)
#     scene_final.add(scene_luz)
#     scene_final.add(scene_fet)
#     return scene_luz,scene_fet,scene_final


#step 2 : function creation caribu 

def caribu_runing(scene,light,sky,opt,pattern):
    # caribu diffuse running
    caribu_radiosity_diffus=CaribuScene(scene=scene,light=sky,opt=opt,pattern=pattern)
    _,agg_diffuse=caribu_radiosity_diffus.run(infinite=True,simplify=True,direct=False)
    #caribu direct running
    caribu_radiosity_dir=CaribuScene(scene=scene,light=light,opt=opt,pattern=pattern)
    _,agg_direct=caribu_radiosity_dir.run(infinite=True,simplify=True,direct=False)
    
    return agg_diffuse,agg_direct,caribu_radiosity_dir

#step 3 : function id (when all scene was setting up)  we call this function to forced again id 

def forcing_id_scene(scene):
    scene_final=[]
    id_init=0
    for shape in scene:
        ob=Shape(shape.geometry,id=id_init)
        scene_final.append(ob)
    scene_id_forced=Scene(scene_final)
    return scene_id_forced

#step 4 : scaled function to scale down 3d plant mock-up
def scaled_fonction(scene,factor=0.01):
    scale_list=[]
    for obj in scene:
        scaled_final=Shape(Scaled((factor,factor,factor),obj.geometry),id=obj.id)
        scale_list.append(scaled_final)
    return scale_list


#step 5: to rotate scene for some mixtures (wheat-pea)
def rotation_scene(scene_init):
    x=[]
    for shape in scene_init:
        ob=AxisRotated(Vector3(0,0,1),math.pi/2,shape.geometry)
        obj_col=Shape(ob,Material(Color3(34, 139, 34)),id=shape.id)
        x.append(obj_col)
    return Scene(x)

#step 6: set up opticals properties of scene 

# definition optical proprieties for each material in the scene, with possibility to add panel proprieties if there is a panel in the scene
def get_optical_proprieties(scene, abs_1, trans_1, band_name_1, abs_2, trans_2, band_name_2, panel_scene):
    opt_config = {}

    opt_config[band_name_1] = {}
    opt_config[band_name_2] = {}

    for mat in scene:
        opt_config[band_name_1][mat.id] = (abs_1, trans_1)
        opt_config[band_name_2][mat.id] = (abs_2, trans_2)

    if panel_scene is not None:
        for po in panel_scene:
            opt_config[band_name_1][po.id] = (0.06, 0)
            opt_config[band_name_2][po.id] = (0.06, 0)

    return opt_config

#step 6: to center scene for some mock-up (wheat-pea an fescue-clover)
def centre_scene_scaled(scene_scaled):
    """_summary_
We use this function for those scene which not center in (0,0)
before using this function, the scene input must to be scaled 
we can use this function for mixture Fescues-Clover and Wheat pea. they need a center function to center all scene in 0,0

    Args:
        scene_scaled (_type_): _description_
        scene scaled 

    Returns:
        _type_: _description_
        scene center 
    """
    xmax=BoundingBox(scene_scaled).getXMax()
    xmin=BoundingBox(scene_scaled).getXMin()
    ymax=BoundingBox(scene_scaled).getYMax()
    ymin=BoundingBox(scene_scaled).getYMin()
    
    dist_x=(xmax-xmin)/2
    dist_y=(ymax-ymin)/2
    tr_x=0-dist_x
    tr_y=0-dist_y
    shape_final=[]
    for shape in scene_scaled:
        shp=Shape(Translated(Vector3(tr_x,tr_y,0),shape.geometry),id=shape.id)
        shape_final.append(shp)
    scene_shape=Scene(shape_final)
    return scene_shape


#step 7 : to get pattern for the infinite zone
def extraction_infinite(scene):
    xmax=BoundingBox(scene).getXMax()
    xmin=BoundingBox(scene).getXMin()
    ymax=BoundingBox(scene).getYMax()
    ymin=BoundingBox(scene).getYMin()
    return (xmin,ymin,xmax,ymax)

# step 8 : to get the light position (for direct radiation)
def light_position(doy,heure,latitude,direct_radiation):
    DOY=doy
    Heure=heure
    s=Sun.Sun()
    s._set_pos_astro(DOY,Heure,3.14/180*latitude)
    sun =  Gensun.Gensun()(1, DOY, Heure, latitude)
    sun = GetLightsSun.GetLightsSun(sun)
    sun_str_split = sun.split(' ')
#   x=round(float(sun_str_split[1]),2)
#   y=round(float(sun_str_split[2]),2)
#   z=round(float(sun_str_split[3]),2)
    light = [tuple((float(direct_radiation),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
    return light

#step 9: to dataframe the outputs and to make some operations 
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

# #step 10 : scene constructor
# def constructor_scene(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte):
#     canopy={0:"alfalfa-fescue",1:"wheat-pea",2:"fescue-clover"}

#     scene_init=Scene(scene_path)
#     scene_id_force=forcing_id_scene(scene_init)
#     scene_scaled=color(scene_id_force,factor=0.01)
    
#     if canopy.get(mixte)==0:
#         scene_sud=scene_scaled
#         scene_est=rotation_scene(scene_scaled)
#     elif canopy.get(mixte)==2:
#         scene_centrated=centre_scene_scaled(scene_scaled) 
#         scene_sud=scene_centrated
#         scene_est=rotation_scene(scene_centrated)
#     elif canopy.get(mixte)==1:
#         scene_centrated=centre_scene_scaled(scene_scaled)
#         scene_sud=rotation_scene(scene_scaled)
#         scene_est=scene_centrated
    
#     #merge de scene  
#     scene_panel_sud,_=type_panneau_orient_univ(dicco_paneau_sud)
#     scene_panel_est,_=type_panneau_orient_univ(dicco_paneau_est)
    
#     scene_final_sud=Scene()
#     scene_final_sud.add(scene_panel_sud)
#     scene_final_sud.add(scene_sud)
    
#     scene_final_est=Scene()
#     scene_final_est.add(scene_panel_est)
#     scene_final_est.add(scene_est)
    
#     #saving scenes with and without panel
#     scene_final_sud.save("scene_final_sud.bgeom")
#     scene_final_est.save("scene_final_est.bgeom")
#     scene_sud.save("scene_sud.bgeom")   
#     scene_est.save("scene_est.bgeom")
    
#     infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel=extraction_infinite(scene_final_sud),extraction_infinite(scene_final_est),extraction_infinite(scene_sud),extraction_infinite(scene_est)
#     # getting optique properties
#     optique_panel_sud =get_optical_proprieties(infi_sud_with_panel,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel_sud)
#     optique_panel_est=get_optical_proprieties(infi_est_with_panel,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel_est)
#     optique_no_panel_sud=get_optical_proprieties(infi_sud_no_panel,0.1,0.07,"RC",0.41,0.43,"RS",None)
#     optique_no_panel_est=get_optical_proprieties(infi_est_no_panel,0.1,0.07,"RC",0.41,0.43,"RS",None)
    
#     return [scene_final_sud,scene_final_est,scene_sud,scene_est],[infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel],[optique_panel_sud,optique_panel_est,optique_no_panel_sud,optique_no_panel_est]

#step 10 : scene constructor
def scene_signal(scene_path,dicco_panneau_sud,dicco_paneau_est,mixte,annexe_sud,annexe_est):
    
    scene_init=Scene(scene_path)
    scene_id_force=forcing_id_scene(scene_init)
    scene_scaled=color(scene_id_force,factor=0.01)
    
    if mixte == 0:
        scene_sud=scene_scaled
        scene_est=rotation_scene(scene_scaled)
    elif mixte ==2:
        scene_centrated=centre_scene_scaled(scene_scaled) 
        scene_sud=scene_centrated
        scene_est=rotation_scene(scene_centrated)
    elif mixte == 1:
        scene_centrated=centre_scene_scaled(scene_scaled)
        scene_sud=rotation_scene(scene_scaled)
        scene_est=scene_centrated
    
    scene_sud_final=putting_scene(scene_sud,annexe_sud)
    scene_est_final=putting_scene(scene_est,annexe_est)

    panel_sud,_=type_panneau_orient_univ(dicco_panneau_sud)
    panel_est,_=type_panneau_orient_univ(dicco_paneau_est)
    
    scene_with_panel_sud=Scene()
    scene_with_panel_est=Scene()
    scene_no_panel_sud=Scene()
    scene_no_panel_est=Scene()
    
    scene_with_panel_sud.add(panel_sud)
    scene_with_panel_est.add(panel_est)
    scene_with_panel_sud.add(scene_sud_final)
    scene_with_panel_est.add(scene_est_final)
    
    scene_no_panel_sud.add(scene_sud_final)
    scene_no_panel_est.add(scene_est_final)
    
    infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel=extraction_infinite(scene_with_panel_sud),extraction_infinite(scene_with_panel_est),extraction_infinite(scene_no_panel_sud),extraction_infinite(scene_no_panel_est)
    
    optique_panel_sud =get_optical_proprieties(scene_with_panel_sud,0.1,0.07,"RC",0.41,0.43,"RS", panel_sud)
    optique_panel_est=get_optical_proprieties(scene_with_panel_est,0.1,0.07,"RC",0.41,0.43,"RS", panel_est)
    optique_no_panel_sud=get_optical_proprieties(scene_no_panel_sud,0.1,0.07,"RC",0.41,0.43,"RS",None)
    optique_no_panel_est=get_optical_proprieties(scene_no_panel_est,0.1,0.07,"RC",0.41,0.43,"RS",None)
    
    return [scene_with_panel_sud,scene_with_panel_est,scene_no_panel_sud,scene_no_panel_est],\
        [infi_sud_with_panel,infi_est_with_panel,infi_sud_no_panel,infi_est_no_panel],\
        [optique_panel_sud,optique_panel_est,optique_no_panel_sud,optique_no_panel_est]\


def computation_data_agg(aggLD22,aggLD21,suffixe,caribuscene,name):
    
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
    
    
def putting_scene(scene_scaled_final,annexe):
    x_coord_max=annexe.get("x_coord_max")
    y_coord_max=annexe.get("y_coord_max")
    x_coord_min=annexe.get("x_coord_min")
    y_coord_min=annexe.get("y_coord_min")
    x_coord_int=annexe.get("x_coord_int")
    y_coord_int=annexe.get("y_coord_int")
    
    scene_final_max=[]
    scene_final_min=[]
    scene_final_int=[]
    for shape in scene_scaled_final:
        ob=Shape(Translated(Vector3(x_coord_max,y_coord_max,0),shape.geometry),id=shape.id)
        scene_final_max.append(ob)
        ob1=Shape(Translated(Vector3(x_coord_min,y_coord_min,0),shape.geometry),id=shape.id)
        scene_final_min.append(ob1)
        ob2=Shape(Translated(Vector3(x_coord_int,y_coord_int,0),shape.geometry),id=shape.id)
        scene_final_int.append(ob2)
        
    scene_tot=Scene()
    scene_tot.add(Scene(scene_final_max))
    scene_tot.add(Scene(scene_final_min))   
    scene_tot.add(Scene(scene_final_int))
    return scene_tot


def Simulation_signaux(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte,annexe_sud,annexe_est,name):
    latitude =annexe_est.get("latitude")
    longitude= annexe_est.get("longitude")
    debut=annexe_est.get("debut")
    fin=annexe_est.get("fin")
    
    scene,pattern,optical=scene_signal(scene_path,dicco_paneau_sud,dicco_paneau_est,mixte,annexe_sud,annexe_est)
    data_meteo=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    print("name =", name)
    print("latitude =", latitude)
    print("longitude =", longitude)

    data_select=data_meteo[data_meteo["decimal_hours"]==12]
    direct_radiation=data_select["direct_radiation"].values[0]
    diffuse_radiation=data_select["diffuse_radiation"].values[0]
    doy=data_select["day_of_year"].values[0]
    heure_dec=data_select["decimal_hours"].values[0]
    
    print(data_select[[
        "date_time",
        "direct_radiation",
        "diffuse_radiation"
        ]])
    sky=recup_meteo.modelize_sky(diffuse_radiation)
    light_direct=light_position(doy,heure_dec,latitude,direct_radiation)

    agg_diffus_sud,agg_direct_sud,mapper=caribu_runing(scene=scene[0],light=light_direct,sky=sky,opt=optical[0],pattern=pattern[0])
    agg_diffus_est,agg_direct_est,_=caribu_runing(scene=scene[1],light=light_direct,sky=sky,opt=optical[1],pattern=pattern[1])
    agg_diffus_sud_nop,agg_direct_sud_nop,_=caribu_runing(scene=scene[2],light=light_direct,sky=sky,opt=optical[2],pattern=pattern[2])
    agg_diffus_est_nop,agg_direct_est_nop,_=caribu_runing(scene=scene[3],light=light_direct,sky=sky,opt=optical[3],pattern=pattern[3])
    
    # computation data 
    scene_sud_panel=computation_data_agg(agg_diffus_sud,agg_direct_sud,"panel_sud",mapper,name)
    scene_est_panel=computation_data_agg(agg_diffus_est,agg_direct_est,"panel_est",mapper,name)
    scene_sud_no_panel=computation_data_agg(agg_diffus_sud_nop,agg_direct_sud_nop,"nop_panel_sud",mapper,name)
    scene_est_no_panel=computation_data_agg(agg_diffus_est_nop,agg_direct_est_nop,"nop_panel_est",mapper,name)
    
    return scene_sud_panel,scene_est_panel,scene_sud_no_panel,scene_est_no_panel
###

#light vegemanager

# from lightvegemanager.src.lightvegemanager import VTK
# from lightvegemanager.src.lightvegemanager import LVM

# import os 
# scene_HD1=Scene(r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom")

# test_scene=LVM.LightVegeManager(lightmodel="riri5",main_unit="cm")
# test_scene.build(geometry={"scenes":[scene_HD1]})

# test_scene.s2v()

# def s2v_output(scene):
#     test_scene=LVM.LightVegeManager(lightmodel="riri5",main_unit="cm")
#     test_scene.build(geometry={"scenes":[scene]})   

#     return test_scene.s2v()


# scene_1,scene_2,scene_3=fonction_separation_scene(Scene(r"PAR_FSPM\Fescue-Alfalfa\Scene\HD2-asso-luz.bgeom"))

# s2v_output(scene_3)


