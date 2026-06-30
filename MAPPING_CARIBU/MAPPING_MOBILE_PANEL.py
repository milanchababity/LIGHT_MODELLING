from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import math
from matplotlib.patches import Rectangle
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo
from tqdm import tqdm
import meteo
import requests 
import json
import pandas as pd 
import datetime
import multiprocessing
from mpl_toolkits.axes_grid1 import make_axes_locatable
from MAPPING_CARIBU.MODULE_TRACKING.solar_tracking_caribu import fonction_X,fonction_Y,type_panneau_orient_st
from MAPPING_CARIBU import MODULE_MAPPING

def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)
### information statut


### functions
## getting uniquely the panels of the scene
def get_panels(scene):
    """_summary_
    Args:
        scene (_panel_): _for plotting in matplotlib_
    Returns:
        _scene_panel plangl_: _description_
    """
    panels=[]
    soil=[]
    for shape in scene:
        if shape.id== 3000000:
            panels.append(shape)
        else:
            soil.append(shape)
    return Scene(panels)

# extrate coordonate scene_panels
def plotting_panels(scene):
    """_summary_
    Args:
        scene (_type_): _this function generate the coordonate x,y z for plotting panel on matplotlib_
    Returns:
        _type_: _description_
    """
    scene_f= get_panels(scene)
    list_rectangle=[]
    for element in scene_f:
        xmin=BoundingBox(element).getXMin()
        xmax=BoundingBox(element).getXMax()
        ymin=BoundingBox(element).getYMin()
        ymax=BoundingBox(element).getYMax() 
        rectangle=Rectangle((ymin,xmin),ymax-ymin,xmax-xmin,edgecolor='black',facecolor='none')
        list_rectangle.append(rectangle)
    return list_rectangle

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

#### selected values froms soils mesh
def soils_values (dataframe_panda,id_panel=3000000):
    """_summary_
    Args:
        aggregated (_type_): _outputs caribu_
        id_panel (_type_): _id panels numbers = 30000_
    Returns:
        _type_: _description_ get those values for soil mesh 
        dict with id was kept in order to link with values
    """
    if dataframe_panda.get("Ei_total_sum") is not None:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_sum"]))
    else:
        dico_value_calculare = dict(zip(dataframe_panda["Triangles"],dataframe_panda["Ei_total_mean"]))
    return {key:val for key, val in dico_value_calculare.items() if key != id_panel}

def coordinate_x_y(agg, id_panel, primitive_tri, id_primitive):
    coord_x = []
    coord_y = []
    values_Ei = []
    for idx, val in zip(id_primitive, primitive_tri):

        if idx != int(id_panel):

            if idx in agg:
                x = (val[0][0], val[1][0], val[2][0])
                y = (val[0][1], val[1][1], val[2][1])
                coord_x.append(x)
                coord_y.append(y)
                values_Ei.append(agg[idx])
    return coord_x, coord_y, values_Ei


