import math
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun
import numpy as np
import pandas as pd
import pvlib as pv
from openalea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun


#### get parameter azimuth and sun angulaire 

def convert_panda_datemine(data_test):
    ### extraction parameters
    start=data_test.get("start")
    end=data_test.get("end")
    tz=data_test.get("tz")
    ### creation datetime table with pandas
    times=pd.date_range(start,end,freq="5 min",tz=tz)
    return times 


def calcul_azimut_elev(data_test):
    # extraction parameters
    latitude=data_test.get("latitude")
    longitude=data_test.get("longitude")
    start=data_test.get("start")
    end=data_test.get("end")
    tz=data_test.get("tz")
    ### datetime creation
    times = convert_panda_datemine(data_test)
    ### calcul solar_position
    data_angle=pv.solarposition.get_solarposition(times,latitude,longitude)
    return data_angle

##### create day and hour in panda dataframe
def separate_date_hour(dataframe):
    dataframe=dataframe.reset_index()
    dataframe.rename(columns={"index":"date_heure"},inplace=True)
    dataframe["date"]=dataframe["date_heure"].dt.date
    dataframe["hour"]=dataframe["date_heure"].dt.time
    dataframe["min"]=dataframe["date_heure"].dt.minute
    dataframe["day_of_year"]=dataframe["date_heure"].dt.dayofyear
    return dataframe

###calculation cartesians points
def coordon_x_y_z(dataframe):
    elevation=np.radians(dataframe["apparent_elevation"])
    azimuth=np.radians(dataframe["azimuth"])
    dataframe["y"] = np.cos(elevation) * np.sin(azimuth)
    dataframe["x"] = -(np.cos(elevation) * np.cos(azimuth))
    dataframe["z"] = np.sin(elevation)
    return dataframe

### computation of coordinates 
def coordinate_extraction(data_test):
    data_angle= calcul_azimut_elev(data_test)
    data_date_heure=separate_date_hour(data_angle)
    data_frame_xyz=coordon_x_y_z(data_date_heure)
    dataframe=data_frame_xyz[data_frame_xyz["z"]>0]
    dataframe["z"]=-dataframe["z"]
    datafinal=dataframe[["date_heure","day_of_year","apparent_elevation","azimuth","hour","min","x","y","z"]]
    return datafinal

## another function to calcuate solar position 
def solar_position (dataframe,latitude):
    light=[]
    periode=[]
    x_coord=[]
    y_coord=[]
    z_coord=[]
    for ind, row in enumerate(dataframe.itertuples()):
        day_of_year=row.day_of_year
        t_heure=row.hour
        heure=t_heure.hour + t_heure.minute/60 + t_heure.second/3600
        s=Sun.Sun()
        s._set_pos_astro(day_of_year,heure,3.14/180*latitude)
        if math.degrees(s.elev)<88:
            print("numero jour et heure",day_of_year,heure)
            sun =  Gensun.Gensun()(1, day_of_year, heure, latitude)
            sun = GetLightsSun.GetLightsSun(sun)
            sun_str_split = sun.split(' ')
            x=round(float(sun_str_split[1]),2)
            y=round(float(sun_str_split[2]),2)
            z=round(float(sun_str_split[3]),2)
            sun = [tuple((float(sun_str_split[0]),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
            x_coord.append(x)
            y_coord.append(y)
            z_coord.append(z)
            light.append(sun)
            periode.append(heure)
    #doc_final=pd.DataFrame({"periodes":periode,"coordonnee":light})
    doc_sec=pd.DataFrame({"periode":periode,"x":x_coord,"y":y_coord,"z":z_coord})
    return doc_sec


## Z caribu 
def z_caribu(coordo_z,intens):
    ajus=[]
    for i in range (len(coordo_z)):
        inter=(intens,(coordo_z[i][0],coordo_z[i][1],-coordo_z[i][2]))
        ajus.append(inter)
    return ajus
        
###### little test selection 
def selection (nb,coord):
    doc=[]
    for ls in range(nb):
        doc.append(coord[ls])
    return doc

##### creation format light
def fonction_cvt_light(intensity,coord):
    light=[]
    for i in range(len(coord)):
        cod=(intensity,coord[i])
        light.append(cod)
    return light

#### sky discreditation diffuse modelling
def sky_modelizing(energy):
    ciel_model=GenSky.GenSky()
    ciel_s=ciel_model(energy,"soc",12,9)
    light_string=GetLight.GetLight(ciel_s)
    # light discreditation 
    sky_light=[]
    for string in light_string.split("\n"):
        if len(string)!=0:
            string_split=string.split()
            intens=float(string_split[0])
            direction=tuple(((float(string_split[1]), float(string_split[2]), float(string_split[3]))))
            source = tuple((intens, direction))
            sky_light.append(source)
    return sky_light
            
doc=sky_modelizing(2)




