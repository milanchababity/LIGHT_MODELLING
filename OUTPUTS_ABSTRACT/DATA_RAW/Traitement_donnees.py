import os 
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 

########## data importation TM 
wd=os.getcwd()
WD_final=os.path.join(wd,"OUTPUTS_ABSTRACT/DATA_RAW")
doc_list=os.listdir(WD_final)
print(doc_list)


# importation dataset csv 

def data_groupement(doc_list):
    DATA_SIRASCA=[]
    DATA_3D_SUD=[]
    DATA_3D_EAST=[]
    for element in doc_list:
        if element.startswith("TM_"):
            DATA_SIRASCA.append(element)
        elif element.__contains__("RAW_SUD"):
            DATA_3D_SUD.append(element)
        elif element.__contains__("RAW_EST"):
            DATA_3D_EAST.append(element)
        elif element.endswith(".xlsx"):
            DATA_METEO=pd.read_excel(os.path.join(WD_final,element))
    return DATA_SIRASCA,DATA_3D_SUD,DATA_3D_EAST,DATA_METEO

data_sirasca,data3d_sud,_,meteo=data_groupement(doc_list)

print(data_sirasca)


#### uploading data frame 

##" upload documents "
def upluoad(wd, name):
    path=os.path.join(wd,name) 
    data=pd.read_csv(path).fillna(0)
    return data

DATA_3D=upluoad(WD_final,data3d_sud[0])

sirasca=[]
for ele in data_sirasca:
    ob=upluoad(WD_final,ele)
    sirasca.append(ob)

SIRASCA = pd.concat(sirasca, axis=1,join="outer",ignore_index=False)
DATA=SIRASCA[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS","species_1","species_2"]]

colname=["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS","species_1","species_2"]
cols=[]
count=0
for col in DATA.columns:
    if col in colname:
        name = f"{col}_{count}"
        cols.append(name)
        count+=1

DATA.columns=cols
print(DATA)
DATA_10H= DATA[DATA["HOURS_0"]==10]


DATA_10= DATA_10H[['ESPECE_1_direct_3','ESPECE_1_direct_4','ESPECE_1_direct_5','ESPECE_2_direct_6','ESPECE_2_direct_7',
                           'ESPECE_2_direct_8','TREATMENTS_12']]


AF=DATA_10[DATA_10["TREATMENTS_12"].str.startswith(("HD1_","HD2_","LD1_","LD2_"))]
WP_=DATA_10[DATA_10["TREATMENTS_12"].str.startswith("WP_")]
FC_=DATA_10[DATA_10["TREATMENTS_12"].str.startswith(("AS3C1","AS3C3"))]


AF_CONT=AF[AF["TREATMENTS_12"].str.contains("NO_")]
WP_CONT=WP_[WP_["TREATMENTS_12"].str.contains("NO_")]
FC_CONT=FC_[FC_["TREATMENTS_12"].str.contains("NO_")]


AF_PV = AF[AF["TREATMENTS_12"].str.contains("P_")]
WP_PV= WP_[WP_["TREATMENTS_12"].str.contains("P_")]
FC_PV= FC_[FC_["TREATMENTS_12"].str.contains("P_")]


AF_CONT=AF_CONT.reset_index().set_index("TREATMENTS_12")
WP_CONT=WP_CONT.reset_index().set_index("TREATMENTS_12")
FC_CONT=FC_CONT.reset_index().set_index("TREATMENTS_12")


AF_PV=AF_PV.reset_index().set_index("TREATMENTS_12")
WP_PV=WP_PV.reset_index().set_index("TREATMENTS_12")
FC_PV=FC_PV.reset_index().set_index("TREATMENTS_12")



########################################## 3D DATA TREATMENTS
def extraction_3d (data):
    DATA_CONT=data[data["Treatments"].str.contains("_NO_")]
    DATA_PV=data [data["Treatments"].str.contains("_P_")]
    return DATA_PV,DATA_CONT


def groupement_species(data3d):
    ALFES= data3d[data3d["Treatments"].str.startswith(("HD1","HD2","LD1","LD2"))]
    WP= data3d[data3d["Treatments"].str.startswith("WP")]
    FECLOV=data3d[data3d["Treatments"].str.startswith("AS3")]
    return ALFES,WP,FECLOV


def TD_data(data):
    datapv,data_cont=extraction_3d(data)
    AL_PV,wp_pv,fes_pv=groupement_species(datapv)
    AL_ct,wp_ct,fes_ct=groupement_species(data_cont)
    return [AL_PV,wp_pv,fes_pv],[AL_ct,wp_ct,fes_ct]

def filter_10_(data, time):
    for i in range(len(data)):
        data_test=data[i]
        if i == 0:
            mix1=data_test[data_test["horaire"]==time]
        elif i ==1:
            mix2=data_test[data_test["horaire"]==time]
        elif i ==2:
            mix3=data_test[data_test["horaire"]==time]

    return [mix1,mix2,mix3]


def pivot_fonction (datalist,pv=True):

    afalfa_fescue=datalist[0]
    wheat_pea=datalist[1]
    fescue_clover=datalist[2]

    if pv==True:
        # pivot 
        data_fescue_alfa=afalfa_fescue.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000:"ALFA_MIX1",2000:"FES_MIX1",3000000: "PV_PANEL"})
        data_wheat_pea=wheat_pea.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000: "WHEAT_MIX2",2000: "PEA_MIXT2",3000000: "PV_PANEL" })
        data_fescue_clover=fescue_clover.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000: "FESCU_MIX3",2000: "CLOV_MIXT3",3000000: "PV_PANEL"})
    else:
        data_fescue_alfa=afalfa_fescue.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000:"ALFA_MIX1",2000:"FES_MIX1"})
        data_wheat_pea=wheat_pea.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000: "WHEAT_MIX2",2000: "PEA_MIXT2"})
        data_fescue_clover=fescue_clover.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(
            columns={1000: "FESCU_MIX3",2000: "CLOV_MIXT3"})
    return [data_fescue_alfa,data_wheat_pea,data_fescue_clover]


######## extraction DATA SIRASCA ET 10 DEG
def TD_extraction(dataframe,hours):
    datapv,data_cont=TD_data(dataframe)
    clean_pv,clean_cont=filter_10_( datapv,hours),filter_10_(data_cont,hours)
    TD_pv_final,TD_cont_final=pivot_fonction(clean_pv),pivot_fonction(clean_cont,pv=False)
    return TD_pv_final,TD_cont_final


PV3D,CONT3D= TD_extraction(DATA_3D, 10)



DataframeAF_cont=pd.concat([AF_CONT,CONT3D[0]],axis=1,ignore_index=False,join="outer")
DataframeAF_pv=pd.concat([AF_PV,PV3D[0]],axis=1,ignore_index=False,join="outer")

DataframeWP_cont=pd.concat([WP_CONT,CONT3D[1]],axis=1,ignore_index=False,join="outer")
DataframeWP_pv=pd.concat([WP_PV,PV3D[1]],axis=1,ignore_index=False,join="outer")


DataframeFC_cont=pd.concat([FC_CONT,CONT3D[2]],axis=1,ignore_index=False,join="outer")
DataframeFC_pv=pd.concat([FC_PV,PV3D[2]],axis=1,ignore_index=False,join="outer")



DataframeAF_cont["symbole"]=np.select([DataframeAF_cont.index.str.startswith("HD1"),
     DataframeAF_cont.index.str.startswith("HD2"),
     DataframeAF_cont.index.str.startswith("LD1"),
     DataframeAF_cont.index.str.startswith("LD2"),],["o","s","d","D"], default="D")

