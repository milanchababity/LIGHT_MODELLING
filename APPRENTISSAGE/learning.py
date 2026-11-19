
###### gantt diagramm

import pandas as pd
from plotly_calplot import calplot
file_path=r"C:\Users\mbabity\Documents\PlantGL\learning\sales_data.xlsx"
sales_data=pd.read_excel(file_path)
sales_data['date'] = pd.to_datetime(sales_data['date'], errors='coerce').astype('datetime64[ns]')
print(sales_data["date"].dtype)
print(sales_data.head())

fig=calplot(sales_data,x="date",y="sales",dark_theme=True)

fig.show()

###" diagramme de gantt"
import numpy as np
import matplotlib as plt
import seaborn as sns

########################################
#septembre 2026
sept_2026=pd.date_range(start="2026-09-01",end="2026-09-30",freq="B")
n_sep = len(sept_2026)
tier_sep = n_sep // 3

septembre_2026 =pd.DataFrame({
    "Dates":sept_2026,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[1]*tier_sep + [0]*(n_sep-tier_sep),
    "Expérimentation exploratoire":[0]*tier_sep + [1]*tier_sep + [0]*(n_sep-(2*tier_sep)),
    "Expérimentation Nièvre":[0]*n_sep,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_sep,
    "Production d'article sientifique":[0]*n_sep,
    "Comité de pilotage de thèse":[0]*n_sep,
    "Analyses et traitements de données":[0]*n_sep,
    "Rédaction de manuscrit de thèse":[0]*n_sep,
    "Recherches bibliographiques":[0]*(2*tier_sep) + [1]*(n_sep-(2*tier_sep)),
    "soutenance de thèse":[0]*n_sep 
}).set_index("Dates")

print(septembre_2026)


# octobre 2026##############################
oct_2026=pd.date_range(start="2026-10-01",end="2026-10-31",freq="B")
n_oct = len(oct_2026)
quart_oct = n_oct // 4

octobre_2026 =pd.DataFrame({
    "Dates":oct_2026,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[1]*quart_oct + [0]*(n_oct-quart_oct),
    "Expérimentation exploratoire":[0]*quart_oct + [1]*quart_oct + [0]*(n_oct-(2*quart_oct)),
    "Expérimentation Nièvre":[0]*n_oct,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_oct,
    "Production d'article sientifique":[0]*n_oct,
    "Comité de pilotage de thèse":[0]*n_oct,
    "Analyses et traitements de données":[0]*n_oct,
    "Rédaction de manuscrit de thèse":[0]*n_oct,
    "Recherches bibliographiques":[0]*(3*quart_oct) + [1]*(n_oct-(3*quart_oct)),
    "soutenance de thèse":[0]*n_oct
}).set_index("Dates")

### novembre 2026
nov_2026=pd.date_range(start="2026-11-01",end="2026-11-30",freq="B")
n_nov = len(nov_2026)
quart_nov = n_nov // 4

novembre_2026 =pd.DataFrame({
    "Dates":nov_2026,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_nov,
    "Expérimentation exploratoire":[1]*(2*quart_nov) + [0]*(n_nov-(2*quart_nov)),
    "Expérimentation Nièvre":[0]*n_nov,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*(2*quart_nov) + [1]*(quart_nov)+[0]*(n_nov-(3*quart_nov)),
    "Production d'article sientifique":[0]*n_nov,
    "Comité de pilotage de thèse":[0]*(n_nov-1)+ [1],
    "Analyses et traitements de données":[0]*n_nov,
    "Rédaction de manuscrit de thèse":[0]*n_nov,
    "Recherches bibliographiques":[0]*(3*quart_nov) + [1]*((n_nov-1)-(3*quart_nov))+ [0],
    "soutenance de thèse":[0]*n_nov 
}).set_index("Dates")

# Décembre 2026
dec_2026=pd.date_range(start="2026-12-01",end="2026-12-31",freq="B")
n_dec = len(dec_2026)
quart_dec = n_dec // 4
decembre_2026 =pd.DataFrame({
    "Dates":dec_2026,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_dec,
    "Expérimentation exploratoire":[1]*(3*quart_dec) + [0]*(n_dec-(3*quart_dec)),
    "Expérimentation Nièvre":[0]*n_dec,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_dec,
    "Modélisation sur Stics":[0]*n_dec,
    "Production d'article sientifique":[0]*n_dec,
    "Comité de pilotage de thèse":[0]*n_dec,
    "Analyses et traitements de données":[0]*n_dec,
    "Rédaction de manuscrit de thèse":[0]*n_dec,
    "Recherches bibliographiques":[0]*(3*quart_dec) + [1]*(n_dec-(3*quart_dec)),
    "soutenance de thèse":[0]*n_dec
}).set_index("Dates")

print(novembre_2026)

# janv 2027
janv_2027=pd.date_range(start="2027-01-01",end="2027-01-30",freq="B")
n_janv_2027 = len(janv_2027)
quart_janv_2027 = n_janv_2027 // 4

