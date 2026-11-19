## IMPORT MODULES AND LIBRARIES
from openalea.caribu.CaribuScene import CaribuScene
from openalea.plantgl.all import *

from mpl_toolkits.axes_grid1 import make_axes_locatable
from tqdm import tqdm
import matplotlib.dates as mdates
from multiprocessing import Pool
import math 
#### modules 
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.recup_meteo import recup_direct_diffuse_mn,modelize_sky,light_caribu,recup_direct_diffuse
from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import fonction_triangle_mesh,log,type_panneau_orient_univ
from MAPPING_CARIBU.MODULE_TRACKING.solar_tracking_caribu import fonction_X,fonction_Y,type_panneau_orient_st

# data analysis 
import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd

#### scene creation 

scene =Scene(r"PAR_FSPM\Fescue-Alfalfa\Scene\HD1-asso-luz.bgeom")
Viewer.display(scene)


def intermittence_simulation (dict_panel,data_meteo,alpha_p=0,st=0,mobile=False):
    
    data_frame_meteo=recup_direct_diffuse(data_meteo.get("latitude"),data_meteo.get("longitude"),data_meteo.get("debut"),data_meteo.get("fin"))
    spot_scene=fonction_triangle_mesh(0.5,0.5,dict_panel.get("ecart_rangee"),dict_panel.get("orientation"))
    latitude=data_meteo.get("latitude")
    longitude=data_meteo.get("longitude")
    
    ### unpacking
    
    orientation=dict_panel.get("orientation")
    hauteur_p=dict_panel.get("hauteur_p")
    longueur_p=dict_panel.get("longueur_p")
    largeur_p=dict_panel.get("largeur_p")
    nb_panel=dict_panel.get("nb_panel")
    nb_rangee=dict_panel.get("nb_rangee")
    ecart_panel=dict_panel.get("ecart_panel")
    ecart_rangee=dict_panel.get("ecart_rangee")
    panel_opacity=dict_panel.get("opacity")
    
    
    direct=True if panel_opacity==1 else False
    
    if mobile == False:
        
        scene=Scene()
        paneau,_=type_panneau_orient_univ(dict_panel)
        scene.add(paneau)
        scene.add(spot_scene)

        
        opt_config = {"default_band": {}}
        for z in spot_scene:
            opt_config["default_band"][z.id] = (0.06, 0)
        for p in scene:
            opt_config["default_band"][p.id] = (0.06, 1 - panel_opacity)
        
        
        log("DIFFUSE SIMULATION")
        sky=modelize_sky(1)
        
        diffus=CaribuScene(scene=scene,light=sky,opt=opt_config)
        _,agg_diffus=diffus.run(simplify=True, infinite=False,direct=direct)
        data_diffuse_calculate=pd.DataFrame({
                "Triangles":agg_diffus["Ei"].keys(),
                #"times":[doy.date_time]*len(agg_diffus["Ei"].keys()),
                "values_Ei_diffus":agg_diffus["Ei"].values()
            }).set_index("Triangles")
        
        log("COMPUTING REAL DATA DIFFUSE")
        Data_calcul=[]
        log("COMPUTING REAL DATA DIFFUSE")
        Data_calcul=[]
        for i,row in enumerate(tqdm(data_frame_meteo.itertuples(),total=len(data_frame_meteo))):
            if row.diffuse_radiation > 0:   
                data_diffuse_hour=data_diffuse_calculate.copy()
                data_diffuse_hour["values_diffuse_brute"]=(data_diffuse_hour["values_Ei_diffus"] * float(row.diffuse_radiation))
                data_diffuse_hour["Hours"]=row.decimal_hours
                data_diffuse_hour = data_diffuse_hour.reset_index().set_index(["Hours", "Triangles"])
                Data_calcul.append(data_diffuse_hour)

        data_DIFFUSE=pd.concat(Data_calcul,axis=0,ignore_index=False,join="outer")        
        
        log("COMPUTING REAL DATA DIRECT")
        DATA_DIRECT=[]
        
        for i,row in enumerate(tqdm(data_frame_meteo.itertuples(),total=len(data_frame_meteo))):
            light,_,_=light_caribu(row.day_of_year,row.decimal_hours,latitude,row.direct_radiation,diffuse=False)
            if light is not None:
                direct=CaribuScene(scene=scene,light=[light],opt=opt_config)
                _,agg_direct=direct.run(simplify=True,infinite=False,direct=direct)
                data_direct=pd.DataFrame({
                    "Triangles":agg_direct["Ei"].keys(),
                    "Hours":[row.decimal_hours]*len(agg_direct["Ei"].keys()),
                    "values_direct_brute":agg_direct["Ei"].values() 
                }).set_index(["Hours","Triangles"])
                DATA_DIRECT.append(data_direct)
                
        dataframe_direct = pd.concat(DATA_DIRECT,axis=0,join="outer",ignore_index=False)
        
        DATA_FINAL=pd.concat([ data_DIFFUSE,dataframe_direct],axis=1,ignore_index=False,join="outer")
        
    else:
        angle_beta=[]
        hours_angle=[]
        scene_paneau=[]
        DATA_DIRECT_MOBILE=[]
        DATA_DIFFUSE_MOBILE=[]
        

        for ind,row in enumerate(tqdm(data_frame_meteo.itertuples(),total=len(data_frame_meteo))): 
            light_caribu_direct,solar_position,angle_azimuth =light_caribu(day_of_year=row.day_of_year,heure_decimaux=row.decimal_hours,latitude=latitude,intensity=row.direct_radiation,diffuse=False)
                
            if (light_caribu_direct is not None and solar_position is not None and angle_azimuth is not None):
                alpha_s,beta_s= solar_position,angle_azimuth   
                    
                B=fonction_Y(beta_s)
                A=fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
                    
                if st==0:
                    beta_p=np.atan2(B,A)
                else:
                    beta_p=np.atan2(-A,B)
                    
                beta_p = np.clip(beta_p, -np.pi/2, np.pi/2)
                        
                angle_beta.append(beta_p)
                hours_angle.append(row.decimal_hours)
                    
                scene_panel_direct,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
                    
                opt_config = {"default_band": {}}
                for z in spot_scene:
                            opt_config["default_band"][z.id] = (0.06, 0)
                for p in scene_panel_direct:
                            opt_config["default_band"][p.id] = (0.06, 1 - panel_opacity)
                    
                scene_final=Scene()
                scene_final.add(spot_scene)
                scene_final.add(scene_panel_direct)
                
                scene_paneau.append(scene_final)
                    
                caribu_direct=CaribuScene(scene=scene_final,light=[light_caribu_direct],opt=opt_config)
                _,agg_direct_st=caribu_direct.run(infinite=False, simplify=True,direct=direct)
                ST_direct=pd.DataFrame({
                        "Triangles":agg_direct_st["Ei"].keys(),
                        "Hours":[row.decimal_hours]*len(agg_direct_st["Ei"].keys()),
                        "values_Ei_direct":agg_direct_st["Ei"].values()
                    }).set_index(["Hours","Triangles"])
                DATA_DIRECT_MOBILE.append(ST_direct)
                
                sky=modelize_sky(row.diffuse_radiation)
    
                caribu_diffuse=CaribuScene(scene=scene_final,light=sky,opt=opt_config)
                _,agg_diffuse_st=caribu_diffuse.run(simplify=True,infinite=False, direct=direct)
                st_diffus=pd.DataFrame({
                        "Triangles":agg_diffuse_st["Ei"].keys(),
                        "Hours":[row.decimal_hours]*len(agg_diffuse_st["Ei"].keys()),
                        "values_Ei_diffuse":agg_diffuse_st["Ei"].values()
                    }).set_index(["Hours","Triangles"])
                    
                DATA_DIFFUSE_MOBILE.append(st_diffus)
                
        data_st_direct = pd.concat(DATA_DIRECT_MOBILE,axis=0,ignore_index=False,join="outer")
        data_st_diffus=pd.concat(DATA_DIFFUSE_MOBILE,axis=0,ignore_index=False,join="outer")
        
        DATA_FINAL=pd.concat([data_st_direct,data_st_diffus],axis=1,join="outer",ignore_index=False)
        
    if mobile ==True:
        return DATA_FINAL, [angle_beta, hours_angle, scene_paneau]
    return DATA_FINAL,scene
                    


