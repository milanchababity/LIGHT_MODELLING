## IMPORT MODULES AND LIBRARIES
from openalea.caribu.CaribuScene import CaribuScene
from openalea.plantgl.all import *

from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm
import matplotlib.dates as mdates
from multiprocessing import Pool
import math 
#### modules 
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.recup_meteo import recup_direct_diffuse_mn,modelize_sky,light_caribu,modelize_sky,recup_direct_diffuse
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import fonction_triangle_mesh,log
from MAPPING_CARIBU.MODULE_TRACKING.solar_tracking_caribu import fonction_X,fonction_Y,type_panneau_orient_st

# data analysis 
import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd




#### imports scene 
scene_sud = r"MAPPING_CARIBU\OUTPUTS_MAPPING\scene_normal_EST_5mn.bgeom"
scene_est = r"MAPPING_CARIBU\OUTPUTS_MAPPING\scene_normal_sud_5mn.bgeom"

### 
def signature_plot(dataframe,name):
    
    grouped0=dataframe.groupby("Triangles").get_group(0)
    grouped1=dataframe.groupby("Triangles").get_group(1)
    grouped2=dataframe.groupby("Triangles").get_group(2)
    grouped_direct=[grouped0,grouped1,grouped2]
    print("graphique en cours de construction...")
    fig, ax = plt.subplots(figsize=(10, 6),ncols=1,nrows=3)
    for indgroup, group in enumerate(grouped_direct):
        if indgroup == 0:
            color="red"
        elif indgroup == 1:
            color="blue"    
        else:
            color="green"
        ax[indgroup].plot(group["date_time"],group["values_Ei_direct"],color=color,label="direct")
        ax[indgroup].plot(group["date_time"],group["values_Ei_diffus"],color="orange",ls="--",label="diffus")
        ax[indgroup].plot(group["date_time"],group["Ei_total"],color="black",label="total Ei")
        ax[indgroup].set_title(f"Triangle {indgroup}")
        ax[indgroup].set_ylabel("Ei (W/m²)")

    for i in range(3):
        ax[i].xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax[i].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax[i].tick_params (axis="x",rotation=45)
        ax[i].set_label("time")
    
    plt.tight_layout()
    fig.legend(loc="upper right")
    fig.savefig(f"intermittent_irradiance_normal_panel{name}.png")


