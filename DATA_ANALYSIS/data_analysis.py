# packages importations 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from pathlib import Path
import os
import datetime
from tqdm import tqdm
# packages CARIBU
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from matplotlib import colors as mcolors
import matplotlib.dates as mdates
import matplotlib.dates as mdates

### FUNCTION IMPORTATION DATA
#loading data set and triangles coordonates
def dataset_load(dataset_name,doc_name):
    path_final=str(Path.cwd())
    doc=pd.read_csv(f"{path_final}\\{doc_name}\\{dataset_name}")
    if "hours"in doc.columns:
        doc["hours_dt"]=pd.to_datetime(doc["hours"],format="%H:%M:%S").dt.time
        doc_plot=doc[doc["Triangles"] <3000000] # to delete all lines associates with panels and poteaux
        doc_final=doc_plot.set_index("Triangles",drop=True)
        doc_final.drop(labels=["hours"],axis=1,inplace=True)
        return doc_final
    else:
        doc_tri=doc[doc["Triangles"] <3000000]
        doc_tri.set_index("Triangles",inplace=True)
        return doc_tri


doc = pd.read_csv(r"C:\Users\mbabity\Documents\PlantGL\MAPPING_CARIBU\OUTPUTS_MAPPING\panel_normal_sud_5mn.csv")
doc["hours_dt"]=pd.to_datetime(doc["hours"],format="%H:%M:%S")


doc_1= doc.groupby("Triangles").get_group(0)
doc_2= doc.groupby("Triangles").get_group(1)
doc_3= doc.groupby("Triangles").get_group(2)

fig,ax=plt.subplots(figsize=(10,6),nrows=3,ncols=1)
ax[0].plot(doc_1["hours_dt"],doc_1["Ei"],color="red")
ax[0].set_title("Triangle 0")   
ax[1].plot(doc_2["hours_dt"],doc_2["Ei"],color="blue")
ax[1].set_title("Triangle 1")   
ax[2].plot(doc_3["hours_dt"],doc_3["Ei"],color="green")
ax[2].set_title("Triangle 2")   
ax[2].set_xlabel("hours")
ax[0].xaxis.set_major_locator(mdates.HourLocator(interval=1))   
ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))      
ax[1].xaxis.set_major_locator(mdates.HourLocator(interval=1))   
ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))      
ax[2].xaxis.set_major_locator(mdates.HourLocator(interval=1))   
ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))      
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
plt.savefig("transient_irradiance_normal_panel1.png")



### function for grouping / grouping the result according to the index ("Triangles") use for visualing transient irradiance
def fonction_groupinng(data,nb_grp):
    group=[]
    grouped_data=data.groupby(level=0)
    for i in range (nb_grp):
        triangle=grouped_data.get_group(i)
        group.append(triangle)
    return group # return list of dataset by triangle 

# for plotting transient 
def plotting_triangle_function(data1, config, step_time, col):
    fig, ax = plt.subplots(figsize=(10, 6)) 
    fig.suptitle(f"Transient irradiance on {config} | Step: {step_time}")
    for i in range(len(data1)):
        times = pd.to_datetime(data1[i]["hours_dt"], format='%H:%M:%S', errors='coerce')
        # Plotting on 'ax' directly
        ax.plot(times, data1[i]["Ei"], color=col)
    ax.set_title(f"Configuration: {config}", loc="left", fontsize=8)
    ax.set_xlabel("hours")
    # Formatting dates
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"transient_irradiance_{config}.png")



doc_plot= {
    "dataset_data":"panel_normal_1.csv",
    "dataset_tr":"coord_xy_norm_1.csv",
    "doc_name":"outputs_simulation",
    "nb_grp":6,
    "index_groupe":"Triangles",
    "config":"normal sud",
    "step_time":"1 h"
}

def plot_automatic_transt(dic_plot,col="black",mapping=False):
    dataset_data=dic_plot.get("dataset_data")
    dataset_tri=dic_plot.get("dataset_tr")
    doc_name=dic_plot.get("doc_name")
    nb_grp=dic_plot.get("nb_grp")
    index_groupe=dic_plot.get("index_groupe")
    doc_name=dic_plot.get("doc_name")
    config=dic_plot.get("config")
    step_time=dic_plot.get("step_time")
    
    # dataset importation
    data_load=dataset_load(dataset_data,doc_name)
    group_load=fonction_groupinng(data_load,nb_grp)
    plotting_triangle_function(group_load,config,step_time,col)
    data_tri=dataset_load(dataset_tri,doc_name)
    
    grouped = data_load.groupby("hours_dt")
    for i, (time_val, data_grouped) in enumerate(grouped):
            plot_merge = pd.merge(data_tri, data_grouped[["Ei"]], left_index=True, right_index=True, how="inner")
            datafinal = plot_merge.pivot(index="X", columns="Y", values="Ei")
            fig, ax = plt.subplots()
            mesh = ax.pcolormesh(datafinal.columns, datafinal.index, datafinal.values, shading="auto")
            plt.colorbar(mesh, label='Ei')
            ax.set_title(f"Irradiance at {time_val}")
            plt.savefig(f"mapping_irradiance_groupe{i}.png")
            plt.close(fig) # Important: prevents memory leaks when creating many plots
    
plot_automatic_transt(doc_plot,col="red",mapping=True)
        
    
    
    
    
    


import matplotlib.colors as col
from matplotlib import colors as mcolors
colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
print(colors.keys())
color=col()