DataframeAF_pv["symbole"]=np.select([DataframeAF_pv.index.str.startswith("HD1"),
     DataframeAF_pv.index.str.startswith("HD2"),
     DataframeAF_pv.index.str.startswith("LD1"),
     DataframeAF_pv.index.str.startswith("LD2"),],["o","s","d","D"], default="D")


DataframeWP_cont["symbole"]=np.select([DataframeWP_cont.index.str.startswith("WP_300"),DataframeWP_cont.index.str.startswith("WP_1100")],
                              ["p","h"],default="D")
DataframeWP_pv["symbole"]=np.select([DataframeWP_pv.index.str.startswith("WP_300"),DataframeWP_pv.index.str.startswith("WP_1100")],
                              ["p","h"],default="D")

DataframeFC_cont["symbole"]=np.select([DataframeFC_cont.index.str.startswith("AS3C1"),DataframeFC_cont.index.str.startswith("AS3C3")],
                                 ["v","<"],default="D")
DataframeFC_pv["symbole"]=np.select([DataframeFC_pv.index.str.startswith("AS3C1"),DataframeFC_pv.index.str.startswith("AS3C3")],
                                 ["v","<"],default="D")

print(DataframeFC_cont)
# DataframeAF_pv=pd.concat([AF_PV,PV3D[0]],axis=1,ignore_index=False,join="outer")
# DataframeWP_cont=pd.concat([WP_CONT,CONT3D[1]],axis=1,ignore_index=False,join="outer")
# DataframeWP_pv=pd.concat([WP_PV,PV3D[1]],axis=1,ignore_index=False,join="outer")
# DataframeFC_cont=pd.concat([FC_CONT,CONT3D[2]],axis=1,ignore_index=False,join="outer")
# DataframeFC_pv=pd.concat([FC_PV,PV3D[2]],axis=1,ignore_index=False,join="outer")


######### TEST PV 

import matplotlib.pyplot as plt
figure, axe=plt.subplots(figsize=(10,8),nrows=1,ncols=3)

for _, row in DataframeAF_cont.iterrows():
    axe[0].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_3"],
        marker=row["symbole"],
        color="green"
    )
    axe[0].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_6"],
        marker=row["symbole"],
        color="red"
    )
    axe[1].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_4"],
        marker=row["symbole"],
        color="green"
    )
    axe[1].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_7"],
        marker=row["symbole"],
        color="red"
    )
    axe[2].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_5"],
        marker=row["symbole"],
        color="green"
    )
    axe[2].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_8"],
        marker=row["symbole"],
        color="red"
    )
    
    
for _, row in DataframeWP_cont.iterrows():
    axe[0].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_1_direct_3"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[0].scatter(row["PEA_MIXT2"],
                   row["ESPECE_2_direct_6"],
                   marker=row["symbole"],
                   color="yellow"
    )
    axe[1].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_1_direct_4"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[1].scatter(row["PEA_MIXT2"],
                   row["ESPECE_2_direct_7"],
                   marker=row["symbole"],
                   color="yellow"
    )
    
    axe[2].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_1_direct_5"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[2].scatter(row["PEA_MIXT2"],
                   row["ESPECE_2_direct_8"],
                   marker=row["symbole"],
                   color="yellow"
    )
    
for _, row in DataframeFC_cont.iterrows():
    
    axe[0].scatter(row["FESCU_MIX3"],
                   row["ESPECE_1_direct_3"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[0].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_2_direct_6"],
                   marker=row["symbole"],
                   color="blue"
    )
    
    axe[1].scatter(row["FESCU_MIX3"],
                   row["ESPECE_1_direct_4"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[1].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_2_direct_7"],
                   marker=row["symbole"],
                   color="blue"
    )

    axe[2].scatter(row["FESCU_MIX3"],
                   row["ESPECE_1_direct_5"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[2].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_2_direct_8"],
                   marker=row["symbole"],
                   color="blue"
    )


figure.patch.set_facecolor("white")

for i in range(len(axe)):
    axe[i].set_xlim(0, 1)
    axe[i].set_ylim(0, 1)
    axe[i].set_aspect('equal', adjustable='box')
    axe[i].grid(True, linestyle=':', alpha=0.5)
    axe[i].set_xlabel("3D MODEL",fontsize=10,fontweight=8,color="red")
    axe[i].set_ylabel("SIRASCA_MODEL",fontsize=10,fontweight=8,color="red")
    x = np.linspace(0, 1, 100)
    axe[i].plot(
    x, x,
    color="black",
    linestyle="--",
    linewidth=1.5,
    label="1:1")

    axe[i].fill_between(
    x,
    0.9*x,
    1.1*x,
    color="white",
    alpha=0.2,
    label="±10 %")
       
plt.show()
figure.savefig("CONTROL.png")


import matplotlib.pyplot as plt
figure, axe=plt.subplots(figsize=(10,8),nrows=1,ncols=3)

for _, row in DataframeAF_cont.iterrows():
    axe[0].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_3"],
        marker=row["symbole"],
        color="green"
    )
    axe[0].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_6"],
        marker=row["symbole"],
        color="red"
    )
    axe[1].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_4"],
        marker=row["symbole"],
        color="green"
    )
    axe[1].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_7"],
        marker=row["symbole"],
        color="red"
    )
    axe[2].scatter(
        row["ALFA_MIX1"],
        row["ESPECE_1_direct_5"],
        marker=row["symbole"],
        color="green"
    )
    axe[2].scatter(
        row["FES_MIX1"],
        row["ESPECE_2_direct_8"],
        marker=row["symbole"],
        color="red"
    )
    
    
for _, row in DataframeWP_cont.iterrows():
    axe[0].scatter(row["PEA_MIXT2"],
                   row["ESPECE_1_direct_3"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[0].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_2_direct_6"],
                   marker=row["symbole"],
                   color="yellow"
    )
    axe[1].scatter(row["PEA_MIXT2"],
                   row["ESPECE_1_direct_4"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[1].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_2_direct_7"],
                   marker=row["symbole"],
                   color="yellow"
    )
    
    axe[2].scatter(row["PEA_MIXT2"],
                   row["ESPECE_1_direct_5"],
                   marker=row["symbole"],
                   color="black"
    )
    axe[2].scatter(row["WHEAT_MIX2"],
                   row["ESPECE_2_direct_8"],
                   marker=row["symbole"],
                   color="yellow"
    )
    
for _, row in DataframeFC_cont.iterrows():
    
    axe[0].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_1_direct_3"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[0].scatter(row["FESCU_MIX3"],
                   row["ESPECE_2_direct_6"],
                   marker=row["symbole"],
                   color="blue"
    )
    
    axe[1].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_1_direct_4"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[1].scatter(row["FESCU_MIX3"],
                   row["ESPECE_2_direct_7"],
                   marker=row["symbole"],
                   color="blue"
    )

    axe[2].scatter(row["CLOV_MIXT3"],
                   row["ESPECE_1_direct_5"],
                   marker=row["symbole"],
                   color="blue"
    )
    axe[2].scatter(row["FESCU_MIX3"],
                   row["ESPECE_2_direct_8"],
                   marker=row["symbole"],
                   color="blue"
    )


figure.patch.set_facecolor("white")

for i in range(len(axe)):
    axe[i].set_xlim(0, 1)
    axe[i].set_ylim(0, 1)
    axe[i].set_aspect('equal', adjustable='box')
    axe[i].grid(True, linestyle=':', alpha=0.5)
    axe[i].set_xlabel("3D MODEL",fontsize=10,fontweight=8,color="red")
    axe[i].set_ylabel("SIRASCA_MODEL",fontsize=10,fontweight=8,color="red")
    x = np.linspace(0, 1, 100)
    axe[i].plot(
    x, x,
    color="black",
    linestyle="--",
    linewidth=1.5,
    label="1:1")

    axe[i].fill_between(
    x,
    0.9*x,
    1.1*x,
    color="gray",
    alpha=0.2,
    label="±10 %")
       
