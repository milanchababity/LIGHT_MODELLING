import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.tri as tri 

from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *
from mpl_toolkits.axes_grid1 import make_axes_locatable

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from MAPPING_CARIBU import MODULE_MAPPING


##### importation files 
# triangles 
with open("MAPPING_CARIBU/PKL_FILE/id_primitive_ajoures_panel_est.pkl","rb") as prim:
    id_prim=pickle.load(prim)

with open("MAPPING_CARIBU/PKL_FILE/triangle_prim_ajoures_panel_est.pkl","rb") as triangle:
    tri_prim=pickle.load(triangle)

data_ajoure=pd.read_csv("MAPPING_CARIBU/RAW_CSV/data_ajoures_panel_est.csv")

scene=Scene(r"MAPPING_CARIBU/bgeom_USEFUL/scene_ajoures_panel_est.bgeom")





##### STANDARIZED OBJECT
scaler=StandardScaler()

data_ajoure[["values_Ei_direct_ST","values_Ei_diffus_ST","values_Ei_totale_ST"]]=scaler.fit_transform(data_ajoure[["values_Ei","Values_Ei_finale","Ei_total_sum"]])
print(data_ajoure)


# ## identifing optimum Kluster 
# def optimise_kluster (data, max_k):
#     means=[]
#     inertia=[]
#     for k in range (1,max_k):
#         kmeans=KMeans(n_clusters=k)
#         kmeans.fit(data)
#         means.append(k)
#         inertia.append(kmeans.inertia_)
#     fig=plt.subplots(figsize=(10,10))
#     plt.plot(means,inertia,"o-")
#     plt.xlabel('Number of clusters ')
#     plt.ylabel("inertia")
#     plt.grid(True)
#     plt.show()
    
# optimise_kluster(data_ajoure[["values_Ei_totale_ST"]],10)

kmeans=KMeans(n_clusters=3)
kmeans.fit(data_ajoure[["values_Ei_totale_ST"]])
data_ajoure["labels"]=kmeans.labels_

data_mapping=data_ajoure[["Triangles","labels"]]

data_mapping=data_mapping.rename(columns={"labels":"Ei_total_sum"})



maping=MODULE_MAPPING.mapping_2D(data_mapping,tri_prim,id_prim,scene,"ajoure_est",id_panel=3000000)

scene_normal=Scene(r"MAPPING_CARIBU/bgeom_USEFUL/scene_normal_sud.bgeom")

with open("MAPPING_CARIBU/PKL_FILE/id_primitive_normal_sud.pkl","rb") as prim:
    id_prim_sud=pickle.load(prim)

with open("MAPPING_CARIBU/PKL_FILE/triangle_prim_normal_sud.pkl","rb") as triangle:
    tri_prim_sud=pickle.load(triangle)

data_ajoure=pd.read_csv("MAPPING_CARIBU/RAW_CSV/datanormal_sud.csv")

data_ajoure[["values_Ei_direct_ST","values_Ei_diffus_ST","values_Ei_totale_ST"]]=scaler.fit_transform(data_ajoure[["values_Ei","Values_Ei_finale","Ei_total_sum"]])
print(data_ajoure)

kmeans=KMeans(n_clusters=3)
kmeans.fit(data_ajoure[["values_Ei_totale_ST"]])
data_ajoure["labels"]=kmeans.labels_

data_mapping=data_ajoure[["Triangles","labels"]]

data_mapping=data_mapping.rename(columns={"labels":"Ei_total_sum"})
maping=MODULE_MAPPING.mapping_2D(data_mapping,tri_prim,id_prim,scene,"normal_sud",id_panel=3000000)