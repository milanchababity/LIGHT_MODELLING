import math
import numpy as np
import pandas as pd
import pvlib as pv
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun,GenSky
from tqdm import tqdm
import datetime
import requests
import pandas as pd
import json
### information statut
def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

#### get parameter azimuth and sun angulaire 

def convert_panda_datemine(data_test):
    ### extraction parameters
    start=data_test.get("start")
    end=data_test.get("end")
    tz=data_test.get("tz")
    ### creation datetime table with pandas
    times=pd.date_range(start,end,freq="1h",tz=tz)
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
    return dataframe


def dayof_year_extraction(debut,fin,frequence,tz):
    date=pd.date_range(debut,fin,freq=frequence,tz=tz)
    date_dataframe=pd.DataFrame({"date":date})
    date_dataframe["day_of_year"]=date_dataframe["date"].dt.day_of_year
    date_dataframe["heures"]=date_dataframe["date"].dt.hour
    date_dataframe["minutes"]=date_dataframe["date"].dt.minute
    return date_dataframe


def light_caribu(day_of_year,heure_decimaux,latitude,intensity,diffuse):
        doy = float(day_of_year)
        s=Sun.Sun()
        s._set_pos_astro(doy,heure_decimaux,3.14/180*latitude)
        if math.degrees(s.elev)< 88:
            sun =  Gensun.Gensun()(1, doy, heure_decimaux, latitude)
            sun = GetLightsSun.GetLightsSun(sun)
            sun_str_split = sun.split(' ')
            # x=round(float(sun_str_split[1]),2)
            # y=round(float(sun_str_split[2]),2)
            # z=round(float(sun_str_split[3]),2)
            angle_zenithal, angle_azimutal =s._get_pos_astro()
            elevation_solaire= math.radians(90)-angle_zenithal

 
            if diffuse==True:
                sun_light = tuple((float(1),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))
            else:
                sun_light = tuple((intensity,tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))
            return sun_light,elevation_solaire,angle_azimutal
        else:
            sun_light=None
            elevation_solaire=None
            angle_azimutal=None
            return sun_light,elevation_solaire,angle_azimutal
 






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
    datafinal=dataframe[["date_heure","apparent_elevation","azimuth","hour","min","x","y","z"]]
    return datafinal

# other function to calculate solar position 
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
            #sun = [tuple((float(sun_str_split[0]),tuple((float(sun_str_split[1]), float(sun_str_split[2]), float(sun_str_split[3])))))]
            x_coord.append(x)
            y_coord.append(y)
            z_coord.append(z)
            light.append(sun)
            periode.append(heure)
    #doc_final=pd.DataFrame({"periodes":periode,"coordonnee":light})
    doc_sec=pd.DataFrame({"periode":periode,"x":x_coord,"y":y_coord,"z":z_coord})
    return doc_sec

def modelize_sky(energy):
    sky_string = GetLight.GetLight(GenSky.GenSky()(energy, 'soc', 12, 9))  #: (energy, 'soc'=standard sky / 'uoc'=ultraviolet sky, nb secteurs d'panel_north_angle, nb secteurs de zenith)
    # Convert string to list in order to be compatible with CaribuScene input format
    sky = []
    for string in sky_string.split('\n'):
        if len(string) != 0:
            string_split = string.split(' ')
            intensity = float(string_split[0])
            direction = tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))
            source = tuple((intensity, direction))
            sky.append(source)
    return sky



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

def compute_day_of_years(start_date, end_date):
    day_of_years = []
    date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    while (date.strftime("%Y-%m-%d") <= end_date):
        doy = date.timetuple().tm_yday,
        day_of_years.append(doy[0])
        date += datetime.timedelta(days=1)
    return day_of_years

def format_meteo_data(data):
    # returns a [day][hour][direct radiation / diffuse radiation] table
    clean_data = []
    daily_results = []
    for i in range(0, len(data["hourly"]["time"])):
        if i > 0 and i % 24 == 0:
            clean_data.append(daily_results)
            daily_results = []
        daily_results.append([data["hourly"]["direct_radiation"][i], data["hourly"]["diffuse_radiation"][i]])
    clean_data.append(daily_results)
    return clean_data
        
METEO_URL = "https://archive-api.open-meteo.com/v1/archive?latitude={0}&longitude={1}&start_date={2}&end_date={3}&hourly=diffuse_radiation,direct_radiation"
METEO_URL_MN = "https://archive-api.open-meteo.com/v1/archive?latitude={0}&longitude={1}&start_date={2}&end_date={3}&minutely_15=diffuse_radiation,direct_radiation&past_minutely_15=96"

METEO_TEST="https://api.open-meteo.com/v1/forecast""?latitude={0}""&longitude={1}""&minutely_15=direct_radiation,diffuse_radiation""&past_minutely_15=96"

def recup_direct_diffuse (lat,long,start,end):

    reponse= METEO_URL.format(lat,long,start,end) 
    data=requests.get(reponse)
    data_meteo=data.json()
    data_final=pd.DataFrame({"times":data_meteo["hourly"]["time"],
                            "direct_radiation":data_meteo["hourly"]["direct_radiation"],
                            "diffuse_radiation":data_meteo["hourly"]["diffuse_radiation"],
                            })
    data_final["date_time"]=pd.to_datetime(data_final["times"])
    data_final["day_of_year"]=data_final["date_time"].dt.day_of_year
    data_final["hours"]=data_final["date_time"].dt.time
    data_final["minutes"]=data_final["date_time"].dt.minute
    data_final["decimal_hours"] = (pd.to_datetime(data_final["hours"], format="%H:%M:%S").dt.hour
    + pd.to_datetime(data_final["hours"], format="%H:%M:%S").dt.minute / 60)
    data_final["month"]=data_final["date_time"].dt.month
    return data_final

def recup_direct_diffuse_mn (latitude,longitude):
    reponse= METEO_TEST.format(latitude,longitude)
    data=requests.get(reponse)
    data_meteo=data.json()
    data_final=pd.DataFrame({"times":data_meteo["minutely_15"]["time"],
                            "direct_radiation":data_meteo["minutely_15"]["direct_radiation"],
                            "diffuse_radiation":data_meteo["minutely_15"]["diffuse_radiation"],
                            })
    data_final["date_time"]=pd.to_datetime(data_final["times"])
    data_final["day_of_year"]=data_final["date_time"].dt.day_of_year
    data_final["hours"]=data_final["date_time"].dt.time
    data_final["minutes"]=data_final["date_time"].dt.minute
    data_final["decimal_hours"] = (pd.to_datetime(data_final["hours"], format="%H:%M:%S").dt.hour
    + pd.to_datetime(data_final["hours"], format="%H:%M:%S").dt.minute / 60)
    data_final["month"]=data_final["date_time"].dt.month
    return data_final