plt.show()
figure.savefig("PV0.png")


print(DataframeAF_cont.head())





#### fescue alfalfa mixte 
DataframeAF_cont["markers"]=np.select(
    [DataframeAF_cont.index.str.startswith("HD1"),
     DataframeAF_cont.index.str.startswith("HD2"),
     DataframeAF_cont.index.str.startswith("LD1"),
     DataframeAF_cont.index.str.startswith("LD2"),],["o","s","d","D"], default="D")
DataframeAF_cont ["colors"]=np.select([DataframeAF_cont.index.str.startswith("HD"),DataframeAF_cont.index.str.startswith("LD")],["limegreen","stgreeforen"],default="black")

#wheat pea mixte 
wheat_pea["colors"]=np.select([wheat_pea.index.str.startswith("WP_300"),wheat_pea.index.str.startswith("WP_1100")],
                              ["firebrick","firebrick"],default="black")
wheat_pea["markers"]=np.select([wheat_pea.index.str.startswith("WP_300"),wheat_pea.index.str.startswith("WP_1100")],
                              ["p","h"],default="D")

# fescue clover mixte 
fescue_clover["colors"]=np.select([fescue_clover.index.str.startswith("AS3C1"),fescue_clover.index.str.startswith("AS3C3")],
                                 ["lightcoral","lightcoral"],default="black")

fescue_clover["markers"]=np.select([fescue_clover.index.str.startswith("AS3C1"),fescue_clover.index.str.startswith("AS3C3")],
                                 ["v","<"],default="D")




print(DataframeAF_pv)

def extraction_cont_pv (data_sirasca):
    data_sirasca=data_sirasca.fillna(0)
    pv=data_sirasca[data_sirasca["PV_direct"]>0]
    contr=data_sirasca[data_sirasca["PV_direct"]==0]
    return pv,contr