dict_panel_st={
    "orientation":"sud",
    "longueur_p":3.54,
    "largeur_p":3.47,
    "resolution_p":0.4,
    "nb_panel":4,
    "nb_rangee":4,
    "ecart_panel":3.64,
    "ecart_rangee":9.5,
    "hauteur_p":4,
    "hauteur_haut_p":4.05,
    "hauteur_bas_p":3.55,
    "angle_p":30,
    "opacity":1,
    "st": True}



dict_meteo={
    "latitude":46.433331,
    "longitude":0.11667,
    "debut":"2025-05-15",
    "fin":"2025-05-15"
}



data,scene=intermittence_simulation(dict_panel_st,dict_meteo,alpha_p=1,st=1,mobile=False)    
data     
import matplotlib.pyplot as plt


figure, axes = plt.subplots(
    figsize=(10, 8),
    nrows=3,
    ncols=1,
    sharex=True
)

for i in range(3):

    data_f = data.xs(i, level="Triangles")

    axes[i].plot(
        data_f.index,                         # <-- Hours
        data_f["values_direct_brute"],
        label="direct",
        color="red"
    )

    axes[i].plot(
        data_f.index,                         # <-- Hours
        data_f["values_diffuse_brute"],
        label="diffuse",
        color="black"
    )

    axes[i].set_title(f"Triangle {i}")
    axes[i].set_ylabel("Ei")
    axes[i].grid()
    axes[i].legend()

axes[-1].set_xlabel("Heure")

plt.tight_layout()
plt.show()


    



                
               
                            
            
                
                
                
                    
                    
            
        
                
                
                
                
                
                
                
                
                
        
     
        
        
        
        
    
        

        
    
    

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
        
    



  
        
    