def simulation_panel_mobile(dict_panel,dict_soil,id_panels,dict_date,name):
    log("upload parameters")
    orientation=dict_panel.get("orientation")
    longueur_p=dict_panel.get("longueur_p")
    largeur_p=dict_panel.get("largeur_p")
    nb_panel=dict_panel.get("nb_panel")
    nb_rangee=dict_panel.get("nb_rangee")
    ecart_panel=dict_panel.get("ecart_panel")
    ecart_rangee=dict_panel.get("ecart_rangee")
    hauteur_p=dict_panel.get("hauteur_p")
    st=dict_panel.get("st")
    
    log("loading dict soil")
    
    ecart_panel_sol=dict_soil.get("ecart_panel")
    ecart_rangee_sol=dict_soil.get("ecart_rangee")
    longueur_panel=dict_soil.get("longeur_panel")
    largeur_panel=dict_soil.get("largeur_panel")
    orientation_sol=dict_soil.get("orientation")
    resolution=dict_soil.get("resolution")
    
    log("dict_date")
    debut=dict_date.get('debut')
    fin=dict_date.get("fin")
    tz=dict_date.get("tz")
    freq=dict_date.get("freq")
    latitude=dict_date.get("latitude")
    longitude=dict_date.get('longitude')
    
    ###### fonction solar tracking
    log("soil scene")
    scene_soil=soil_mesh_triangle(ecart_panel_sol,ecart_rangee_sol,longueur_panel,largeur_panel,orientation_sol,resolution)
    log("Scene caribu ")
    scene_caribu=scene_soil
    log("importation day of calculation direct and diffuse calculation")
    
    day_of_year_len=recup_meteo.compute_day_of_years(debut,fin)
    data_meteo_rd=recup_meteo.recup_direct_diffuse(latitude,longitude,debut,fin)
    
    log("caribu on diffuse radiation")
    
    azimuth_angle ={
        "sud":0,
        "nord":180,
        "est":-90,
        "ouest":90
    }
    alpha_p=azimuth_angle.get("orientation",0)
    
    
    log("data_stockage scene")
    data_diffus=[]
    data_direct=[]
    angle_calc=[]
    hours_diffus=[]
    hours_direct=[]
    scene_panneau=[]
    
    for ind,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))):
        sky=recup_meteo.modelize_sky(doy.diffuse_radiation)
        sun,solar_position_elev,solar_position_azim =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=True)
        if (sun is not None and solar_position_elev is not None and solar_position_azim is not None):
            
            alpha_s,beta_s= solar_position_elev,solar_position_azim 
            B = fonction_Y(beta_s)
            A = fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)
            angle_calc.append(beta_p)
            angle_calc.append(beta_p)
            hours_diffus.append(doy.decimal_hours)
            scene_panel,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            nouvelle_scene = scene_caribu

            nouvelle_scene.add(scene_panel)
            scene_panneau.append(nouvelle_scene)
            
            cs_diffus = CaribuScene(nouvelle_scene, light=sky)
            _,aggregate_diffus=cs_diffus.run(simplify=True, infinite=False)
            
            data_dif=pd.DataFrame({
                    "Triangles":aggregate_diffus["Ei"].keys(),
                    "horaire":[doy.decimal_hours]*len(aggregate_diffus["Ei"].keys()),
                    "values_Ei":aggregate_diffus["Ei"].values()
                }).set_index("Triangles")
            data_diffus.append(data_dif)
        
    log("concatenate diffuse radiation")
    dataframe_diffus=pd.concat(data_diffus,axis=0,ignore_index=False,join="outer") 
     
    log("converting diffus values")
    datacaribu_diffuse = (dataframe_diffus.groupby("Triangles")["values_Ei"].sum().mul(0.0036).to_frame(name="Values_Ei_finale"))
    
    log("direct running ")
    
    for ind,doy in enumerate(tqdm(data_meteo_rd.itertuples(),total=len(data_meteo_rd))): 
        light_caribu_direct,solar_position,angle_azimuth =recup_meteo.light_caribu(day_of_year=doy.day_of_year,heure_decimaux=doy.decimal_hours,latitude=latitude,intensity=doy.direct_radiation,diffuse=False)
        ok=0
        if (light_caribu_direct is not None and solar_position is not None and angle_azimuth is not None):
            alpha_s,beta_s= solar_position,angle_azimuth   
            B=fonction_Y(beta_s)
            A=fonction_X(alpha_s,beta_s, alpha_p=alpha_p)
            if st==True:
                beta_p=np.atan2(B,A)
            else:
                beta_p=np.atan2(-A,B)
            
            # init=beta_p=np.atan2(B,A)
            # if st==True:
            #     beta_p=init
            # else:
            #     beta_p=init+math.degrees(90)
            angle_calc.append(beta_p)
            angle_calc.append(beta_p)
            hours_direct.append(doy.decimal_hours)
            
            scene_panel_direct,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=beta_p)
            
            scene_final=scene_caribu
            scene_final.add(scene_panel_direct)
            scene_panneau.append(scene_final)
            
            cs_direct = CaribuScene(scene_final, light=[light_caribu_direct])
            _,aggregate_direct=cs_direct.run(simplify=True, infinite=False)
            data_caribu_direct=pd.DataFrame({
                    "Triangles":aggregate_direct["Ei"].keys(),
                    "horaire":[doy.date_time]*len(aggregate_direct["Ei"].keys()),
                    "values_Ei":aggregate_direct["Ei"].values()
                }).set_index("Triangles")
            
            data_direct.append(data_caribu_direct)
            if ok==0:
                triangles_,id_geom,_,_,_= cs_direct.as_primitive()
            ok+=1
      
    log("computing values direct_radiation ")
    data_extract_direct=pd.concat(data_direct,axis=0,join="outer",ignore_index=False) 
    
    log("caclulation of sum values Ei (direct + diffuse radiation) ")
    datacaribu_final_sum = (data_extract_direct.groupby("Triangles")["values_Ei"].sum().mul(0.0036).to_frame(name="values_Ei"))
   
    log("concat direct + diffuse")
    data_caribu_direct_diffus=pd.concat([datacaribu_final_sum,datacaribu_diffuse],axis=1,join="outer",ignore_index=False)
    data_caribu_direct_diffus = data_caribu_direct_diffus.reset_index()
    
    log("somming direct + diffuse radiation")
    
    data_caribu_direct_diffus["Ei_total_sum"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)
    #data_caribu_direct_diffus["Ei_total_mean"]=(data_caribu_direct_diffus["values_Ei"] + data_caribu_direct_diffus["Values_Ei_finale"])/len(day_of_year_len)
    
    #doc_mapper=[data_caribu_direct_diffus,data_caribu_direct_diffus]
    
    log("scene_construction")
    scene_demonstration,_ =type_panneau_orient_st(orientation=orientation,hauteur_p=hauteur_p,longueur_p=longueur_p,largeur_p=largeur_p,nb_panel=nb_panel,nb_rangee=nb_rangee,ecart_panel=ecart_panel,ecart_rangee=ecart_rangee,angle_p=0)
    
    log("mapping data ")
    x=0
    
    MODULE_MAPPING.mapping_2D (dataframe_panda=data_caribu_direct_diffus,primitive_tri=triangles_,id_primitive=id_geom,scene_save=scene_demonstration,name=name)
    # for data in doc_mapper:
    #     log("extraction data Ei for mapping ")
    #     agg_sum=soils_values (data,id_panel=3000000)
    #     # mapping section  
    #     log("extraction triangles geoms")   
        
    #     # triangles_,id_geom,_,_,_= cs_direct.as_primitive()
    #     cor_x, cor_y, values = coordinate_x_y(agg_sum, id_panels, triangles_, id_geom)
    #                 #working with numpy to flatten list
    #     x_flat = np.array(cor_x).flatten()
    #     y_flat = np.array(cor_y).flatten()
    #                 # get the sommets
    #     num_triangles = len(cor_x)
    #     triangles_indices = np.arange(num_triangles * 3).reshape((num_triangles, 3))
    #                 # for mutpliying values for 3 sommets
    #     z_flat = np.repeat(values, 3)
    #                 # triangulation on matplotlib
                    
    #             ### values fixations
    #     val_min=0
    #     val_max=25
    #     level= np.linspace(val_min,val_max,20)
        
    #     triangulation_parfaite = tri.Triangulation(y_flat,x_flat, triangles=triangles_indices)
    #     figure,axe=plt.subplots(figsize=(15, 15))
    #                 # triangle countourung
    #     log("mapping colorations")
        
    #     contour = axe.tricontourf(triangulation_parfaite, z_flat, levels=level, vmin=val_min,vmax=val_max, cmap='jet')
    #     divider = make_axes_locatable(axe)
    #     cax = divider.append_axes("right",size="2%",pad=0.5)
        
    #     rectangle=plotting_panels(scene_demonstration)
    #     for rect in rectangle:
    #         axe.add_patch(rect)
    #     axe.autoscale_view()
    #     axe.set_aspect('equal')
    #     cbar = figure.colorbar(contour, cax=cax,extend="max")
    #     cbar.set_label("Soil_irradiance(Ei)")
    #     axe.set_xlabel("East-west")
    #     axe.set_ylabel("South-North")
    #     axe.set_title(f"Light shelttering_{doy.hours}")
    #     axe.invert_xaxis()
    #     plt.tight_layout()
    #             # axe.invert_yaxis()
    #     plt.savefig(f"MAPPING_CARIBU/GIF_MAPPING/mapping_figure{x}{name}.png", dpi=800)
    #     plt.close()
    #     x+=1
    log("mapping done successfully")
    data_caribu_direct_diffus.to_csv(f"MAPPING_CARIBU\\RAW_CSV\\{name}.csv")
    return data_caribu_direct_diffus