def dataTMclean(data):
    pv,cont=extraction_cont_pv(data)
    PV_clean=pv[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS","species_1","species_2"]].groupby("HOURS").get_group(10.0)
    cont_clean=cont[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS","species_1","species_2"]].groupby("HOURS").get_group(10.0)

    # SEPARATE BY SPECIES
    # with PV
    ALF_FES_PV=PV_clean[PV_clean["TREATMENTS"].str.startswith(("HD1_","HD2_","LD1_","LD2_"))]
    WP_PV=PV_clean[PV_clean["TREATMENTS"].str.startswith("WP_")]
    FC_PV=PV_clean[PV_clean["TREATMENTS"].str.startswith("AS3")]

    # WITHOUT PV
    ALF_FES_cont=cont_clean[cont_clean["TREATMENTS"].str.startswith(("HD1_","HD2_","LD1_","LD2_"))]
    WP_PV_cont=cont_clean[cont_clean["TREATMENTS"].str.startswith("WP_")]
    FC_PV_contr=cont_clean[cont_clean["TREATMENTS"].str.startswith("AS3")]

    return [ALF_FES_PV,WP_PV,FC_PV],[ALF_FES_cont,WP_PV_cont,FC_PV_contr]

#### EXTRACTION CONTROL, 0deg et 10 DEG TURBID MEDIUM 
TM_0DEG=upluoad(WD_final,data_sirasca[0])
TM_10DEG=upluoad(WD_final,data_sirasca[1])
TD_0DEG=upluoad(WD_final,data3d_sud[0])
TD_10DEG=upluoad(WD_final,data3d_sud[1])


###### TRAITEMENTS DE DONNEES 

###### data 3D
DAT_3D_0DEG,DAT_3D_CONT=TD_extraction(TD_0DEG,10.0)
DAT_3D_10DEG,_=TD_extraction(TD_10DEG,10.0)

# DAT_3D_0DEG[1] = DAT_3D_0DEG[1].iloc[::-1]
# DAT_3D_10DEG[1] = DAT_3D_10DEG[1].iloc[::-1]
# DAT_3D_CONT[1] = DAT_3D_CONT[1].iloc[::-1]

#### concatenate by species for all configurations 


TD_COMBINE_mix1= pd.concat([DAT_3D_0DEG[0],DAT_3D_10DEG[0],DAT_3D_CONT[0]],axis=0,ignore_index=False).fillna(0)
TD_COMBINE_mix2=pd.concat([DAT_3D_0DEG[1],DAT_3D_10DEG[1],DAT_3D_CONT[1]],axis=0,ignore_index=False).fillna(0)
TD_COMBINE_mix3=pd.concat([DAT_3D_0DEG[2],DAT_3D_10DEG[2],DAT_3D_CONT[2]],axis=0,ignore_index=False).fillna(0)

TM_PV_0DEG,CONTR=dataTMclean(TM_0DEG)
TM_PV_10DEG,_=dataTMclean(TM_10DEG)


##### data Turbid_medium

for element in TM_PV_0DEG:
    element=element.set_index("TREATMENTS",inplace=True)
for element in TM_PV_10DEG:
    element=element.set_index("TREATMENTS",inplace=True)
for element in CONTR:
    element=element.set_index("TREATMENTS",inplace=True)
    


TM_COMBINE_mix1=pd.concat([TM_PV_0DEG[0],TM_PV_10DEG[0],CONTR[0]],axis=0,ignore_index=False).fillna(0)
TM_COMBINE_mix2=pd.concat([TM_PV_0DEG[1],TM_PV_10DEG[1],CONTR[1]],axis=0,ignore_index=False).fillna(0)
TM_COMBINE_mix3=pd.concat([TM_PV_0DEG[2],TM_PV_10DEG[2],CONTR[2]],axis=0,ignore_index=False).fillna(0)
TM_COMBINE_mix2.index = TM_COMBINE_mix2.index.str.strip()
TD_COMBINE_mix2.index = TD_COMBINE_mix2.index.str.strip()



combine=pd.concat([TM_COMBINE_mix1,TD_COMBINE_mix1],axis=1,ignore_index=False,join="outer")
wheat_pea=pd.concat([TM_COMBINE_mix2,TD_COMBINE_mix2],axis=1,ignore_index=False,join="outer")
fescue_clover=pd.concat([TM_COMBINE_mix3,TD_COMBINE_mix3],axis=1,ignore_index=False,join="outer")



#### fescue alfalfa mixte 
combine["markers"]=np.select(
    [combine.index.str.startswith("HD1"),
     combine.index.str.startswith("HD2"),
     combine.index.str.startswith("LD1"),
     combine.index.str.startswith("LD2"),],["o","s","d","D"], default="D")
combine ["colors"]=np.select([combine.index.str.startswith("HD"),combine.index.str.startswith("LD")],["limegreen","forestgreen"],default="black")

#wheat pea mixte 
wheat_pea["colors"]=np.select([wheat_pea.index.str.startswith("WP_300"),wheat_pea.index.str.startswith("WP_1100")],
                              ["firebrick","firebrick"],default="black")
wheat_pea["markers"]=np.select([wheat_pea.index.str.startswith("WP_300"),wheat_pea.index.str.startswith("WP_1100")],
                              ["p","h"],default="D")

# fescue clover mixte 
fescue_clover["colors"]=np.select([fescue_clover.index.str.startswith("AS3C1"),fescue_clover.index.str.startswith("AS3C3")],
                                 ["lightcoral","lightcoral"],default="black")

fescue_clover["markers"]=np.select([fescue_clover.index.str.startswith("AS3C1"),fescue_clover.index.str.startswith("AS3C3")],
                                 ["v","<"],default="D")
wheat_pea
# filter control
aflafa_fescue_control=combine[combine.index.str.contains("_0DEG") & combine.index.str.contains("_NO")]
wheat_peat_control=wheat_pea[wheat_pea.index.str.contains("_0DEG") & wheat_pea.index.str.contains("_NO")]
fescue_clover_control=fescue_clover[fescue_clover.index.str.contains("_0DEG") & fescue_clover.index.str.contains("_NO")]

# filter 0 deg
aflafa_fescue_0deg=combine[combine.index.str.contains("_0DEG") & combine.index.str.contains("_P")]
wheat_peat_0deg=wheat_pea[wheat_pea.index.str.contains("_0DEG") & wheat_pea.index.str.contains("_P")]
fescue_clover_0deg=fescue_clover[fescue_clover.index.str.contains("_0DEG") & fescue_clover.index.str.contains("_P")]

# filter 10 deg
aflafa_fescue_10deg=combine[combine.index.str.contains("_10DEG") & combine.index.str.contains("_P")]
wheat_peat_10deg=wheat_pea[wheat_pea.index.str.contains("_10DEG") & wheat_pea.index.str.contains("_P")]
print(wheat_peat_10deg)
fescue_clover_10deg=fescue_clover[fescue_clover.index.str.contains("_10DEG") & fescue_clover.index.str.contains("_P")]
print(aflafa_fescue_0deg.columns)

### DATA PLOTTING 
print(wheat_peat_control)
TEM=[[aflafa_fescue_control,wheat_peat_control,fescue_clover_control],[aflafa_fescue_0deg,wheat_peat_0deg,fescue_clover_0deg],
     [aflafa_fescue_10deg,wheat_peat_10deg,fescue_clover_10deg]]



######## ROOT MEAN SQUARE ERRORS 
# CONTROL by density 
aflafa_fescue_control["errors_alfalfa"]=(aflafa_fescue_control["ESPECE_1_direct"] - aflafa_fescue_control["ALFA_MIX1"])**2
aflafa_fescue_control["errors_fescue"]=(aflafa_fescue_control["ESPECE_2_direct"] - aflafa_fescue_control["FES_MIX1"])**2
wheat_peat_control["errors_pea"]=(wheat_peat_control["ESPECE_1_direct"]-wheat_peat_control["PEA_MIXT2"])**2
wheat_peat_control["errors_wheat"]=(wheat_peat_control["ESPECE_2_direct"]-wheat_peat_control["WHEAT_MIX2"])**2
fescue_clover_control["errors_clover"]=(fescue_clover_control["ESPECE_1_direct"]-fescue_clover_control["CLOV_MIXT3"])**2
fescue_clover_control["errors_fescue_Cl"]=(fescue_clover_control["ESPECE_2_direct"]-fescue_clover_control["FESCU_MIX3"])**2

print(wheat_peat_control)
# 0 deg 
aflafa_fescue_0deg["errors_alfalfa"]=(aflafa_fescue_0deg["ESPECE_1_direct"] - aflafa_fescue_0deg["ALFA_MIX1"])**2
aflafa_fescue_0deg["errors_fescue"]=(aflafa_fescue_0deg["ESPECE_2_direct"] - aflafa_fescue_0deg["FES_MIX1"])**2
wheat_peat_0deg["errors_pea"]=(wheat_peat_0deg["ESPECE_1_direct"]-wheat_peat_0deg["PEA_MIXT2"])**2
wheat_peat_0deg["errors_wheat"]=(wheat_peat_0deg["ESPECE_2_direct"]-wheat_peat_0deg["WHEAT_MIX2"])**2
fescue_clover_0deg["errors_clover"]=(fescue_clover_0deg["ESPECE_1_direct"]-fescue_clover_0deg["CLOV_MIXT3"])**2
fescue_clover_0deg["errors_fescue_Cl"]=(fescue_clover_0deg["ESPECE_2_direct"]-fescue_clover_0deg["FESCU_MIX3"])**2

##### 10 DEG

aflafa_fescue_10deg["errors_alfalfa"]=(aflafa_fescue_10deg["ESPECE_1_direct"] - aflafa_fescue_10deg["ALFA_MIX1"])**2
aflafa_fescue_10deg["errors_fescue"]=(aflafa_fescue_10deg["ESPECE_2_direct"] - aflafa_fescue_10deg["FES_MIX1"])**2
wheat_peat_10deg["errors_pea"]=(wheat_peat_10deg["ESPECE_1_direct"]-wheat_peat_10deg["PEA_MIXT2"])**2
wheat_peat_10deg["errors_wheat"]=(wheat_peat_10deg["ESPECE_2_direct"]-wheat_peat_10deg["WHEAT_MIX2"])**2
fescue_clover_10deg["errors_clover"]=(fescue_clover_10deg["ESPECE_1_direct"]-fescue_clover_10deg["CLOV_MIXT3"])**2
fescue_clover_10deg["errors_fescue_Cl"]=(fescue_clover_10deg["ESPECE_2_direct"]-fescue_clover_10deg["FESCU_MIX3"])**2

########## CALCULE RMSEP
### control HD
AF_Fe_hd=aflafa_fescue_control[aflafa_fescue_control.index.str.startswith(("HD1","HD2"))]
RMSE_HD_alfalfa=np.sqrt(AF_Fe_hd["errors_alfalfa"].mean())
RMSE_HD_fescue=np.sqrt(AF_Fe_hd["errors_fescue"].mean())

AF_Fe_ld=aflafa_fescue_control[aflafa_fescue_control.index.str.startswith(("LD1","LD2"))]
RMSE_LD_alfalfa=np.sqrt(AF_Fe_ld["errors_alfalfa"].mean())
RMSE_LD_fescue=np.sqrt(AF_Fe_ld["errors_fescue"].mean())

AF_fescue=aflafa_fescue_control[aflafa_fescue_control.index.str.startswith(("HD1","HD2","LD1","LD2"))]
RMSE_AF_alfalfa=np.sqrt(AF_fescue["errors_alfalfa"].mean())
RMSE_AF_fescue=np.sqrt(AF_fescue["errors_fescue"].mean())


### wheat pea control

wheat_pea_300=wheat_peat_control[wheat_peat_control.index.str.startswith("WP_300")]
RMSE_WP_300_PEA=np.sqrt(wheat_pea_300["errors_pea"].mean())
RMSE_WP_300_WHEAT=np.sqrt(wheat_pea_300["errors_wheat"].mean())


wheat_pea_1100=wheat_peat_control[wheat_peat_control.index.str.startswith("WP_1100")]
RMSE_WP_1100_PEA=np.sqrt(wheat_pea_1100["errors_pea"].mean())
RMSE_WP_1100_WHEAT=np.sqrt(wheat_pea_1100["errors_wheat"].mean())

wheat_pea=wheat_peat_control[wheat_peat_control.index.str.startswith(("WP_300","WP_1100"))]
RMSE_mixte_pea=np.sqrt(wheat_pea["errors_pea"].mean())
RMSE_mixte_wheat=np.sqrt(wheat_pea["errors_wheat"].mean())

### fescue clover controm
fescue_clover=fescue_clover_control[fescue_clover_control.index.str.startswith(("AS3C1","AS3C3"))]
RMSE_Fescue_mixte=np.sqrt(fescue_clover["errors_fescue_Cl"].mean())
RMSE_clover_mixte=np.sqrt(fescue_clover["errors_clover"].mean())

fescue_clover_300=fescue_clover_control[fescue_clover_control.index.str.startswith("AS3C1")]
RMSE_Fescue_AS3C1=np.sqrt(fescue_clover_300["errors_fescue_Cl"].mean())
RMSE_clover_AS3C1=np.sqrt(fescue_clover_300["errors_clover"].mean())

fescue_clover_1100=fescue_clover_control[fescue_clover_control.index.str.startswith("AS3C3")]
RMSE_Fescue_AS3C3=np.sqrt(fescue_clover_1100["errors_fescue_Cl"].mean())
RMSE_clover_AS3C3=np.sqrt(fescue_clover_1100["errors_clover"].mean())


######## list RMSEP ######

table_temoin={"FESCUE":{"HD_mixte_fescue":RMSE_HD_fescue,"LD_mixte_fescue":RMSE_LD_fescue},
              "ALFALFA":{"HD_mixte_alfalfa":RMSE_HD_alfalfa,"LD_mixte_alfalfa":RMSE_LD_alfalfa},
              "WHEAT":{"300_wheat":RMSE_WP_300_WHEAT,"1100_wheat":RMSE_WP_1100_WHEAT,"Mixte_wheat":RMSE_mixte_wheat},
              "PEA":{"300_pea":RMSE_WP_300_PEA,"1100_pea":RMSE_WP_1100_PEA,"Mixte_pea":RMSE_mixte_pea},
              "CLOVER":{"AS3C1_clover":RMSE_clover_AS3C1,"AS3C3_clover":RMSE_clover_AS3C3,"Mixte_clover":RMSE_clover_mixte},
              "Fescue_CLOV":{"AS3C1_fescue_clov":RMSE_Fescue_AS3C1,"AS3C3_fescue_clov":RMSE_Fescue_AS3C3,"Mixte_fescue_clov":RMSE_Fescue_mixte}}
data=pd.DataFrame(table_temoin)

########################0Degrees applied 

def RMSEP_extraction (mix1,mix2,mix3):
    mix1["errors_alfala"]=(mix1["ESPECE_1_direct"]-mix1["ALFA_MIX1"])**2
    mix1["erros_fescue"]=(mix1["ESPECE_2_direct"]-mix1["FES_MIX1"])**2
    HD_alfa =np.sqrt(mix1.loc[mix1.index.str.startswith("HD"), "errors_alfala"].mean())
    LD_alfa=np.sqrt(mix1.loc[mix1.index.str.startswith("LD"), "errors_alfala"].mean())

    HD_fes =np.sqrt(mix1.loc[mix1.index.str.startswith("HD"), "errors_fescue"].mean())
    LD_fes=np.sqrt(mix1.loc[mix1.index.str.startswith("LD"), "errors_fescue"].mean())

    mix2["errors_wheat_mixte"]=(mix2["ESPECE_2_direct"]-mix2["WHEAT_MIX2"])**2
    error_wheat_mixte=np.sqrt(mix2["errors_wheat_mixte"].mean())
    error_wheat_300=np.sqrt(mix2.loc[mix2.index.str.startswith("WP_300"),"errors_wheat_mixte"].mean())
    error_wheat_1100=np.sqrt(mix2.loc[mix2.index.str.startswith("WP_1100"),"errors_wheat_mixte"].mean())

    mix2["errors_pea_mixte"]=(mix2["ESPECE_1_direct"]-mix2["PEA_MIXT2"])**2
    error_pea_mixte=np.sqrt(mix2["errors_pea_mixte"].mean())
    error_pea_300=np.sqrt(mix2.loc[mix2.index.str.startswith("WP_300"),"errors_pea_mixte"].mean())
    error_pea_1100=np.sqrt(mix2.loc[mix2.index.str.startswith("WP_1100"),"errors_pea_mixte"].mean())

    mix3["errors_FC_mixte"]=(mix3["ESPECE_1_direct"]-mix3["CLOV_MIXT3"])**2
    error_mixte_clov=np.sqrt(mix3["errors_FC_mixte"].mean())
    error_clov_AS3C1=np.sqrt(mix3.loc[mix3.index.str.startswith("AS3C1"),"errors_FC_mixte"].mean())
    error_clov_AS3C3=np.sqrt(mix3.loc[mix3.index.str.startswith("AS3C3"),"errors_FC_mixte"].mean())

    mix3["errors_fescue_mixte"]=(mix3["ESPECE_2_direct"]-mix3["FESCU_MIX3"])**2
    errors_fesCL_mixte=np.sqrt(mix3["errors_fescue_mixte"].mean())
    errors_fesCL_AS3C1=np.sqrt(mix3.loc[mix3.index.str.startswith("AS3C1"),"errors_fescue_mixte"].mean())
    errors_fesCL_AS3C3=np.sqrt(mix3.loc[mix3.index.str.startswith("AS3C3"),"errors_fescue_mixte"].mean())

    def assemblage (liste_mixte):
        final_items=[]
        for element in liste_mixte:
            for obj in element:
                final_items.append(obj)
        return final_items
    
    items=[["Fescue_alfalfa"]*4+["Wheat_pea"]*6+["Fescue_clover"]*6]
    items_final=assemblage(items)

    species=[["alfalfa"]*2 + ["fescue"]*2 + ["wheat"]*3 + ["pea"]*3 + ["clover"]*3 + ["fescue_cl"]*3]
    species_final=assemblage(species)

    condition = [["HD","LD"]*2 + ["mixte_pea"] + ["pea_300"]+["pea_1100"] +
                 ["mixte_wheat"] + ["wheat_300"]+ ["wheat_1100"]+
                 ["mixte_clover"]+ ["clover_AS3C1"]+ ["clover_AS3C3"]+
                 ["mixte_fescue_cl"]+ ["fescue_cl_AS3C1"]+ ["fescue_cl_AS3C3"]]
    condition_final=assemblage(condition)

    RMSEP=[HD_alfa,LD_alfa,HD_fes,LD_fes,error_pea_mixte,error_pea_300,error_pea_1100,
           error_wheat_mixte,error_wheat_300,error_wheat_1100,
           error_mixte_clov,error_clov_AS3C1,error_clov_AS3C3,
           errors_fesCL_mixte,errors_fesCL_AS3C1,errors_fesCL_AS3C3]
    data_errors =pd.DataFrame({"mixtures":items_final,
                               "species":species_final,
                               "canopies_type":condition_final,
                               "RMSEP":RMSEP})
    data_errors["Types_"]=np.select([data_errors["species"].isin(["fescue","wheat","fescue_cl"]),
                                    data_errors["species"].isin(["pea","clover","alfalfa"])],
                                    ["Grass","Legume"],default="noclass")

    return data_errors

RMSEP_control=RMSEP_extraction(aflafa_fescue_control,wheat_peat_control,fescue_clover_control)
RMSEP_0DEG=RMSEP_extraction(aflafa_fescue_0deg,wheat_peat_0deg,fescue_clover_0deg)
RMSEP_10DEG=RMSEP_extraction(aflafa_fescue_10deg,wheat_peat_10deg,fescue_clover_10deg)
print(RMSEP_control)
print(RMSEP_control)
### tracage histogramme 


def figure_RMSEP(dataframe):
    import seaborn as sns
    import matplotlib.pyplot as plt
    #species=["alfalfa","fescue","pea","wheat","clover","clover","fescue_cl"]
    #species=["Fescue_alfalfa","Wheat_pea","Fescue_clover"]
    species=["Legume","Grass"]
    figure_spe, ax_spec = plt.subplots(figsize=(8, 6),nrows=1,ncols=2,sharey=True)

    for ax,mixture in zip(ax_spec.flat,species):
        data=dataframe[dataframe["Types_"]==mixture]
        sns.violinplot(
        y=data["RMSEP"],
        ax=ax,
        inner="box",
        cut=0,
        color="forestgreen",
        alpha=0.15,
    )
        sns.stripplot(
        y=data["RMSEP"],
        ax=ax,
        color="black",
        size=6,
        jitter=True,
        alpha=0.2
    )
        ax.set_title(mixture)
        ax.set_ylabel("RMSEP")
        ax.set_ylim(0, 1)
        ax.set_aspect('equal', adjustable='box')

        ax.grid(True,axis="y",linestyle="--",alpha=0.5)
        ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()


test=figure_RMSEP(RMSEP_10DEG)


    










import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from adjustText import adjust_text
figures,axes=plt.subplots(figsize=(22,8),nrows=1,ncols=3)


for i, element in enumerate(TEM):
    if i==0:
        print('control plotting')
        for j,obj in enumerate(element):
            if j == 0:
                print('afalfa')
                for _, row in obj.iterrows():
                    axes[0].scatter(row["ESPECE_1_direct"],row["ALFA_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Alfalfa",(row["ESPECE_1_direct"], row["ALFA_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[0].scatter(row["ESPECE_2_direct"],row["FES_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Fescue",(row["ESPECE_2_direct"], row["FES_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)

            elif j ==1:
                print("wheat-pea")
                for _, row in obj.iterrows():
                    axes[0].scatter(row["ESPECE_1_direct"],row["PEA_MIXT2"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Pea",(row["ESPECE_1_direct"], row["PEA_MIXT2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[0].scatter(row["ESPECE_2_direct"],row["WHEAT_MIX2"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Wheat",(row["ESPECE_2_direct"], row["WHEAT_MIX2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)

            elif j ==2:
                print("fescue_clover")
                for _,row in obj.iterrows():
                    axes[0].scatter(row["ESPECE_1_direct"],row["CLOV_MIXT3"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Clover",(row["ESPECE_1_direct"], row["CLOV_MIXT3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[0].scatter(row["ESPECE_2_direct"],row["FESCU_MIX3"],color=row["colors"],marker=row["markers"])
                    axes[0].annotate("Fescue_Clv",(row["ESPECE_2_direct"], row["FESCU_MIX3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
    elif i ==1:
        print("plotting 0deg")
        for j,obj in enumerate(element):
            if j == 0:
                print('afalfa 0deg')
                for _, row in obj.iterrows():
                    axes[1].scatter(row["ESPECE_1_direct"],row["ALFA_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Alfalfa",(row["ESPECE_1_direct"], row["ALFA_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[1].scatter(row["ESPECE_2_direct"],row["FES_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Fescue",(row["ESPECE_2_direct"], row["FES_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)


            elif j ==1:
                print("wheat-pea 0deg")
                for _, row in obj.iterrows():
                    axes[1].scatter(row["ESPECE_1_direct"],row["PEA_MIXT2"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Pea",(row["ESPECE_1_direct"], row["PEA_MIXT2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[1].scatter(row["ESPECE_2_direct"],row["WHEAT_MIX2"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Wheat",(row["ESPECE_2_direct"], row["WHEAT_MIX2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)

            elif j ==2:
                print("fescue_clover 0deg")
                for _,row in obj.iterrows():
                    axes[1].scatter(row["ESPECE_1_direct"],row["CLOV_MIXT3"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Clover",(row["ESPECE_1_direct"], row["CLOV_MIXT3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[1].scatter(row["ESPECE_2_direct"],row["FESCU_MIX3"],color=row["colors"],marker=row["markers"])
                    axes[1].annotate("Fescue_Clv",(row["ESPECE_2_direct"], row["FESCU_MIX3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)

    elif i ==2:
        print("plotting 10deg")
        for j,obj in enumerate(element):
            if j == 0:
                print('afalfa 10deg')
                for _, row in obj.iterrows():
                    axes[2].scatter(row["ESPECE_1_direct"],row["ALFA_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Alfalfa",(row["ESPECE_1_direct"], row["ALFA_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[2].scatter(row["ESPECE_2_direct"],row["FES_MIX1"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Fescue",(row["ESPECE_2_direct"], row["FES_MIX1"]),xytext=(2, 2),textcoords="offset points",fontsize=8)


            elif j ==1:
                print("wheat-pea 10deg")
                for _, row in obj.iterrows():
                    axes[2].scatter(row["ESPECE_1_direct"],row["PEA_MIXT2"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Pea",(row["ESPECE_1_direct"], row["PEA_MIXT2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[2].scatter(row["ESPECE_2_direct"],row["WHEAT_MIX2"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Wheat",(row["ESPECE_2_direct"], row["WHEAT_MIX2"]),xytext=(2, 2),textcoords="offset points",fontsize=8)


            elif j ==2:
                print("fescue_clover 10deg")
                for _,row in obj.iterrows():
                    axes[2].scatter(row["ESPECE_1_direct"],row["CLOV_MIXT3"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Clover",(row["ESPECE_1_direct"], row["CLOV_MIXT3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)
                    axes[2].scatter(row["ESPECE_2_direct"],row["FESCU_MIX3"],color=row["colors"],marker=row["markers"])
                    axes[2].annotate("Fescue_Clv",(row["ESPECE_2_direct"], row["FESCU_MIX3"]),xytext=(2, 2),textcoords="offset points",fontsize=8)

figures.patch.set_facecolor("white")

for i, element in enumerate(TEM):
    axes[i].set_xlim(0, 1)
    axes[i].set_ylim(0, 1)
    axes[i].set_aspect('equal', adjustable='box')
    axes[i].grid(True, linestyle=':', alpha=0.5)
    axes[i].set_xlabel("SIRASCA MODEL",fontsize=10,fontweight=8,color="red")
    axes[i].set_ylabel("3D MODEL",fontsize=10,fontweight=8,color="red")
    x = np.linspace(0, 1, 100)
    axes[i].plot(
    x, x,
    color="black",
    linestyle="--",
    linewidth=1.5,
    label="1:1")

    axes[i].fill_between(
    x,
    0.9*x,
    1.1*x,
    color="gray",
    alpha=0.2,
    label="±10 %")
    if i==0:
        axes[i].set_title("Control",fontsize=12, pad=12)
    elif i ==1:
        axes[i].set_title("Tilt: 0° and orientation: south",fontsize=12, pad=12)
    else:
        axes[i].set_title("Tilt: 10° and orientation: south",fontsize=12, pad=12)

for ax in axes:
    ax.set_facecolor("#F5F2F2F9")
    ax.grid(True, linestyle=":", color="gray", alpha=0.2)


legend_elements = [

    # Mix 1 : Alfalfa / Fescue
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor="limegreen",
           markersize=9, label="HD1"),

    Line2D([0], [0], marker="s", color="w",
           markerfacecolor="limegreen",
           markersize=9, label="HD2"),

    Line2D([0], [0], marker="d", color="w",
           markerfacecolor="forestgreen",
           markersize=9, label="LD1"),

    Line2D([0], [0], marker="D", color="w",
           markerfacecolor="forestgreen",
           markersize=9, label="LD2"),

    # Mix 2 : Wheat / Pea
    Line2D([0], [0], marker="p", color="w",
           markerfacecolor="firebrick",
           markersize=9, label="WP_300"),

    Line2D([0], [0], marker="h", color="w",
           markerfacecolor="firebrick",
           markersize=9, label="WP_1100"),

    # Mix 3 : Fescue / Clover
    Line2D([0], [0], marker="v", color="w",
           markerfacecolor="lightcoral",
           markersize=9, label="AS3C1"),

    Line2D([0], [0], marker="<", color="w",
           markerfacecolor="lightcoral",
           markersize=9, label="AS3C3"),

    # Ligne 1:1
    Line2D([0], [0],
           color="black",
           linestyle="--",
           linewidth=1.5,
           label="1:1"),

    # Tolérance
    Line2D([0], [0],
           color="gray",
           linewidth=8,
           alpha=0.2,
           label="±10 %")
]


legend_species = figures.legend(
    handles=legend_elements,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.02),
    ncol=5,
    fontsize=12,
    frameon=True,
    framealpha=1,
    facecolor="white",
    edgecolor="black"
)

figures.subplots_adjust(
    left=0.04,
    right=0.98,
    bottom=0.20,
    top=0.9,
    wspace=0.15
)
figures.savefig(
    "SIRASCA_vs_CARIBU.png",
    dpi=600,
    facecolor="white"
)


plt.show()

######################### IMPORATATION DATA ############################################
import re
wd=os.getcwd()
print(wd)
WD_final=os.path.join(wd,r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACT\TESTSIRASCA")


doc_list = sorted(
    os.listdir(WD_final),
    key=lambda x: int(re.search(r"SIMULATION_(\d+)", x).group(1))
)
print(doc_list)

def upload_csv(doc_list,work_directory):
    doc_total=[]
    control=[]
    pv=[]
    list=[]
    for element in doc_list:
        file=os.path.join(work_directory,element)
        data=pd.read_csv(file)
        data=data[data["HOURS"]==10]
        data=data[["HOURS","ESPECE_1_direct","ESPECE_2_direct","PV_direct","TREATMENTS","species_1","species_2"]]
        data=data.reset_index().set_index("TREATMENTS").fillna(0)
        data_control=data[data["PV_direct"]==0]
        data_pv_direct=data[data["PV_direct"]!=0]
        doc_total.append(data)
        control.append(data_control)
        pv.append(data_pv_direct)
        list.append(element)
    return doc_total,control,pv,list

data3D = pd.read_csv(r"OUTPUTS_ABSTRACT\TURBID_MEDIUM_LIGHT\ABSTRACT\3D_SIMULATION_SUM_EST_10DEG_FINAL.csv")


dataimport=data3D[["Triangles","Treatments","values_Eabs_direct"]]



# dataimport.loc[dataimport.index[38:40],"Treatments"]="AS3C3_EST_0DEG_NO_EAST"
# dataimport.loc[dataimport.index[35:38],"Treatments"]="AS3C3_EST_0DEG_P_EAST"

data3dpivot=dataimport.pivot(index="Treatments",columns="Triangles",values="values_Eabs_direct").rename(columns={
    1000:"ESPECE_1",2000:"ESPECE_2",3000000:"PV"
}).fillna(0)

DATA3D_final=data3dpivot.reset_index()


DATA3D_final["Treatments"]=DATA3D_final["Treatments"].str.replace(r"EAST$","SUD",regex=True)
DATA3D_final["Treatments"] = DATA3D_final["Treatments"].str.replace("_EST_", "_SUD_", regex=False)


DATA3D_final=DATA3D_final.set_index("Treatments")

########### PV and control 3D separation #######################
DATA3D_control=DATA3D_final[DATA3D_final["PV"]==0]
DATA3D_PV=DATA3D_final[DATA3D_final["PV"]!=0]
DATA_SET= DATA3D_final.copy()

#### upluoad TM
data,CONTROL_TM,PV_TM,liste_=upload_csv(doc_list,WD_final)



def mixte_data(tddata, tm_data):
    dataf_final=[]
    for elemnt in tm_data:
        data=pd.concat([tddata,elemnt],axis=1,ignore_index=False,join="outer")
        dataf_final.append(data)
    return dataf_final

############# combine PV and control 
CONTROL_DATA= mixte_data(DATA3D_control,CONTROL_TM)
PV_DATA = mixte_data(DATA3D_PV,PV_TM)

#data_2=mixte_data(DATA3D_final,data)

#########
def naming_plotting(data_2):
    for element in data_2:
        element["colors"]=np.select([element.index.str.startswith("AS3C1"),
                                    element.index.str.startswith("AS3C3"),
                                    element.index.str.startswith("WP_300"),
                                    element.index.str.startswith("WP_1100"),
                                    element.index.str.startswith("HD1_"),
                                    element.index.str.startswith("HD2_"),
                                    element.index.str.startswith("LD1_"),
                                    element.index.str.startswith("LD2_")],
                                    ["#FF5252",  # Remplace "red" (Rouge corail vif)
        "#5F370A",  # Remplace "firebrick" (Rouge plus doux / rosé)
        "#900DC4",  # Remplace "blue" (Cyan néon très lisible)
        "#280224",  # Remplace "skyblue" (Bleu clair lumineux)
        "#033A42",  # Remplace "green" (Vert menthe / fluo qui se détache du fond)
        "#0EE34A",  # Remplace "olive" (Vert très clair pastel)
        "#274604",  # Remplace "limegreen" (Vert chartreuse clair)
        "#0A8367"],  # Remplace "forestgreen" (Vert turquoise clair)],
        "black")
        element["marker_sp1"]=np.select([element.index.str.startswith("AS3C1"),
                                    element.index.str.startswith("AS3C3"),
                                    element.index.str.startswith("WP_300"),
                                    element.index.str.startswith("WP_1100"),
                                    element.index.str.startswith("HD1_"),
                                    element.index.str.startswith("HD2_"),
                                    element.index.str.startswith("LD1_"),
                                    element.index.str.startswith("LD2_")],
                                    ["o","o","s","s","D","D","D","D"],"*")
        element["marker_sp2"]=np.select([element.index.str.startswith("AS3C1"),
                                    element.index.str.startswith("AS3C3"),
                                    element.index.str.startswith("WP_300"),
                                    element.index.str.startswith("WP_1100"),
                                    element.index.str.startswith("HD1_"),
                                    element.index.str.startswith("HD2_"),
                                    element.index.str.startswith("LD1_"),
                                    element.index.str.startswith("LD2_")],
                                    ["*","*","v","v","h","h","h","h"],"D")
    return data_2

Temoin_DATASET=naming_plotting(CONTROL_DATA)
pv_DATASET=naming_plotting(PV_DATA)

def extraction_rmsep(data):
    # extraction grass legume RMSEP
    RMSEP_grass=[]
    RMSEP_legume=[]
    RMSEP_Afalfa_Fc=[]
    RMSEP_Fescue_Fc=[]
    RMSEP_Wheat=[]
    RMSEP_Pea=[]
    RMSEP_Fescue_C=[]
    RMSEP_Clover=[]
    
    for element in data:
        element["RMSEP_legume"]=((element["ESPECE_1"] - element["ESPECE_1_direct"])**2)
        element["RMSEP_grass"] =((element["ESPECE_2"] - element["ESPECE_2_direct"])**2)
        legume=np.sqrt(element["RMSEP_legume"].mean())
        RMSEP_legume.append(legume)
        grass=np.sqrt(element["RMSEP_grass"].mean())
        RMSEP_grass.append(grass)
        
        #### AFALFA _FESCUE 
        RMSEP_Afalfa_Fc.append(np.sqrt(element.loc[element.index.str.startswith(("HD1_","HD2_","LD1_","LD2_")),"RMSEP_legume"].mean()))
        RMSEP_Fescue_Fc.append(np.sqrt(element.loc[element.index.str.startswith(("HD1_","HD2_","LD1_","LD2_")),"RMSEP_grass"].mean()))
        
        # WHEAT PEA
        RMSEP_Pea.append(np.sqrt(element.loc[element.index.str.startswith("WP_"),"RMSEP_legume"].mean()))
        RMSEP_Wheat.append(np.sqrt(element.loc[element.index.str.startswith("WP_"),"RMSEP_grass"].mean()))
        
        # FESCUE_CLOVER
        RMSEP_Clover.append(np.sqrt(element.loc[element.index.str.startswith(("AS3C1","AS3C1")),"RMSEP_legume"].mean()))
        RMSEP_Fescue_C.append(np.sqrt(element.loc[element.index.str.startswith(("AS3C1","AS3C1")),"RMSEP_grass"].mean()))
    
    data_final=pd.DataFrame({"RMSEP_legume":RMSEP_legume,
                            "RMSEP_grass":RMSEP_grass,
                            "RMSEP_Afalfa_Fc":RMSEP_Afalfa_Fc,
                            "RMSEP_Fescue_Fc":RMSEP_Fescue_Fc,
                            "RMSEP_Wheat":RMSEP_Wheat,
                            "RMSEP_Pea":RMSEP_Pea,
                            "RMSEP_Fescue_C":RMSEP_Fescue_C,
                            "RMSEP_Clover":RMSEP_Clover
                             })
    
    return data_final
        
        
data=extraction_rmsep(Temoin_DATASET)
print(data2)
data2=extraction_rmsep(pv_DATASET)
    

##################################################
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def PLOTTING(data_2,name):
    figure,axes=plt.subplots(figsize=(16,10),nrows=1,ncols=3,sharex=True,sharey=True)
    axes=axes.flatten(order="F")
    figure.patch.set_facecolor('white')

    for i, element in enumerate(data_2):
        for _, row in element.iterrows():

            axes[i].scatter(
                row["ESPECE_1"],
                row["ESPECE_1_direct"],
                marker=row["marker_sp1"],
                color=row["colors"]
            )

            axes[i].scatter(
                row["ESPECE_2"],
                row["ESPECE_2_direct"],
                marker=row["marker_sp2"],
                color=row["colors"]
            )
            axes[i].set_facecolor('white')

    for i, element in enumerate(data_2):
        axes[i].set_xlim(0, 1)
        axes[i].set_ylim(0, 1)
        # axes[i].set_aspect('equal', adjustable='box')
        axes[i].grid(True, linestyle=':', alpha=0.5,color="red")
        # axes[i].set_xlabel("3D MODEL",fontsize=10,fontweight=8,color="red")
        # axes[i].set_ylabel("SIRASCA",fontsize=10,fontweight=8,color="red")
        x = np.linspace(0, 1, 100)
        axes[i].plot(
        x, x,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label="1:1")
        
        axes[i].fill_between(
        x,
        0.9*x,
        1.1*x,
        color="grey",
        alpha=0.2,
        label="±10 %")
        axes[i].set_title(f"SIMULATION {i}",fontsize=14, pad=14,color="black")
        axes[i].set_box_aspect(1)
        
    for i, ax in enumerate(axes):
        # Par défaut, on masque toutes les bordures de chaque plot
        for spine in ax.spines.values():
            spine.set_visible(False)
            ax.spines['left'].set_visible(True)
            ax.spines['left'].set_color('black')
            ax.spines['right'].set_visible(True)
            ax.spines['right'].set_color('black')
            
            ax.tick_params(
        axis='both', 
        which='both', 
        color='white',    # Couleur des petits traits des échelles
        labelcolor='black', # Couleur des chiffres (0.0, 0.2, etc.) en blanc
        bottom=True,      # Afficher les ticks en bas
        left=True         # Afficher les ticks à gauche
    )
            
    figure.supxlabel(
        "3D MODEL",
        fontsize=14,
        fontweight="bold",
        y=0.02,
        color="white"
    )

    figure.supylabel(
        "SIRASCA",
        fontsize=14,
        fontweight="bold",
        x=0.02,
        color="white"
    )
    
    figure.subplots_adjust(
    left=0.04,
    right=0.99,
    bottom=0.12,
    top=0.97,
    wspace=0.02,
    hspace=0.08
)

    color_handles = [
        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor="#FF5252",
            markeredgecolor="#FF5252",
            label="AS05C1"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor= "#5F370A",
            markeredgecolor= "#5F370A",
            label="AS05C3"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor="#033A42",
            markeredgecolor="#033A42",
            label="HD1"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor="#0A8367",
            markeredgecolor="#0A8367",
            label="HD2"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor="#274604",
            markeredgecolor="#274604",
            label="LD1"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor="#A7FFEB",
            markeredgecolor="#A7FFEB",
            label="LD2"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor= "#280224",
            markeredgecolor= "#280224",
            label="WP 1100"
        ),

        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=8,
            markerfacecolor= "#900DC4",
            markeredgecolor= "#900DC4",
            label="WP 300"
        )
    ]

    species_handles = [
        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            color="black",
            markersize=8,
            label="Clover"
        ),

        mlines.Line2D(
            [],
            [],
            marker="*",
            linestyle="None",
            color="black",
            markersize=10,
            label="FescueCL"
        ),

        mlines.Line2D(
            [],
            [],
            marker="D",
            linestyle="None",
            color="black",
            markersize=8,
            label="Alfalfa"
        ),

        mlines.Line2D(
            [],
            [],
            marker="h",
            linestyle="None",
            color="black",
            markersize=9,
            label="FescueA"
        ),

        mlines.Line2D(
            [],
            [],
            marker="s",
            linestyle="None",
            color="black",
            markersize=8,
            label="Pea"
        ),
        mlines.Line2D(
            [],
            [],
            marker="v",
            linestyle="None",
            color="black",
            markersize=8,
            label="Wheat"
        )
    ]

    legend_colors = figure.legend(
        handles=color_handles,
        title="Mixture type",
        loc="upper center",
        bbox_to_anchor=(0.32, 0.22),
        ncol=4,
        frameon=True,
        facecolor="white",
        edgecolor="white"
    )

    legend_markers = figure.legend(
        handles=species_handles,
        title="Specie",
        loc="upper center",
        bbox_to_anchor=(0.72, 0.22),
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="white"
    )
    plt.setp(legend_markers.get_texts(), color="black")
    plt.setp(legend_markers.get_title(), color="black")
    
    plt.setp(legend_colors.get_texts(), color="black")
    plt.setp(legend_colors.get_title(), color="black")

    plt.tight_layout(
        rect=[0.0, 0.15, 1, 1]
    )
    figure.savefig(f"{name}.png")

    plt.show()
    return 

PLOTTING(pv_DATASET,"pv_final")

# print( len(data_2))
from pvlib import tracking
import inspect
print(inspect.getsource(tracking.singleaxis))


# import matplotlib.pyplot as plt
# import numpy as np

# figure, axes = plt.subplots(
#     nrows=4,
#     ncols=6,
#     figsize=(20, 14)
# )

# axes = axes.flatten()

# for i, element in enumerate(data_2):

#     for _, row in element.iterrows():

#         # ESPECE 1
#         axes[i].scatter(
#             row["ESPECE_1"],
#             row["ESPECE_1_direct"],
#             marker=row["marker_sp1"],
#             color=row["colors"]
#         )

#         # ESPECE 2
#         axes[i].scatter(
#             row["ESPECE_2"],
#             row["ESPECE_2_direct"],
#             marker=row["marker_sp2"],
#             color=row["colors"]
#         )

#     # Limites
#     axes[i].set_xlim(0, 1)
#     axes[i].set_ylim(0, 1)

#     # Aspect carré
#     axes[i].set_aspect("equal", adjustable="box")

#     # Grille
#     axes[i].grid(
#         True,
#         linestyle=":",
#         alpha=0.5
#     )

#     # Labels
#     axes[i].set_xlabel(
#         "3D MODEL",
#         fontsize=10,
#         fontweight="bold",
#         color="red"
#     )

#     axes[i].set_ylabel(
#         "SIRASCA",
#         fontsize=10,
#         fontweight="bold",
#         color="red"
#     )

#     # Droite 1:1
#     x = np.linspace(0, 1, 100)

#     axes[i].plot(
#         x,
#         x,
#         color="black",
#         linestyle="--",
#         linewidth=1.5
#     )

#     # Zone ±10 %
#     axes[i].fill_between(
#         x,
#         0.9 * x,
#         1.1 * x,
#         color="gray",
#         alpha=0.2
#     )

#     # Titre
#     axes[i].set_title(
#         f"SIMULATION_{i+1}",
#         fontsize=12
#     )

# plt.tight_layout()
plt.show()

    








