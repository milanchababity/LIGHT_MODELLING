from openalea.plantgl.all import *
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.sky_tools import GetLightsSun,Sun,Gensun
from pathlib import Path
import pandas as pd 
import math
from time import time 
import datetime
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import type_panneau_orient_univ
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)


#step 1: get the scene 
class Scene_Signal:
    #attribute
    default_scene_path=None
    default_dicco_panneau_sud=None  
    default_dicco_paneau_est=None
    default_mixte=None  
    default_annexe_sud=None
    default_annexe_est=None
    
    def __init__(self,scene_path=default_scene_path,dicco_panneau_sud=default_dicco_panneau_sud,dicco_paneau_est=default_dicco_paneau_est,mixte=default_mixte,annexe_sud=default_annexe_sud,annexe_est=default_annexe_est):
        self.scene_path=scene_path
        self.dicco_panneau_sud=dicco_panneau_sud
        self.dicco_paneau_est=dicco_paneau_est
        self.mixte=mixte
        self.annexe_sud=annexe_sud
        self.annexe_est=annexe_est
        
    #method 1 : forcing id scene according to height of the scene and the spatial position of the scene  
    def id_scene_by_height(self, scene_scaled, id_0_10=0, id_11_20=2000000, id_21_30=3000000):
        scene_0_10=[]
        scene_11_20=[]   
        scene_21=[]
        scene_final=Scene()
        for shape in scene_scaled:
            z_min=BoundingBox(shape).getZMax()
            z_max=BoundingBox(shape).getZMin()
            z_mean=(z_min+z_max)/2
            if z_mean<=0.1:
                ob=Shape(shape.geometry,id=id_0_10)
                scene_0_10.append(ob)
                id_0_10+=1
            elif z_mean>0.1 and z_mean<=0.20:
                ob1=Shape(shape.geometry,id=id_11_20)
                scene_11_20.append(ob1)
                id_11_20+=1
            else:
                ob2=Shape(shape.geometry,id=id_21_30)
                scene_21.append(ob2)
                id_21_30+=1
        scene_1,scene_2,scene_3 = Scene(scene_0_10),Scene(scene_11_20),Scene(scene_21)
        list_scene=[scene_1,scene_2,scene_3]
        for element in list_scene:
            scene_final.add(element)
        return scene_final
    
    # method 2: scaling scene
    def scaled_fonction(self, scene, factor=0.01):
        scale_list=[]
        for obj in scene:
            scaled_final=Shape(Scaled((factor,factor,factor),obj.geometry),id=obj.id)
            scale_list.append(scaled_final)
        return Scene(scale_list)
    
    #method 3: rotation scene
    def rotation_scene(self, scene_init_scaled):
        x=[]
        for shape in scene_init_scaled:
            ob=AxisRotated(Vector3(0,0,1),math.pi/2,shape.geometry)
            obj_col=Shape(ob,Material(Color3(34, 139, 34)),id=shape.id)
            x.append(obj_col)
        return Scene(x)
    
    #method 4: centralizing scene
    def centre_scene_scaled(self, scene_scaled):
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
    
    # method 4: ducplicate scene scaled and centralized in max and min radiation position 
    def scene_max_min(self,scene_scaled,annex_coord):
        x_coord_max=annex_coord.get("x_coord_max")
        y_coord_max=annex_coord.get("y_coord_max")
        x_coord_min=annex_coord.get("x_coord_min")
        y_coord_min=annex_coord.get("y_coord_min")
        
        list_max=[]
        list_min=[]
        list_final=[]
        
        for shape in scene_scaled:
            ob=Shape(Translated(Vector3(x_coord_max,y_coord_max,0),shape.geometry),id=shape.id)
            list_max.append(ob)
            
            ob1=Shape(Translated(Vector3(x_coord_min,y_coord_min,0),shape.geometry),id=shape.id)
            list_min.append(ob1)

            # ob2=Shape(Translated(Vector3(x_coord_int,y_coord_int,0),shape.geometry),id=shape.id)
            # list_final.append(ob2)
            # id_scene +=1
        _max = Scene(list_max)
        _min = Scene(list_min)
        scene_max=self.id_scene_by_height(_max,1000000000,2000000000,3000000000)
        scene_min=self.id_scene_by_height(_min,4000000,5000000,6000000)
        
        scene_final=Scene()
        scene_final.add(scene_max)
        scene_final.add(scene_min)
        return scene_final
    #method 5: extract pattern for infinitization of the scene
    def pattern_scene(self,scene_final):
        x_min=BoundingBox(scene_final).getXMin()
        x_max=BoundingBox(scene_final).getXMax()    
        y_min=BoundingBox(scene_final).getYMin()
        y_max=BoundingBox(scene_final).getYMax()
        return (x_min,y_min,x_max,y_max)
    
    def caribu_runing(self,scene,light,sky,opt,pattern):
         # caribu diffuse running
        caribu_radiosity_diffus=CaribuScene(scene=scene,light=sky,opt=opt,pattern=pattern)
        _,agg_diffuse=caribu_radiosity_diffus.run(infinite=True,simplify=True,direct=False)
        #caribu direct running
        caribu_radiosity_dir=CaribuScene(scene=scene,light=light,opt=opt,pattern=pattern)
        _,agg_direct=caribu_radiosity_dir.run(infinite=True,simplify=True,direct=False)
        
        return agg_diffuse,agg_direct,caribu_radiosity_dir
    