janvier_2027 =pd.DataFrame({
    "Dates":janv_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_janv_2027,
    "Expérimentation exploratoire":[0]*n_janv_2027,
    "Expérimentation Nièvre":[0]*n_janv_2027,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_janv_2027,
    "Modélisation sur Stics":[0]*n_janv_2027,
    "Production d'article sientifique":[0]*(3*quart_janv_2027) + [1]*(n_janv_2027-(3*quart_janv_2027)),
    "Comité de pilotage de thèse":[0]*n_janv_2027,
    "Analyses et traitements de données":[1]*(2*quart_janv_2027)+[0]*(n_janv_2027-(2*quart_janv_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_janv_2027,
    "Recherches bibliographiques":[0]*(2*quart_janv_2027) + [1]*(quart_janv_2027)+ [0]*(n_janv_2027-(3*quart_janv_2027)),
    "soutenance de thèse":[0]*n_janv_2027
}).set_index("Dates")

#fevrier 2027
fev_2027=pd.date_range(start="2027-02-01",end="2027-02-28",freq="B")
n_fev_2027 = len(fev_2027)
quart_fev_2027 = n_fev_2027 // 4
fevrier_2027 =pd.DataFrame({
    "Dates":fev_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_fev_2027,
    "Expérimentation exploratoire":[0]*n_fev_2027,
    "Expérimentation Nièvre":[0]*n_fev_2027,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_fev_2027,
    "Modélisation sur Stics":[0]*n_fev_2027,
    "Production d'article sientifique":[0]*(2*quart_fev_2027) +[1]*(quart_fev_2027)+[0]*(n_fev_2027-(3*quart_fev_2027)),
    "Comité de pilotage de thèse":[0]*n_fev_2027,
    "Analyses et traitements de données":[1]*(quart_fev_2027)+[0]*(n_fev_2027-(quart_fev_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_fev_2027,
    "Recherches bibliographiques":[0]*(3*quart_fev_2027) + [1]*(n_fev_2027-(3*quart_fev_2027)),
    "soutenance de thèse":[0]*n_fev_2027 
}).set_index("Dates")

# Mars 2027
mas_2027=pd.date_range(start="2027-03-01",end="2027-03-31",freq="B")
n_mars_2027 = len(mas_2027)
quart_mas_2027 = n_mars_2027 // 4
mars_2027 =pd.DataFrame({
    "Dates":mas_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_mars_2027,
    "Expérimentation exploratoire":[0]*n_mars_2027,
    "Expérimentation Nièvre":[0]*(3*quart_mas_2027)+[1]*(n_mars_2027-(3*quart_mas_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_mars_2027,
    "Modélisation sur Stics":[0]*n_mars_2027,
    "Production d'article sientifique":[1]*(2*quart_mas_2027) +[0]*(n_mars_2027-(2*quart_mas_2027)),
    "Comité de pilotage de thèse":[0]*(n_mars_2027-1) + [1],
    "Analyses et traitements de données":[0]*(2*quart_mas_2027)+[1]*(quart_mas_2027)+[0]*(n_mars_2027-(3*quart_mas_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_mars_2027,
    "Recherches bibliographiques":[0]*n_mars_2027,
    "soutenance de thèse":[0]*n_mars_2027
}).set_index("Dates")

# avril_2027
avril_2027=pd.date_range(start="2027-04-01",end="2027-04-30",freq="B")
n_avr_2027 = len(avril_2027)
quart_avr_2027 = n_avr_2027 // 4
avril_2027 =pd.DataFrame({
    "Dates":avril_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_avr_2027,
    "Expérimentation exploratoire":[0]*n_avr_2027,
    "Expérimentation Nièvre":[1]*(3*quart_avr_2027)+ [0]*(n_avr_2027-(3*quart_avr_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_avr_2027,
    "Modélisation sur Stics":[0]*n_avr_2027,
    "Production d'article sientifique":[0]*n_avr_2027,
    "Comité de pilotage de thèse":[0]*n_avr_2027,
    "Analyses et traitements de données":[0]*(3*quart_avr_2027)+[1]*(n_avr_2027-(3*quart_avr_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_avr_2027,
    "Recherches bibliographiques":[0]*n_avr_2027,
    "soutenance de thèse":[0]*n_avr_2027 
}).set_index("Dates")

## mai 2027
ms_2027=pd.date_range(start="2027-05-01",end="2027-05-31",freq="B")
n_mai_2027 = len(ms_2027)
quart_mai_2027 = n_mai_2027 // 4
mai_2027 =pd.DataFrame({
    "Dates":ms_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_mai_2027,
    "Expérimentation exploratoire":[0]*n_mai_2027,
    "Expérimentation Nièvre":[1]*(3*quart_mai_2027)+ [0]*(n_mai_2027-(3*quart_mai_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_mai_2027,
    "Modélisation sur Stics":[0]*n_mai_2027,
    "Production d'article sientifique":[0]*n_mai_2027,
    "Comité de pilotage de thèse":[0]*n_mai_2027,
    "Analyses et traitements de données":[0]*(3*quart_mai_2027)+[1]*(n_mai_2027-(3*quart_mai_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_mai_2027,
    "Recherches bibliographiques":[0]*n_mai_2027,
    "soutenance de thèse":[0]*n_mai_2027 
}).set_index("Dates")

# juin 2027
jn_2027=pd.date_range(start="2027-06-01",end="2027-06-30",freq="B")
n_jn_2027 = len(jn_2027)
quart_jun_2027 = n_jn_2027 // 4
juin_2027 =pd.DataFrame({
    "Dates":jn_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_jn_2027,
    "Expérimentation exploratoire":[0]*n_jn_2027,
    "Expérimentation Nièvre":[1]*(2*quart_jun_2027)+ [0]*(n_jn_2027-(2*quart_jun_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_jn_2027,
    "Modélisation sur Stics":[0]*n_jn_2027,
    "Production d'article sientifique":[0]*(2*quart_jun_2027)+[1]*(quart_jun_2027)+[0]*(n_jn_2027-(3*quart_jun_2027)),
    "Comité de pilotage de thèse":[0]*n_jn_2027,
    "Analyses et traitements de données":[0]*(3*quart_jun_2027)+[1]*(n_jn_2027-(3*quart_jun_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_jn_2027,
    "Recherches bibliographiques":[0]*n_jn_2027,
    "soutenance de thèse":[0]*n_jn_2027 
}).set_index("Dates")

#juillet 2027
jl_2027=pd.date_range(start="2027-07-01",end="2027-07-31",freq="B")
n_jul_2027 = len(jl_2027)
quart_jul_2027 = n_jul_2027 // 4
juillet_2027 =pd.DataFrame({
    "Dates":jl_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_jul_2027,
    "Expérimentation exploratoire":[0]*n_jul_2027,
    "Expérimentation Nièvre":[1]*(2*quart_jul_2027)+ [0]*(n_jul_2027-(2*quart_jul_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_jul_2027,
    "Modélisation sur Stics":[0]*n_jul_2027,
    "Production d'article sientifique":[0]*(2*quart_jul_2027)+[1]*(quart_jul_2027)+[0]*(n_jul_2027-(3*quart_jul_2027)),
    "Comité de pilotage de thèse":[0]*n_jul_2027,
    "Analyses et traitements de données":[0]*(3*quart_jul_2027)+[1]*(n_jul_2027-(3*quart_jul_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_jul_2027,
    "Recherches bibliographiques":[0]*n_jul_2027,
    "soutenance de thèse":[0]*n_jul_2027 
}).set_index("Dates")

#août 2027
aou_2027=pd.date_range(start="2027-08-01",end="2027-08-30",freq="B")
n_aout_2027 = len(aou_2027)
quart_aout_2027 = n_aout_2027 // 4
aout_2027 =pd.DataFrame({
    "Dates":aou_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_aout_2027,
    "Expérimentation exploratoire":[0]*n_aout_2027,
    "Expérimentation Nièvre":[1]*(quart_aout_2027)+ [0]*(n_aout_2027-quart_aout_2027),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_aout_2027,
    "Modélisation sur Stics":[0]*quart_aout_2027+[1]*(n_aout_2027-quart_aout_2027),
    "Production d'article sientifique":[0]*n_aout_2027,
    "Comité de pilotage de thèse":[0]*n_aout_2027,
    "Analyses et traitements de données":[0]*n_aout_2027,
    "Rédaction de manuscrit de thèse":[0]*n_aout_2027,
    "Recherches bibliographiques":[0]*n_aout_2027,
    "soutenance de thèse":[0]*n_aout_2027
}).set_index("Dates")

#septembre 2027#######################################################
sep_2027=pd.date_range(start="2027-09-01",end="2027-09-30",freq="B")
n_sep_2027 = len(sep_2027)
quart_sep_2027 = n_sep_2027 // 4
septembre_2027 =pd.DataFrame({
    "Dates":sep_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_sep_2027,
    "Expérimentation exploratoire":[0]*n_sep_2027,
    "Expérimentation Nièvre":[1]*(2*quart_sep_2027)+ [0]*(n_sep_2027-(2*quart_sep_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_sep_2027,
    "Modélisation sur Stics":[0]*(2*quart_sep_2027)+ [1]*quart_sep_2027 + [0]*(n_sep_2027-(3*quart_sep_2027)),
    "Production d'article sientifique":[0]*n_sep_2027,
    "Comité de pilotage de thèse":[0]*n_sep_2027,
    "Analyses et traitements de données":[0]*n_sep_2027,
    "Rédaction de manuscrit de thèse":[0]*n_sep_2027,
    "Recherches bibliographiques":[0]*(3*quart_sep_2027) +[1]*(n_sep_2027-(3*quart_sep_2027)),
    "soutenance de thèse":[0]*n_sep_2027 
}).set_index("Dates")

# octobre 2027
oct_2027=pd.date_range(start="2027-10-01",end="2027-10-31",freq="B")
n_oct_2027 = len(oct_2027)
quart_oct_2027 = n_oct_2027 // 4
octobre_2027 =pd.DataFrame({
    "Dates":oct_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_oct_2027,
    "Expérimentation exploratoire":[0]*n_oct_2027,
    "Expérimentation Nièvre":[1]*quart_oct_2027 + [0]*(n_oct_2027-(quart_oct_2027)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_oct_2027,
    "Modélisation sur Stics":[0]*quart_oct_2027+ [1]*quart_oct_2027 + [0]*(n_oct_2027-(2*quart_oct_2027)),
    "Production d'article sientifique":[0]*(2*quart_oct_2027)+[1]*quart_oct_2027+[0]*(n_oct_2027-(3*quart_oct_2027)),
    "Comité de pilotage de thèse":[0]*n_oct_2027,
    "Analyses et traitements de données":[0]*(3*quart_oct_2027)+[1]*(n_oct_2027-(3*quart_oct_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_oct_2027,
    "Recherches bibliographiques":[0]*n_oct_2027,
    "soutenance de thèse":[0]*n_oct_2027
}).set_index("Dates")

#novembre 2027
nov_2027=pd.date_range(start="2027-11-01",end="2027-11-30",freq="B")
n_nov_2027 = len(nov_2027)
quart_nov_2027 = n_nov_2027 // 4
novembre_2027 =pd.DataFrame({
    "Dates":nov_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_nov_2027,
    "Expérimentation exploratoire":[0]*n_nov_2027,
    "Expérimentation Nièvre":[0]*n_nov_2027,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_nov_2027,
    "Modélisation sur Stics":[1]*quart_nov_2027 + [0]*(n_nov_2027-(quart_nov_2027)),
    "Production d'article sientifique":[0]*n_nov_2027,
    "Comité de pilotage de thèse":[0]*n_nov_2027,
    "Analyses et traitements de données":[0]*quart_nov_2027 + [1]*(n_nov_2027-(quart_nov_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_nov_2027,
    "Recherches bibliographiques":[0]*n_nov_2027,
    "soutenance de thèse":[0]*n_nov_2027
}).set_index("Dates")


# decembre 2027
dec_2027=pd.date_range(start="2027-12-01",end="2027-12-31",freq="B")
n_dec_2027 = len(dec_2027)
quart_dec_2027 = n_dec_2027 // 4
decembre_2027 =pd.DataFrame({
    "Dates":dec_2027,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_dec_2027,
    "Expérimentation exploratoire":[0]*n_dec_2027,
    "Expérimentation Nièvre":[0]*n_dec_2027,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_dec_2027,
    "Modélisation sur Stics":[1]*quart_dec_2027 + [0]*(n_dec_2027-(quart_dec_2027)),
    "Production d'article sientifique":[0]*n_dec_2027,
    "Comité de pilotage de thèse":[1] + [0]*(n_dec_2027 - 1),
    "Analyses et traitements de données":[0]*(2*quart_dec_2027)+[1]*(n_dec_2027-(2*quart_dec_2027)),
    "Rédaction de manuscrit de thèse":[0]*n_dec_2027,
    "Recherches bibliographiques":[0]*n_dec_2027,
    "soutenance de thèse":[0]*n_dec_2027 
}).set_index("Dates")

# janvier 2028
jan_2028=pd.date_range(start="2028-01-01",end="2028-01-31",freq="B")
n_jan_2028 = len(jan_2028)
quart_jan_2028 = n_jan_2028 // 4
janvier_2028 =pd.DataFrame({
    "Dates":jan_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_jan_2028,
    "Expérimentation exploratoire":[0]*n_jan_2028,
    "Expérimentation Nièvre":[0]*n_jan_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_jan_2028,
    "Modélisation sur Stics":[0]*n_jan_2028,
    "Production d'article sientifique":[0]*n_jan_2028,
    "Comité de pilotage de thèse":[0]*n_jan_2028,
    "Analyses et traitements de données":[1]*(3*quart_jan_2028) +[0]*(n_jan_2028-(3*quart_jan_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_jan_2028,
    "Recherches bibliographiques":[0]*(3*quart_jan_2028) +[1]*(n_jan_2028-(3*quart_jan_2028)),
    "soutenance de thèse":[0]*n_jan_2028 
}).set_index("Dates")

#ferier 2028
fev_2028=pd.date_range(start="2028-02-01",end="2028-02-28",freq="B")
n_fev_2028 = len(fev_2028)
quart_fev_2028 = n_fev_2028 // 4
fevrier_2028 =pd.DataFrame({
    "Dates":fev_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_fev_2028,
    "Expérimentation exploratoire":[0]*n_fev_2028,
    "Expérimentation Nièvre":[0]*n_fev_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_fev_2028,
    "Modélisation sur Stics":[0]*(3*quart_fev_2028) + [1]*(n_fev_2028-(3*quart_fev_2028)),
    "Production d'article sientifique":[0]*n_fev_2028,
    "Comité de pilotage de thèse":[0]*n_fev_2028,
    "Analyses et traitements de données":[1]*(3*quart_fev_2028) +[0]*(n_fev_2028-(3*quart_fev_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_fev_2028,
    "Recherches bibliographiques":[0]*n_fev_2028,
    "soutenance de thèse":[0]*n_fev_2028 
}).set_index("Dates")

#mars 2028
mas_2028=pd.date_range(start="2028-03-01",end="2028-03-31",freq="B")
n_mas_2028 = len(mas_2028)
quart_mas_2028 = n_mas_2028 // 4
mars_2028 =pd.DataFrame({
    "Dates":mas_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_mas_2028,
    "Expérimentation exploratoire":[0]*n_mas_2028,
    "Expérimentation Nièvre":[0]*n_mas_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_mas_2028,
    "Modélisation sur Stics":[1]*(3*quart_mas_2028) + [0]*(n_mas_2028-(3*quart_mas_2028)),
    "Production d'article sientifique":[0]*n_mas_2028,
    "Comité de pilotage de thèse":[0]*(3*quart_mas_2028) + [1] + [0]*((n_mas_2028-1)-(3*quart_mas_2028)),
    "Analyses et traitements de données":[0]*(3*quart_mas_2028) +[0] + [1]*((n_mas_2028-1)-(3*quart_mas_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_mas_2028,
    "Recherches bibliographiques":[0]*n_mas_2028,
    "soutenance de thèse":[0]*n_mas_2028 
}).set_index("Dates")

# avril 2028
avl_2028=pd.date_range(start="2028-04-01",end="2028-04-30",freq="B")
n_avl_2028 = len(avl_2028)
quart_avl_2028 = n_avl_2028 // 4
avril_2028 =pd.DataFrame({
    "Dates":avl_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_avl_2028,
    "Expérimentation exploratoire":[0]*n_avl_2028,
    "Expérimentation Nièvre":[1]*n_avl_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_avl_2028,
    "Modélisation sur Stics":[0]*n_avl_2028,
    "Production d'article sientifique":[0]*n_avl_2028,
    "Comité de pilotage de thèse":[0]*n_avl_2028,
    "Analyses et traitements de données":[0]*n_avl_2028,
    "Rédaction de manuscrit de thèse":[0]*n_avl_2028,
    "Recherches bibliographiques":[0]*n_avl_2028,
    "soutenance de thèse":[0]*n_avl_2028
}).set_index("Dates")

# mai 2028
ma_2028=pd.date_range(start="2028-05-01",end="2028-05-31",freq="B")
n_mai_2028 = len(ma_2028)
quart_mai_2028 = n_mai_2028 // 4
mai_2028 =pd.DataFrame({
    "Dates":ma_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_mai_2028,
    "Expérimentation exploratoire":[0]*n_mai_2028,
    "Expérimentation Nièvre":[1]*(2*quart_mai_2028) + [0]*(n_mai_2028-(2*quart_mai_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_mai_2028,
    "Modélisation sur Stics":[0]*(2*quart_mai_2028) + [1]*(n_mai_2028-(2*quart_mai_2028)),
    "Production d'article sientifique":[0]*n_mai_2028,
    "Comité de pilotage de thèse":[0]*n_mai_2028,
    "Analyses et traitements de données":[0]*n_mai_2028,
    "Rédaction de manuscrit de thèse":[0]*n_mai_2028,
    "Recherches bibliographiques":[0]*n_mai_2028,
    "soutenance de thèse":[0]*n_mai_2028
}).set_index("Dates")

# juin 2028
ju_2028=pd.date_range(start="2028-06-01",end="2028-06-30",freq="B")
n_ju_2028 = len(ju_2028)
quart_ju_2028 = n_ju_2028 // 4
juin_2028 =pd.DataFrame({
    "Dates":ju_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_ju_2028,
    "Expérimentation exploratoire":[0]*n_ju_2028,
    "Expérimentation Nièvre":[1]*(2*quart_ju_2028) + [0]*(n_ju_2028-(2*quart_ju_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_ju_2028,
    "Modélisation sur Stics":[0]*(2*quart_ju_2028) + [0]*quart_ju_2028 + [1]*(n_ju_2028-(3*quart_ju_2028)),
    "Production d'article sientifique":[0]*n_ju_2028,
    "Comité de pilotage de thèse":[0]*n_ju_2028,
    "Analyses et traitements de données":[0]*(2*quart_ju_2028) + [1]*quart_ju_2028 + [0]*(n_ju_2028-(3*quart_ju_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_ju_2028,
    "Recherches bibliographiques":[0]*n_ju_2028,
    "soutenance de thèse":[0]*n_ju_2028
}).set_index("Dates")

#juillet 2028
jul_2028=pd.date_range(start="2028-07-01",end="2028-07-31",freq="B")
n_jul_2028 = len(jul_2028)
quart_jul_2028 = n_jul_2028 // 4
juillet_2028 =pd.DataFrame({
    "Dates":jul_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_jul_2028,
    "Expérimentation exploratoire":[0]*n_jul_2028,
    "Expérimentation Nièvre":[1]*(2*quart_jul_2028) + [0]*(n_jul_2028-(2*quart_jul_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_jul_2028,
    "Modélisation sur Stics":[0]*(2*quart_jul_2028) + [0]*quart_jul_2028 + [1]*(n_jul_2028-(3*quart_jul_2028)),
    "Production d'article sientifique":[0]*n_jul_2028,
    "Comité de pilotage de thèse":[0]*n_jul_2028,
    "Analyses et traitements de données":[0]*(2*quart_jul_2028) + [1]*quart_jul_2028 + [0]*(n_jul_2028-(3*quart_jul_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_jul_2028,
    "Recherches bibliographiques":[0]*n_jul_2028,
    "soutenance de thèse":[0]*n_jul_2028 
}).set_index("Dates")

#aout 2028
aou_2028=pd.date_range(start="2028-08-01",end="2028-08-31",freq="B")
n_aou_2028 = len(aou_2028)
quart_aou_2028 = n_aou_2028 // 4
aout_2028 =pd.DataFrame({
    "Dates":aou_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_aou_2028,
    "Expérimentation exploratoire":[0]*n_aou_2028,
    "Expérimentation Nièvre":[1]*(2*quart_aou_2028) + [0]*(n_aou_2028-(2*quart_aou_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_aou_2028,
    "Modélisation sur Stics":[0]*(2*quart_aou_2028) + [0]*quart_aou_2028 + [1]*(n_aou_2028-(3*quart_aou_2028)),
    "Production d'article sientifique":[0]*n_aou_2028,
    "Comité de pilotage de thèse":[0]*n_aou_2028,
    "Analyses et traitements de données":[0]*(2*quart_aou_2028) + [1]*quart_aou_2028 + [0]*(n_aou_2028-(3*quart_aou_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_aou_2028,
    "Recherches bibliographiques":[0]*n_aou_2028,
    "soutenance de thèse":[0]*n_aou_2028
}).set_index("Dates")

# septembre 2028
sep_2028=pd.date_range(start="2028-09-01",end="2028-09-30",freq="B")
n_sep_2028 = len(sep_2028)
quart_sep_2028 = n_sep_2028 // 4
septembre_2028 =pd.DataFrame({
    "Dates":sep_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_sep_2028,
    "Expérimentation exploratoire":[0]*n_sep_2028,
    "Expérimentation Nièvre":[1]*(2*quart_sep_2028) + [0]*(n_sep_2028-(2*quart_sep_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_sep_2028,
    "Modélisation sur Stics":[0]*(2*quart_sep_2028) + [0]*quart_sep_2028 + [1]*(n_sep_2028-(3*quart_sep_2028)),
    "Production d'article sientifique":[0]*n_sep_2028,
    "Comité de pilotage de thèse":[0]*n_sep_2028,
    "Analyses et traitements de données":[0]*(2*quart_sep_2028) + [1]*quart_sep_2028 + [0]*(n_sep_2028-(3*quart_sep_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_sep_2028,
    "Recherches bibliographiques":[0]*n_sep_2028,
    "soutenance de thèse":[0]*n_sep_2028
}).set_index("Dates")

#octobre 2028
# septembre 2028
oct_2028=pd.date_range(start="2028-10-01",end="2028-10-31",freq="B")
n_oct_2028 = len(oct_2028)
quart_oct_2028 = n_oct_2028 // 4
octobre_2028 =pd.DataFrame({
    "Dates":oct_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_oct_2028,
    "Expérimentation exploratoire":[0]*n_oct_2028,
    "Expérimentation Nièvre":[1]*(2*quart_oct_2028) + [0]*(n_oct_2028-(2*quart_oct_2028)),
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_oct_2028,
    "Modélisation sur Stics":[0]*(2*quart_oct_2028) + [0]*quart_oct_2028 + [1]*(n_oct_2028-(3*quart_oct_2028)),
    "Production d'article sientifique":[0]*n_oct_2028,
    "Comité de pilotage de thèse":[0]*n_oct_2028,
    "Analyses et traitements de données":[0]*(2*quart_oct_2028) + [1]*quart_oct_2028 + [0]*(n_oct_2028-(3*quart_oct_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_oct_2028,
    "Recherches bibliographiques":[0]*n_oct_2028,
    "soutenance de thèse":[0]*n_oct_2028
}).set_index("Dates")

# novembre 2028
nov_2028=pd.date_range(start="2028-11-01",end="2028-11-30",freq="B")
n_nov_2028 = len(nov_2028)
quart_nov_2028 = n_nov_2028 // 4
novembre_2028 =pd.DataFrame({
    "Dates":nov_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_nov_2028,
    "Expérimentation exploratoire":[0]*n_nov_2028,
    "Expérimentation Nièvre":[0]*n_nov_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_nov_2028,
    "Modélisation sur Stics":[0]*(3*quart_nov_2028) + [1]*(n_nov_2028-(3*quart_nov_2028)),
    "Production d'article sientifique":[0]*n_nov_2028,
    "Comité de pilotage de thèse":[0]*n_nov_2028,
    "Analyses et traitements de données":[1]*(3*quart_nov_2028) + [0]*(n_nov_2028-(3*quart_nov_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_nov_2028,
    "Recherches bibliographiques":[0]*n_nov_2028,
    "soutenance de thèse":[0]*n_nov_2028
}).set_index("Dates")

#decembre 2028
dec_2028=pd.date_range(start="2028-12-01",end="2028-12-31",freq="B")
n_dec_2028 = len(dec_2028)
quart_dec_2028 = n_dec_2028 // 4
decembre_2028 =pd.DataFrame({
    "Dates":dec_2028,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_dec_2028,
    "Expérimentation exploratoire":[0]*n_dec_2028,
    "Expérimentation Nièvre":[0]*n_dec_2028,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_dec_2028,
    "Modélisation sur Stics":[0]*(3*quart_dec_2028) + [1]*(n_dec_2028-(3*quart_dec_2028)),
    "Production d'article sientifique":[0]*n_dec_2028,
    "Comité de pilotage de thèse":[0]*n_dec_2028,
    "Analyses et traitements de données":[1]*(3*quart_dec_2028) + [0]*(n_dec_2028-(3*quart_dec_2028)),
    "Rédaction de manuscrit de thèse":[0]*n_dec_2028,
    "Recherches bibliographiques":[0]*n_dec_2028,
    "soutenance de thèse":[0]*n_dec_2028 
}).set_index("Dates")

#janvier 2029
janv_2029=pd.date_range(start="2029-01-01",end="2029-01-31",freq="B")
n_janv_2029 = len(janv_2029)
quart_janv_2029 = n_janv_2029 // 4
janvier_2029 =pd.DataFrame({
    "Dates":janv_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_janv_2029,
    "Expérimentation exploratoire":[0]*n_janv_2029,
    "Expérimentation Nièvre":[0]*n_janv_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_janv_2029,
    "Modélisation sur Stics":[1]*(3*quart_janv_2029) + [0]*(n_janv_2029-(3*quart_janv_2029)),
    "Production d'article sientifique":[0]*n_janv_2029,
    "Comité de pilotage de thèse":[0]*n_janv_2029,
    "Analyses et traitements de données":[0]*(3*quart_janv_2029) + [1]*(n_janv_2029-(3*quart_janv_2029)),
    "Rédaction de manuscrit de thèse":[0]*n_janv_2029,
    "Recherches bibliographiques":[0]*n_janv_2029,
    "soutenance de thèse":[0]*n_janv_2029 
}).set_index("Dates")

# fevrier 2029
fev_2029=pd.date_range(start="2029-02-01",end="2029-02-28",freq="B")
n_fev_2029 = len(fev_2029)
quart_fev_2029 = n_fev_2029 // 4
fevrier_2029 =pd.DataFrame({
    "Dates":fev_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_fev_2029,
    "Expérimentation exploratoire":[0]*n_fev_2029,
    "Expérimentation Nièvre":[0]*n_fev_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_fev_2029,
    "Modélisation sur Stics":[0]*n_fev_2029,
    "Production d'article sientifique":[0]*n_fev_2029,
    "Comité de pilotage de thèse":[1] + [0]*(n_fev_2029-1),
    "Analyses et traitements de données":[0] + [1]*(quart_fev_2029)+ [0]*((n_fev_2029-1)-(quart_fev_2029)),
    "Rédaction de manuscrit de thèse":[0] + [0]*(quart_fev_2029)+ [1]*((n_fev_2029-1)-(quart_fev_2029)),
    "Recherches bibliographiques":[0]*n_fev_2029,
    "soutenance de thèse":[0]*n_fev_2029 
}).set_index("Dates")

#mars 2029
mas_2029=pd.date_range(start="2029-03-01",end="2029-03-31",freq="B")
n_mas_2029 = len(mas_2029)
quart_mas_2029 = n_mas_2029 // 4
mars_2029 =pd.DataFrame({
    "Dates":mas_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_mas_2029,
    "Expérimentation exploratoire":[0]*n_mas_2029,
    "Expérimentation Nièvre":[0]*n_mas_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_mas_2029,
    "Modélisation sur Stics":[0]*n_mas_2029,
    "Production d'article sientifique":[0]*n_mas_2029,
    "Comité de pilotage de thèse":[0]*(n_mas_2029),
    "Analyses et traitements de données":[1]*(quart_mas_2029)+ [0]*((n_mas_2029)-(quart_mas_2029)),
    "Rédaction de manuscrit de thèse":[0]*(quart_mas_2029)+ [1]*((n_mas_2029)-(quart_mas_2029)),
    "Recherches bibliographiques":[0]*n_mas_2029,
    "soutenance de thèse":[0]*n_mas_2029 
}).set_index("Dates")

#avril 2029
avl_2029=pd.date_range(start="2029-04-01",end="2029-04-30",freq="B")
n_avl_2029 = len(avl_2029)
quart_avl_2029 = n_avl_2029 // 4
avril_2029 =pd.DataFrame({
    "Dates":avl_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_avl_2029,
    "Expérimentation exploratoire":[0]*n_avl_2029,
    "Expérimentation Nièvre":[0]*n_avl_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_avl_2029,
    "Modélisation sur Stics":[0]*n_avl_2029,
    "Production d'article sientifique":[0]*n_avl_2029,
    "Comité de pilotage de thèse":[0]*(n_avl_2029),
    "Analyses et traitements de données":[0]*(n_avl_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_avl_2029),
    "Recherches bibliographiques":[0]*n_avl_2029,
    "soutenance de thèse":[0]*n_avl_2029 
}).set_index("Dates")

#mai 2029
ma_2029=pd.date_range(start="2029-05-01",end="2029-05-31",freq="B")
n_ma_2029 = len(ma_2029)
quart_ma_2029 = n_ma_2029 // 4
mai_2029 =pd.DataFrame({
    "Dates":ma_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_ma_2029,
    "Expérimentation exploratoire":[0]*n_ma_2029,
    "Expérimentation Nièvre":[0]*n_ma_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_ma_2029,
    "Modélisation sur Stics":[0]*n_ma_2029,
    "Production d'article sientifique":[0]*n_ma_2029,
    "Comité de pilotage de thèse":[0]*(n_ma_2029),
    "Analyses et traitements de données":[0]*(n_ma_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_ma_2029),
    "Recherches bibliographiques":[0]*n_ma_2029,
    "soutenance de thèse":[0]*n_ma_2029 
}).set_index("Dates")

#juin 2029
ju_2029=pd.date_range(start="2029-06-01",end="2029-06-30",freq="B")
n_ju_2029 = len(ju_2029)
quart_ju_2029 = n_ju_2029 // 4
juin_2029 =pd.DataFrame({
    "Dates":ju_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_ju_2029,
    "Expérimentation exploratoire":[0]*n_ju_2029,
    "Expérimentation Nièvre":[0]*n_ju_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_ju_2029,
    "Modélisation sur Stics":[0]*n_ju_2029,
    "Production d'article sientifique":[0]*n_ju_2029,
    "Comité de pilotage de thèse":[0]*(n_ju_2029),
    "Analyses et traitements de données":[0]*(n_ju_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_ju_2029),
    "Recherches bibliographiques":[0]*n_ju_2029,
    "soutenance de thèse":[0]*n_ju_2029 
}).set_index("Dates")

# juillet 2029
jul_2029=pd.date_range(start="2029-07-01",end="2029-07-31",freq="B")
n_jul_2029 = len(jul_2029)
quart_jul_2029 = n_jul_2029 // 4
juillet_2029 =pd.DataFrame({
    "Dates":jul_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_jul_2029,
    "Expérimentation exploratoire":[0]*n_jul_2029,
    "Expérimentation Nièvre":[0]*n_jul_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_jul_2029,
    "Modélisation sur Stics":[0]*n_jul_2029,
    "Production d'article sientifique":[0]*n_jul_2029,
    "Comité de pilotage de thèse":[0]*(n_jul_2029),
    "Analyses et traitements de données":[0]*(n_jul_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_jul_2029),
    "Recherches bibliographiques":[0]*n_jul_2029,
    "soutenance de thèse":[0]*n_jul_2029 
}).set_index("Dates")

# aout 2029
aou_2029=pd.date_range(start="2029-08-01",end="2029-08-31",freq="B")
n_aou_2029 = len(aou_2029)
quart_aou_2029 = n_aou_2029 // 4
aout_2029 = pd.DataFrame({
    "Dates":aou_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_aou_2029,
    "Expérimentation exploratoire":[0]*n_aou_2029,
    "Expérimentation Nièvre":[0]*n_aou_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_aou_2029,
    "Modélisation sur Stics":[0]*n_aou_2029,
    "Production d'article sientifique":[0]*n_aou_2029,
    "Comité de pilotage de thèse":[0]*(n_aou_2029),
    "Analyses et traitements de données":[0]*(n_aou_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_aou_2029),
    "Recherches bibliographiques":[0]*n_aou_2029,
    "soutenance de thèse":[0]*n_aou_2029 
}).set_index("Dates")

# septembre 2029
sep_2029=pd.date_range(start="2029-09-01",end="2029-09-30",freq="B")
n_sep_2029 = len(sep_2029)
quart_sep_2029 = n_sep_2029 // 4
septembre_2029 = pd.DataFrame({
    "Dates":sep_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_sep_2029,
    "Expérimentation exploratoire":[0]*n_sep_2029,
    "Expérimentation Nièvre":[0]*n_sep_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_sep_2029,
    "Modélisation sur Stics":[0]*n_sep_2029,
    "Production d'article sientifique":[0]*n_sep_2029,
    "Comité de pilotage de thèse":[0]*(n_sep_2029),
    "Analyses et traitements de données":[0]*(n_sep_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_sep_2029),
    "Recherches bibliographiques":[0]*n_sep_2029,
    "soutenance de thèse":[0]*n_sep_2029 
}).set_index("Dates")

# octobre 2029
oct_2029=pd.date_range(start="2029-10-01",end="2029-10-31",freq="B")
n_oct_2029 = len(oct_2029)
quart_oct_2029 = n_oct_2029 // 4
octobre_2029 = pd.DataFrame({
    "Dates":oct_2029,
    "Pré-modélisation (analyse de la signature spatio temporelle d'ombrage)":[0]*n_oct_2029,
    "Expérimentation exploratoire":[0]*n_oct_2029,
    "Expérimentation Nièvre":[0]*n_oct_2029,
    "Pré-modélisation (cartographie et clusterring d'ombrage)":[0]*n_oct_2029,
    "Modélisation sur Stics":[0]*n_oct_2029,
    "Production d'article sientifique":[0]*n_oct_2029,
    "Comité de pilotage de thèse":[0]*(n_oct_2029),
    "Analyses et traitements de données":[0]*(n_oct_2029),
    "Rédaction de manuscrit de thèse":[1]*(n_oct_2029-1) +[0],
    "Recherches bibliographiques":[0]*n_oct_2029,
    "soutenance de thèse":[0]*(n_oct_2029-1) +[1]
}).set_index("Dates")



####################################### planning aout a decembre 2026
# aout 2026
aout_2026=pd.date_range(start="2026-08-01",end="2026-08-31",freq="B")
jours_aout = len(aout_2026)
quart_aout_2026 = jours_aout // 4
print(quart_aout_2026)
print(aout_2026)

AOUT = pd.DataFrame({
    "DATES":aout_2026,
    "REDACTION MANUSCRIT":[0]*quart_aout_2026 + [0]*(3)+[1]*(2)+[0]*(jours_aout-((quart_aout_2026 + 3 + 2))),
    "REALISATION DE L'EXPERIMENTATION INTERMITTENCE":[0]*jours_aout,
    "PRODUCTION POSTER FSPM 2026 ":[0]*(quart_aout_2026) + [1]*3 + [0]*(2) + [0]*(2)+[1]*(3) + [0]*(jours_aout - (quart_aout_2026 + 3 + 2 +2 +3)),
    "SOUMMISSION D'ARTICLE ":[0]*(3*quart_aout_2026)+[1]*(jours_aout - (3*quart_aout_2026))}).set_index("DATES")

####################################### planning aout a decembre 2026
# septembre 2026
septembre_2026=pd.date_range(start="2026-09-01",end="2026-09-30",freq="B")
jours_sept = len(septembre_2026)
quart_sept_2026 = jours_sept // 4

SEPT = pd.DataFrame({
    "DATES":septembre_2026,
    "REDACTION MANUSCRIT":[0]*jours_sept,
    "REALISATION DE L'EXPERIMENTATION INTERMITTENCE":[0]*(quart_sept_2026) + [1] * (quart_sept_2026) + [0] * (jours_sept - (2*quart_sept_2026)),
    "PRODUCTION POSTER FSPM 2026":[0]*(jours_sept),
    "SOUMMISSION D'ARTICLE":[1]*(2*quart_sept_2026)+ [1]*(jours_sept - (2*quart_aout_2026))}).set_index("DATES")
        
# octobre 2026
octobre_2026=pd.date_range(start="2026-10-01",end="2026-10-31",freq="B")
jours_oct = len(octobre_2026)
quart_oct_2026 = jours_oct // 4


OCT = pd.DataFrame({
    "DATES":octobre_2026,
    "REDACTION MANUSCRIT":[0]*jours_oct,
    "REALISATION DE L'EXPERIMENTATION INTERMITTENCE":[1]*(quart_oct_2026)+[0]*(quart_oct_2026)+ [0]*(jours_oct-(2*quart_oct_2026)),
    "PRODUCTION POSTER FSPM 2026":[0]*(quart_oct_2026) + [1]*(quart_oct_2026) + [0]*(jours_oct-(2*quart_oct_2026)),
    "SOUMMISSION D'ARTICLE":[1]*(quart_oct_2026) + [0]*(quart_oct_2026) + [1]*(quart_oct_2026) + [1]*(3)+ [0]*(jours_oct-((3*quart_oct_2026)+3))}).set_index("DATES")

# Novembre 2026
novembre_2026=pd.date_range(start="2026-11-01",end="2026-11-30",freq="B")
jours_nov = len(novembre_2026)
quart_nov_2026 = jours_nov // 4

NOV = pd.DataFrame({
    "DATES":novembre_2026,
    "REDACTION MANUSCRIT":[0]*jours_nov,
    "REALISATION DE L'EXPERIMENTATION INTERMITTENCE":[1]*(2*quart_nov_2026) + [0]*(jours_nov-(2*quart_nov_2026)),
    "PRODUCTION POSTER FSPM 2026":[0]*(jours_nov),
    "SOUMMISSION D'ARTICLE":[0]*quart_nov_2026 + [1]*quart_nov_2026 + [1]*(jours_nov -(2*quart_nov_2026))}).set_index("DATES")

# Decembre 2026
decembre_2026=pd.date_range(start="2026-12-01",end="2026-12-31",freq="B")
jours_dec = len(decembre_2026)
quart_dec_2026 = jours_dec // 4


DEC = pd.DataFrame({
    "DATES":decembre_2026,
    "REDACTION MANUSCRIT":[0]*jours_dec,
    "REALISATION DE L'EXPERIMENTATION INTERMITTENCE":[0]*(2*quart_dec_2026) + [1]*(jours_dec-(2*quart_dec_2026)),
    "PRODUCTION POSTER FSPM 2026":[0]*jours_dec,
    "SOUMMISSION D'ARTICLE":[1]*(2*quart_dec_2026)+ [0]*(jours_dec-(2*quart_dec_2026))}).set_index("DATES")

doc=[AOUT,SEPT,OCT,NOV,DEC]

tableau =pd.concat(doc).fillna(0)
tableau.index=pd.to_datetime(tableau.index)
tableau_t=tableau.T
print(tableau.head(10))

#############
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# On regroupe les colonnes similaires et on force le type numérique
df_clean = tableau.copy()
df_clean.columns = [c.strip() for c in df_clean.columns]
df_clean = df_clean.groupby(level=0, axis=1).max().fillna(0).astype(int)
df_clean = df_clean.T.groupby(level=0).max().T.fillna(0).astype(int)
print(df_clean)

# 2. RÉDUIRE L'AFFICHAGE : On passe d'un affichage journalier à HEBDOMADAIRE
#df_clean.resample('W').max() 
df_resampled = df_clean.resample('W').max()


# 1. Somme totale des jours travaillés par colonne
totaux_jours = df_clean.sum()
print(totaux_jours)

# 2. Conversion en semaines (puisque 5 jours = 1 semaine)
totaux_semaines_reels = totaux_jours / 5
print(totaux_semaines_reels)

# Affichage pour contrôle
print("Volume de travail en 'Semaines pleines' :")
print(totaux_semaines_reels.sort_values(ascending=False))

# 3. Configuration du graphique
fig, ax = plt.subplots(figsize=(14, 4))
ax.set_facecolor('white')
fig.patch.set_facecolor('white')


# On dessine la heatmap sur les données resamplées
ax = sns.heatmap(df_resampled.T, 
                 cmap=['white', 'black'], 
                 cbar=False, 
                 linewidths=0.5, 
                 linecolor='lightgray',
                 vmin=0, vmax=1)

# 4. RÉDUIRE LES LABELS SUR L'AXE X
# On ne garde qu'une étiquette de date sur 4 (environ une fois par mois)
locs, labels = plt.xticks()
plt.xticks(locs[::4], [df_resampled.index[int(i)].strftime('%b %Y') for i in locs[::4]], rotation=45)

plt.title("Planning des différentes tâches (echelle Hebdomadaire)", fontsize=12, pad=20)
plt.ylabel("Activités",fontsize=8)
plt.xlabel("Temps (Semaines)",fontsize=8)
plt.yticks(fontsize=6)
plt.xticks(fontsize=6)
donnees_triees = totaux_semaines_reels.sort_values(ascending=False)
texte_stats = "  RÉSUMÉ DES CHARGES  \n"
texte_stats += "  " + "─" * 20 + "  \n"
for activite, total in donnees_triees.items():
    nom = (activite[:25] + '..') if len(activite) > 25 else activite
    texte_stats += f" {nom:<27} : {total:>4.1f} sem \n"

# 3. Ajout du rectangle avec le texte à l'intérieur

# On utilise l'argument 'bbox' pour créer le cadre
fig.text(0.78, 0.5, texte_stats, 
         color='white', 
         fontsize=7, 
         family='monospace',
         va='center', 
         linespacing=1.8,
         transform=fig.transFigure,
         bbox=dict(
             boxstyle='round,pad=1',      # Coins arrondis et marge intérieure
             facecolor="#141414",         # Fond gris très foncé pour le rectangle
             edgecolor='gray',            # Bordure grise
             alpha=0.8                    # Légère transparence pour le style
         ))

# 4. Ajustement pour que le rectangle ne touche pas le graphique
plt.subplots_adjust(left=0.15, right=0.75, top=0.85, bottom=0.2)
plt.show()