def intermittent_simulation(path_scene,longitude, latitude,debut,fin,name="est"):
    scene_caribu=Scene(path_scene)

    #data_meteo_rd=recup_direct_diffuse(latitude,longitude)
    # data_daily=recup_direct_diffuse_mn(latitude, longitude)
    data_daily=recup_direct_diffuse(latitude,longitude,debut,fin)

    data_direct=[]
    for id, ligne in enumerate(tqdm(data_daily.itertuples(), total=data_daily.shape[0])):
        light_caribu_direct,solar_position,angle_azimuth =light_caribu(day_of_year=ligne.day_of_year,heure_decimaux=ligne.decimal_hours,latitude=43.03,intensity=ligne.direct_radiation,diffuse=False)
        if (light_caribu_direct is not None and solar_position is not None and angle_azimuth is not None):
            caribu_scene=CaribuScene(scene=scene_caribu, light =[light_caribu_direct])
            _,agg_direct=caribu_scene.run(infinite=False,simplify=True)
            dataframe_caribu=pd.DataFrame({
                    "Triangles":agg_direct["Ei"].keys(),
                    "date_time":[ligne.date_time]*len(agg_direct["Ei"].keys()),
                    "values_Ei_direct":agg_direct["Ei"].values()
                }).set_index("Triangles")
            data_direct.append(dataframe_caribu) 
            
    data_extract_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) 

    data_diffus=[]
    for ind,ligne in enumerate(tqdm(data_daily.itertuples(),total=len(data_daily))):
        sky=modelize_sky(ligne.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =light_caribu(day_of_year=ligne.day_of_year,heure_decimaux=ligne.decimal_hours,latitude=latitude,intensity=ligne.direct_radiation,diffuse=True)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            diffus=CaribuScene(scene=scene_caribu,light=sky)
            _,agg_diffus=diffus.run(simplify=True, infinite=False)
            data_diffuse_calculate=pd.DataFrame({
                    "Triangles":agg_diffus["Ei"].keys(),
                    "date_time":[ligne.date_time]*len(agg_diffus["Ei"].keys()),
                    "values_Ei_diffus":agg_diffus["Ei"].values()
                }).set_index("Triangles")
            data_diffus.append(data_diffuse_calculate)
            
    data_extract_diffuse=pd.concat(data_diffus,axis=0,join="outer",ignore_index=False) 
    
    ## concat two dataframs 
    data_final=pd.merge(data_extract_direct,data_extract_diffuse,on=["Triangles","date_time"],how="outer")
    data_final["Ei_total"]=data_final["values_Ei_direct"]+ data_final["values_Ei_diffus"]
    signature_plot(data_final,name=name)
    return data_extract_direct,data_extract_diffuse


# data_direct,data_diffuse=intermittent_simulation(path_scene=scene_est,longitude=0.122, latitude=43.03,name="EST",debut="2025-05-01",fin="2025-05-02")
# data_direct_sud,data_diffuse_sud=intermittent_simulation(path_scene=scene_sud,longitude=0.122, latitude=43.03,name="SUD",debut="2025-05-01",fin="2025-05-02")

### solar tracking 

def panel_mobile (longitude,latitude,dict_panel,soil_param,dict_date,name):
    #extraction dict_panel
    
    orientation=dict_panel.get("orientation")
    longueur_p=dict_panel.get("longueur_p")
    largeur_p=dict_panel.get("largeur_p")
    nb_panel=dict_panel.get("nb_panel")
    nb_rangee=dict_panel.get("nb_rangee")
    ecart_panel=dict_panel.get("ecart_panel")
    ecart_rangee=dict_panel.get("ecart_rangee")
    hauteur_p=dict_panel.get("hauteur_p")
    st=dict_panel.get("st")
    
    #extraction soil params
    x=soil_param.get("x")
    y=soil_param.get("y")
    
    #extraction simulation dates
    
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    
    # scene soil
    scene_soil_survey = fonction_triangle_mesh(x=x,y=y,ecart_rangee=ecart_rangee,orientation=orientation)
    scene_caribu=scene_soil_survey
    alpha_p=0
    # data meteo calculation
    # data_daily=recup_direct_diffuse_mn(latitude, longitude)
    data_daily=recup_direct_diffuse(latitude,longitude,debut,fin)
    
    data_diffus=[]
    data_direct=[]
    
    for id, ligne in enumerate(tqdm(data_daily.itertuples(), total=data_daily.shape[0])):
        sky=modelize_sky(ligne.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =light_caribu(day_of_year=ligne.day_of_year,heure_decimaux=ligne.decimal_hours,latitude=latitude,intensity=ligne.direct_radiation,diffuse=True)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            
            alpha_s,beta_s= solar_position_elev,solar_position_azim 
            B = fonction_Y(beta_s)
            A = fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)

            scene_panel,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            nouvelle_scene = scene_caribu
            nouvelle_scene.add(scene_panel)
            cs_diffus = CaribuScene(nouvelle_scene, light=sky)
            _,aggregate_diffus=cs_diffus.run(simplify=True, infinite=False)
            
            data_dif=pd.DataFrame({
                    "Triangles":aggregate_diffus["Ei"].keys(),
                    "date_time":[ligne.date_time]*len(aggregate_diffus["Ei"].keys()),
                    "values_Ei_diffus":aggregate_diffus["Ei"].values()
                }).set_index("Triangles")
            data_diffus.append(data_dif)
            
    dataframe_diffus=pd.concat(data_diffus,axis=0,ignore_index=False,join="outer")
    
     
    for ind,ligne in enumerate(tqdm(data_daily.itertuples(),total=len(data_daily))): 
        light_caribu_direct,solar_position,angle_azimuth =light_caribu(day_of_year=ligne.day_of_year,heure_decimaux=ligne.decimal_hours,latitude=latitude,intensity=ligne.direct_radiation,diffuse=False)
        ok=0
        if (light_caribu_direct is not None and solar_position is not None and angle_azimuth is not None):
            alpha_s,beta_s= solar_position,angle_azimuth   
            B=fonction_Y(beta_s)
            A=fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)

            scene_panel_direct,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            
            scene_final=scene_caribu
            scene_final.add(scene_panel_direct)
            
            cs_direct = CaribuScene(scene_final, light=[light_caribu_direct])
            _,aggregate_direct=cs_direct.run(simplify=True, infinite=False)
            data_caribu_direct=pd.DataFrame({
                    "Triangles":aggregate_direct["Ei"].keys(),
                    "date_time":[ligne.date_time]*len(aggregate_direct["Ei"].keys()),
                    "values_Ei_direct":aggregate_direct["Ei"].values()
                }).set_index("Triangles")  
            data_direct.append(data_caribu_direct)
            
    dataframe_direct=pd.concat(data_direct,axis=0,ignore_index=False,join="outer")
    
    data_final=pd.merge(dataframe_direct,dataframe_diffus,on=["Triangles","date_time"],how="outer")
    data_final["Ei_total"]=data_final["values_Ei_direct"]+ data_final["values_Ei_diffus"]
    
    signature_plot(data_final,name)
    
    return dataframe_direct,dataframe_diffus 

    
    
    ## creation of table tha exprime the ligth in percentage / maximum 
    

    
    