def merging_scene(scene_canopy,dicco_panel):
    scene_final=Scene()
    scene_final.add(scene_canopy)
    scene_p,_=type_panneau_orient_univ(dicco_panel)
    scene_final.add(scene_p)
    return scene_final

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

def data_framing(aggegate):
    #transform dictionary to dataframe
    data_rc_rs =pd.DataFrame({"Triangles":aggegate["RC"]["Eabs"].keys(),
                                "Valeur_abs_RC":aggegate["RC"]["Eabs"].values(),
                                "Valeur_Ei_RC":aggegate["RC"]["Ei"].values(),
                                "Valeur_eabs_RS":aggegate["RS"]["Eabs"].values(),
                                "Valeur_Ei_RS":aggegate["RS"]["Ei"].values()}).set_index("Triangles")
    # calculation and operation 
    data_rc_rs["rapport_rc/rs_eabs"]=data_rc_rs["Valeur_abs_RC"]/data_rc_rs["Valeur_eabs_RS"]
    data_rc_rs["rapport_Ei"]=data_rc_rs["Valeur_Ei_RC"]/data_rc_rs["Valeur_Ei_RS"]
    data_rc_rs["rapport_RS/RC_abs"]=data_rc_rs["Valeur_eabs_RS"]/data_rc_rs["Valeur_abs_RC"]
    data_rc_rs["rapport_RS/RC_Ei"]=data_rc_rs["Valeur_Ei_RS"]/data_rc_rs["Valeur_Ei_RC"]
    return data_rc_rs

def computation_data_agg(aggLD22,aggLD21,suffixe,caribuscene,name):
    
    data_direct=data_framing(aggLD22)
    data_diffuse=data_framing(aggLD21)
    data_final= data_direct+ data_diffuse
    data_final["Treatments"]=suffixe
    
    agg_final = {"RC": 
        {"Eabs": data_final["Valeur_abs_RC"].to_dict(),"Ei": data_final["Valeur_Ei_RC"].to_dict()},
    "RS": 
        {"Eabs": data_final["Valeur_eabs_RS"].to_dict(),"Ei": data_final["Valeur_Ei_RS"].to_dict()},
    "RC/RS": 
        {"Eabs": data_final["rapport_rc/rs_eabs"].to_dict(),"Ei": data_final["rapport_Ei"].to_dict()},
    "RS/RC": 
        {"Eabs": data_final["rapport_RS/RC_abs"].to_dict(),"Ei": data_final["rapport_RS/RC_Ei"].to_dict()}}

    data_final.to_csv("C:/Users/mbabity/Documents/PlantGL/SIGNAUX/MODULES/DATAFRAME_SIGNALS/SIGNAL_SM" + suffixe + ".csv")
    
    scene_rc,_=caribuscene.plot(agg_final["RC"]["Eabs"],None,None,None,False)   
    scene_rs,_=caribuscene.plot(agg_final["RS"]["Eabs"],None,None,None,False)
    scene_ratio_rc_rs,_=caribuscene.plot(agg_final["RC/RS"]["Eabs"],None,None,None,False)
    
    #saving
    scene_rc.save(f"SIGNAUX/BGEOM_SIGNAL_SIMULATION/BGEOM_POSTERS/RED_PLOT{name}.bgeom")
    scene_rs.save(f"SIGNAUX/BGEOM_SIGNAL_SIMULATION/BGEOM_POSTERS/F_RED_PLOT{name}.bgeom")
    scene_ratio_rc_rs.save(f"SIGNAUX/BGEOM_SIGNAL_SIMULATION/BGEOM_POSTERS/RED_FARED_PLOT{name}.bgeom")
    return data_final

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

