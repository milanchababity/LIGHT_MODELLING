import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy
import os 

dataTM_0deg=pd.read_csv(r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACTSIRASCA_SIMULATION_0_degre_sud.csv")
dataTM_12deg=pd.read_csv(r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACTSIRASCA_SIMULATION_12_degre_sud.csv")




data_0=dataTM_0deg.groupby("HOURS")[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS"]].get_group(12).reset_index()
data_12=dataTM_12deg.groupby("HOURS")[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS"]].get_group(12).reset_index()
data_0_clear=data_0.fillna(0)
data_12_clear=data_12.fillna(0) 
lable=list(data_0_clear['TREATMENTS'])




### colorations 

col_alfa_fes={
"HD1":"red",
"HD2":"darkred",
"LD1":"lightcoral",
"LD2":"orangered"}

col_wheat_pea={"WP_300":"blue",
"WP_1100":"cyan"}
col_fescue_clover={"AS3C1":"green",
                   "AS3C3":"darkgreen"}

## markers ALFALFA 
Dicco_markers={
"HD1":"+",
"HD2":"+",
"LD1":"+",
"LD2":"+",
"WP_300":"o",
"WP_1100":"o",
"AS3C1":"*",
"AS3C3":"*"
}

#### test 
print(data_0_clear)
data_panel_0=data_0_clear[data_0_clear["PV_direct"]>0]
data_control_0=data_0_clear[data_0_clear["PV_direct"]==0]



data_mixte=pd.concat([data_0,data_12],axis=0,ignore_index=True).reset_index()
data_mixte_clear=data_mixte.fillna(0)

data_mixte_clear.to_csv("DATATEST.csv")

print(data_mixte_clear)


