if __name__=="__main__":
    
    log("loading parameters")
    
    path_scene1=r"MAPPING_CARIBU\OUTPUTS_MAPPING\scene_normal_EST_5mn.bgeom"
    path_scene2=r"MAPPING_CARIBU\OUTPUTS_MAPPING\scene_normal_sud_5mn.bgeom"
    longitude=0.122
    latitude=43.03
    name1="orientation_sud"
    name2="orientation_est_ouest"
    debut="2025-05-01"
    fin="2025-05-02"
    
    log("loading dicctionary parameters")
    dict_panel_st={
    "orientation":"sud",
    "longueur_p":3.54,
    "largeur_p":4.03,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.64,
    "ecart_rangee":9.5,
    "hauteur_p":3.7,
    "angle_p":30,
    "st": True}
    
    dict_panel_at={
    "orientation":"sud",
    "longueur_p":3.54,
    "largeur_p":4.03,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.64,
    "ecart_rangee":9.5,
    "hauteur_p":3.7,
    "angle_p":30,
    "st": False}
    

    dict_date={
    "debut":"2025-05-01",
    "fin":"2025-05-02",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
        
    soil_param={
        "x":0.1,
        "y":0.1   
    }
    name3="solar_tracking"
    name4="anti_tracking"
    
    log("loading arguments")
    args_fixe=[
        (path_scene1,longitude,latitude,debut,fin,name1),
        (path_scene2,longitude,latitude,debut,fin,name2)
        
    ]
    args_mobile=[
        (longitude,latitude,dict_panel_st,soil_param,dict_date,name3),
        (longitude,latitude,dict_panel_at,soil_param,dict_date,name4)
    ]
    
    # log(" simulation fixe panel")
    # with Pool (processes=2) as pool:
    #     result_fixe=pool.starmap(intermittent_simulation,args_fixe)
    
    log("simulation mobile panels")
    with Pool (processes=2) as pool:
        result_mobile =pool.starmap(panel_mobile,args_mobile)
        
    # for data in result_fixe:
    #     data.to_csv(f"data{data}.csv")
    for data_mobile in result_mobile:
        data_mobile.to_csv(f"data{data_mobile}.csv")
        
    



  
        
    