def radiation(dicco_meteo):
    latitude=dicco_meteo.get("latitude")
    longitude=dicco_meteo.get("longitude")
    debut=dicco_meteo.get("debut")
    fin=dicco_meteo.get("fin")
    hours=dicco_meteo.get("hours")
    data_meteo=recup_meteo.recup_direct_diffuse(latitude, longitude,debut,fin)
    
    # extraction at midday
    data_select=data_meteo[data_meteo["decimal_hours"]==hours]
    direct_radiation=data_select["direct_radiation"].values[0]
    diffuse_radiation=data_select["diffuse_radiation"].values[0]
    doy=data_select["day_of_year"].values[0]
    heure_dec=data_select["decimal_hours"].values[0]
    
    #light and sky coordonates(x,y,z)
    sky=recup_meteo.modelize_sky(diffuse_radiation)
    light_direct=light_position(doy,heure_dec,latitude,direct_radiation)
    return sky,light_direct
    
def simulation_on(scene_path,dicco_panel,orientation,annex_params,dicco_meteo,name,panel_option,control,suffixe,mixte=0):
    log("DATA CALCULATION STEP 1")

    def filter_scene (scene):
        scene_filter=[]
        for shp in scene:
            number=shp.id
            if number != 0:
                shape=Shape(shp.geometry,id=shp.id)
                scene_filter.append(shape)
            else:
                print("soil")
        return Scene(scene_filter)
    
    sky,light=radiation(dicco_meteo)
    scene=Scene(scene_path)
    scene_class=Scene_Signal()
    
    if mixte == 0:
        scene_scaled=scene_class.scaled_fonction(scene,0.01)
        if orientation=="sud":
            scene_canopy=scene_scaled
        else:
            scene_canopy=scene_class.rotation_scene(scene_scaled) 
             
    elif mixte ==2: #fescue _clover
        scene_filter=filter_scene(scene)
        scene_scaled=scene_class.scaled_fonction(scene_filter,0.01)
        scene_centrated=scene_class.centre_scene_scaled(scene_scaled) 
        
        if orientation=="sud":
            scene_canopy=scene_centrated
        else:
            scene_canopy=scene_class.rotation_scene(scene_centrated)
    else: # wheat_pea
        scene_filter=filter_scene(scene)
        scene_scaled=scene_class.scaled_fonction(scene_filter,0.01)
        scene_centrated=scene_class.centre_scene_scaled(scene_scaled)

        if orientation=="sud":
            scene_canopy=scene_class.rotation_scene(scene_centrated)
        else:
            scene_canopy=scene_centrated
            
    log("CREATING SCENE FOR SIMULATION STEP 2")
    
    scene_final= Scene()
    if control==False:
        scene_canopy_duplicated=scene_class.scene_max_min(scene_canopy,annex_params)
        scene_panel,_=type_panneau_orient_univ(dicco_panel)
        scene_final.add(scene_canopy_duplicated)
        scene_final.add(scene_panel)
    else:
        scene_final.add(scene_canopy)
        
    log("MERGING SCENE CANOPY AND PANEL STEP 3")
    pattern=scene_class.pattern_scene(scene_final)
    
    log("GETTING OPTICALS PROPERTIES STEP 4")
    if panel_option==True:
        optical_properties =get_optical_proprieties(scene_final,0.1,0.07,"RC",0.41,0.43,"RS",scene_panel)
    else:
        optical_properties =get_optical_proprieties(scene_final,0.1,0.07,"RC",0.41,0.43,"RS",None)
    
    log("RUNNING CARIBU DIRECT AND DIFFUSE SIMULTANEOUSLY STEP 5")
    agg_diffuse,agg_direct,class_function=scene_class.caribu_runing(scene_final,light,sky,optical_properties,pattern)

    # computation data 
    log("COMPUTING THE RESULT AND MAPPING DATA STEP 6")
    data_result=computation_data_agg(agg_diffuse,agg_direct,suffixe,class_function,name)
    log("SIMULATION FINISHED STEP 7")
    return data_result
    
 

    
      
    
    
    