# dict_panel_st ={
#     "orientation":"est",
#     "longueur_p":3.54,
#     "largeur_p":4.03,
#     "resolution_p":0.4,
#     "nb_panel":4,
#     "nb_rangee":4,
#     "ecart_panel":3.64,
#     "ecart_rangee":9.5,
#     "hauteur_p":3.7,
#     "angle_p":30,
#     "st": True}
    
# dict_panel_at ={
#     "orientation":"est",
#     "longueur_p":3.54,
#     "largeur_p":4.03,
#     "resolution_p":0.4,
#     "nb_panel":4,
#     "nb_rangee":4,
#     "ecart_panel":3.64,
#     "ecart_rangee":9.5,
#     "hauteur_p":3.7,
#     "angle_p":30,
#     "st": False}
        
# dict_soil_st ={
#         "ecart_panel":20,
#         "ecart_rangee":25,
#         "longeur_panel":1,
#         "largeur_panel":9,
#         "orientation":"est",
#         "resolution":0.5}

# dict_date_test_janv={
#     "debut":"2025-06-01",
#     "fin":"2025-06-02",
#     "tz":"Europe/Paris",
#     "freq":"1h",
#     "latitude": 43.34,
#     "longitude": 0.122}



# doc=simulation_panel_mobile(dict_panel=dict_panel_at,dict_soil=dict_soil_st,id_panels=300000,dict_date=dict_date_test_janv,name="panel_st_janv")


# # print(len(doc))





if __name__=="__main__":
    
    dict_panel_st ={
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
    
    dict_panel_at ={
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
        
    dict_soil_st ={
        "ecart_panel":20,
        "ecart_rangee":25,
        "longeur_panel":1,
        "largeur_panel":9,
        "orientation":"sud",
        "resolution":0.5}

    dict_date_test_janv={
    "debut":"2025-06-15",
    "fin":"2025-06-16",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}
    
    dict_date_test_mars={
    "debut":"2025-09-01",
    "fin":"2025-09-02",
    "tz":"Europe/Paris",
    "freq":"1h",
    "latitude": 43.34,
    "longitude": 0.122}

    process1 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_st,"id_panels":300000,"dict_soil":dict_soil_st,"dict_date":dict_date_test_janv,"name":"janv_solar_trak"})
    process2 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_at,"id_panels":300000,"dict_soil":dict_soil_st,"dict_date":dict_date_test_janv,"name":"janv_anti_track"})
    process3 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_st,"id_panels":300000,"dict_soil":dict_soil_st,"dict_date":dict_date_test_mars,"name":"mai_solar_track"})
    process4 = multiprocessing.Process(
        target=simulation_panel_mobile,
        kwargs={"dict_panel":dict_panel_at,"id_panels":300000,"dict_soil":dict_soil_st,"dict_date":dict_date_test_mars,"name":"anti_track_mai"})
    
    
    process1.start()
    process2.start()
    process3.start()
    process4.start()


    process1.join()
    process2.join()
    process3.join()
    process4.join()
    

    log('ending')
        



