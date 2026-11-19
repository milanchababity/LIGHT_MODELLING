import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import warnings; warnings.filterwarnings("ignore")
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun,GenSky
import math 
from dataclasses import dataclass
import pandas as pd 
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo
import os 



from TurbidMedium.sirasca_2d import (
    SpeciesParams, PVPanelParams, RadiativeConfig,
    build_agrivoltaic, build_stratified_mixed,
    run_2d_radiative_balance, run_batch, K_ext,
)


##### option 
AVEC_PV = False 
COMPARE = False # if true that compare soc with sun
BAND_WIDTH = 2.5 # for infinite scene (width band repetitive)
N_Y        = 25 # horizontal division 

### SPECIES PARAMETERS 
# Paramètres disponibles par espèce :
#   name     : nom affiché dans les résultats
#   H        : hauteur de l'espèce (m)
#   LAI      : Leaf Area Index
#   alpha    : angle foliaire moyen (°)  0=planophile, 90=érectophile
#   rho      : réflectance foliaire PAR
#   tau      : transmittance foliaire PAR  (0 = feuilles opaques)
#   y0, y1   : position horizontale dans la bande (fraction de W)
#              None → toute la largeur W (couvert homogène)
#              Ex. y0=0.0, y1=0.5 → demi-bande gauche (rangs séparés)
#   z_haut   : hauteur du sommet depuis le sol (m) — défaut = H
#   z_bas    : hauteur du bas depuis le sol (m) — défaut = 0.0
#   shape_z  : profil vertical  "uniform"|"parabolic"|"gaussian"|"triangular"
#   peak_z   : position du pic vertical (0=sommet, 1=sol, 0.5=milieu)
#   shape_y  : profil horizontal dans la bande  "uniform"|"parabolic"|"gaussian"
#   gap_frac : fraction de la bande vide de chaque côté (H2) — 0 = pas de gap

ESPECES = [
    {
        "name"    : "FETUQUES",
        "H"       : 0.36,       # hauteur (m) — dominante
        "LAI"     : 0.37,
        "alpha"   : 42.4,       # feuilles quasi-verticales
        "rho"     : 0.0,
        "tau"     : 0.0,
        "y0"      : 0.0,      # toute la largeur
        "y1"      : 1.0,
        "z_haut"  : 0.36,
        "z_bas"   : 0.05,      # jusqu'au sol
        "shape_z" : "uniform",
        "peak_z"  : 0.5,
        "shape_y" : "uniform",
        "gap_frac": 0.0,
    },
    {
        "name"    : "LUZERNE",
        "H"       : 0.56,       # hauteur (m) — dominée
        "LAI"     : 0.75,
        "alpha"   : 53.4,       # feuilles quasi-horizontales
        "rho"     : 0.0,
        "tau"     : 0.0,
        "y0"      : 0.0,
        "y1"      : 1.0,
        "z_haut"  : 0.56,
        "z_bas"   : 0.0,
        "shape_z" : "uniform",
        "peak_z"  : 0.5,
        "shape_y" : "uniform",
        "gap_frac": 0.0,
    }]

# ── Panneaux PV (utilisés uniquement si AVEC_PV = True) ────────────────
L_PANNEAU      = 0.85    # longueur dans le plan du panneau (m), direction z-y
L_PANNEAU_LARG = 0.93    # largeur parallèle aux rangs x (m)
BETA_PV        = 0.    # inclinaison depuis l'horizontale (°)
GAMMA_PV       = 180.   # azimut de la normale (° ; 180 = plein Sud)
H_BAS_PV       = 4.0    # hauteur du bas du panneau depuis le sol (m)
RHO_PV         = 0.0   # réflectance face active PAR
TAU_PV         = 0.0    # transmittance (0 = opaque)
OPAQUE_MASK    = True   # True = masque géométrique, False = turbide Beer-Lambert
PAS_X          = 0.0    # pas entre panneaux en x (m) ; 0 = panneaux continus
Y0_PV          = 0.3    # position horizontale gauche (fraction de W)
Y1_PV          = 0.7    # position horizontale droite (fraction de W)

# ── Conditions radiatives ───────────────────────────────────────────────
RHO_SOL    = 0.0   # réflectance du sol
N_AZ_SKY   = 12    # directions azimutales ciel SOC
N_EL_SKY   = 8     # élévations ciel SOC
N_BEAMS    = 30    # faisceaux par couche (précision)
N_RAD_ITER = 6     # itérations Gauss-Seidel radiosités


# Directions solaires : (theta_deg, phi_deg)
# 
def sun_direction (data_meteo,latitude):
    SUN_DIRS=[]
    LST_HOURS=[]
    I0=[]
    FD_VALUES=[]
    
    for i,row in enumerate(data_meteo.itertuples()):
        direct_radiation = float(row.direct_radiation)
        diffuse_r = float(row.diffuse_radiation)
        hours = float(row.decimal_hours)
        day_of_year = int(row.day_of_year)
        if direct_radiation > 0:
            s=Sun.Sun()
            s._set_pos_astro(day_of_year, hours, 3.14 / 180 * latitude)
            if math.degrees(s.elev) < 88.:
                        SUN_DIRS.append((math.degrees(s.elev),180.-math.degrees(s.azim)))
                        I0.append(direct_radiation)
                        FD_VALUES.append(diffuse_r)
                        LST_HOURS.append(hours)
    return SUN_DIRS,LST_HOURS,I0,FD_VALUES
            
# ═══════════════════════════════════════════════════════════════════════
# 1.  RÉSOLUTION DE LA GRILLE VERTICALE
# ═══════════════════════════════════════════════════════════════════════

def get_veg_Max(ESPECES):
    return max(e.get("z_haut", e["H"]) for e in ESPECES)
def get_dz(ESPECES):
    veg_max=get_veg_Max(ESPECES)
    veg_min= max(int(np.ceil(veg_max / 0.10)), 5)
    return veg_max/veg_min

def build_pv(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y):
    H_VEG_MAX=get_veg_Max(ESPECES)
    dz=get_dz(ESPECES)
    
    if AVEC_P==True:
        H_PROJ_PV=L_PANNEAU * np.sin(np.deg2rad(BETA_PV))
        H_HAUT_PV  = H_BAS_PV + H_PROJ_PV
        H_TOTAL    = np.ceil(max(H_HAUT_PV, H_VEG_MAX) / dz) * dz
        N_Z        = int(round(H_TOTAL / dz))
        if H_PROJ_PV > 1e-6:
        # Panneau incliné (β > 0°) : ajuster dz pour que H_PROJ_PV soit
        # un multiple entier de dz (évite les artefacts de discrétisation).
            n_proj = H_PROJ_PV / dz
            if abs(n_proj - round(n_proj)) > 1e-6:
                for N_try in range(N_Z, N_Z + 200):
                    dz_try = H_TOTAL / N_try
                    n_v = H_VEG_MAX / dz_try
                    n_p = H_PROJ_PV / dz_try
                    if abs(n_v - round(n_v)) < 1e-6 and abs(n_p - round(n_p)) < 1e-6:
                        N_Z = N_try; dz = dz_try; break
            N_COUCHES_PV = int(round(H_PROJ_PV / dz))
            # z_fracs : depuis le SOMMET de la grille (convention 0=haut, 1=bas)
            z0_pv = max(0., (H_TOTAL - H_HAUT_PV) / H_TOTAL)
            z1_pv = max(0., (H_TOTAL - H_BAS_PV)  / H_TOTAL)
        else:
            # Panneau horizontal (β = 0°) : h_proj = 0, le panneau tient dans
            # UNE seule couche à la hauteur H_BAS_PV.
            # On pointe z0_pv = z1_pv = fraction correspondant à H_BAS_PV
            # (cas span=0 géré dans build_agrivoltaic).
            N_COUCHES_PV = 1
            z_flat = max(0., (H_TOTAL - H_BAS_PV) / H_TOTAL)
            z0_pv  = z_flat
            z1_pv  = z_flat   # span = 0 → une couche affectée par build_agrivoltaic
    else:
        H_PROJ_PV    = 0.
        H_HAUT_PV    = 0.
        H_TOTAL      = np.ceil(H_VEG_MAX / dz) * dz
        N_Z          = int(round(H_TOTAL / dz))
        N_COUCHES_PV = 0
        z0_pv = z1_pv = 0.
    dy = BAND_WIDTH / N_Y
    return  [H_PROJ_PV,H_HAUT_PV,H_TOTAL,N_Z,N_COUCHES_PV,dy,z0_pv,z1_pv]

# dy = BAND_WIDTH / N_Y
        
# H_VEG_MAX = max(e.get("z_haut", e["H"]) for e in ESPECES)
# N_VEG_MIN  = max(int(np.ceil(H_VEG_MAX / 0.10)), 5)
# dz         = H_VEG_MAX / N_VEG_MIN

# if AVEC_PV:
#     H_PROJ_PV  = L_PANNEAU * np.sin(np.deg2rad(BETA_PV))
#     H_HAUT_PV  = H_BAS_PV + H_PROJ_PV        # hauteur du haut du panneau (m)
#     H_TOTAL    = np.ceil(max(H_HAUT_PV, H_VEG_MAX) / dz) * dz
#     N_Z        = int(round(H_TOTAL / dz))

#     if H_PROJ_PV > 1e-6:
#         # Panneau incliné (β > 0°) : ajuster dz pour que H_PROJ_PV soit
#         # un multiple entier de dz (évite les artefacts de discrétisation).
#         n_proj = H_PROJ_PV / dz
#         if abs(n_proj - round(n_proj)) > 1e-6:
#             for N_try in range(N_Z, N_Z + 200):
#                 dz_try = H_TOTAL / N_try
#                 n_v = H_VEG_MAX / dz_try
#                 n_p = H_PROJ_PV / dz_try
#                 if abs(n_v - round(n_v)) < 1e-6 and abs(n_p - round(n_p)) < 1e-6:
#                     N_Z = N_try; dz = dz_try; break
#         N_COUCHES_PV = int(round(H_PROJ_PV / dz))
#         # z_fracs : depuis le SOMMET de la grille (convention 0=haut, 1=bas)
#         z0_pv = max(0., (H_TOTAL - H_HAUT_PV) / H_TOTAL)
#         z1_pv = max(0., (H_TOTAL - H_BAS_PV)  / H_TOTAL)
#     else:
#         # Panneau horizontal (β = 0°) : h_proj = 0, le panneau tient dans
#         # UNE seule couche à la hauteur H_BAS_PV.
#         # On pointe z0_pv = z1_pv = fraction correspondant à H_BAS_PV
#         # (cas span=0 géré dans build_agrivoltaic).
#         N_COUCHES_PV = 1
#         z_flat = max(0., (H_TOTAL - H_BAS_PV) / H_TOTAL)
#         z0_pv  = z_flat
#         z1_pv  = z_flat   # span = 0 → une couche affectée par build_agrivoltaic
# else:
#     H_PROJ_PV    = 0.
#     H_HAUT_PV    = 0.
#     H_TOTAL      = np.ceil(H_VEG_MAX / dz) * dz
#     N_Z          = int(round(H_TOTAL / dz))
#     N_COUCHES_PV = 0
#     z0_pv = z1_pv = 0.

# dy = BAND_WIDTH / N_Y




def species_extaction(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y):
    data= build_pv(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y)
    
    H_TOTAL=data[2]
    
    veg_params_list = []
    lai_per_veg_list     = []
    height_fracs_list    = []
    y_fracs_veg_list     = []
    lad_shape_veg_list   = []
    lad_peak_veg_list    = []
    lad_shape_y_veg_list = []
    gap_frac_veg_list    = []
    for e in ESPECES:
        veg_params_list.append(SpeciesParams(
            e["name"], alpha_deg=e["alpha"], rho=e["rho"], tau_leaf=e["tau"]))
        lai_per_veg_list.append(e["LAI"])
        z_haut_e = e.get("z_haut", e["H"])
        z_bas_e  = e.get("z_bas") if e.get("z_bas") is not None else 0.0
        z0_e = max(0., (H_TOTAL - z_haut_e) / H_TOTAL)
        z1_e = min(1., (H_TOTAL - z_bas_e)  / H_TOTAL)
        height_fracs_list.append((z0_e, z1_e))
        y0_e = e.get("y0") if e.get("y0") is not None else 0.0
        y1_e = e.get("y1") if e.get("y1") is not None else 1.0
        y_fracs_veg_list.append((y0_e, y1_e))
        lad_shape_veg_list.append(e.get("shape_z", "parabolic"))
        lad_peak_veg_list.append(e.get("peak_z",   0.5))
        lad_shape_y_veg_list.append(e.get("shape_y", "uniform"))
        gap_frac_veg_list.append(e.get("gap_frac",  0.0))
        
    return veg_params_list,lai_per_veg_list,height_fracs_list,\
        y_fracs_veg_list,lad_shape_veg_list,lad_peak_veg_list,\
        lad_shape_y_veg_list,gap_frac_veg_list
        
# veg_params_list      = []
# lai_per_veg_list     = []
# height_fracs_list    = []
# y_fracs_veg_list     = []
# lad_shape_veg_list   = []
# lad_peak_veg_list    = []
# lad_shape_y_veg_list = []
# gap_frac_veg_list    = []    
    

# for e in ESPECES:
#     veg_params_list.append(SpeciesParams(
#         e["name"], alpha_deg=e["alpha"], rho=e["rho"], tau_leaf=e["tau"]))
#     lai_per_veg_list.append(e["LAI"])
#     z_haut_e = e.get("z_haut", e["H"])
#     z_bas_e  = e.get("z_bas") if e.get("z_bas") is not None else 0.0
#     z0_e = max(0., (H_TOTAL - z_haut_e) / H_TOTAL)
#     z1_e = min(1., (H_TOTAL - z_bas_e)  / H_TOTAL)
#     height_fracs_list.append((z0_e, z1_e))
#     y0_e = e.get("y0") if e.get("y0") is not None else 0.0
#     y1_e = e.get("y1") if e.get("y1") is not None else 1.0
#     y_fracs_veg_list.append((y0_e, y1_e))
#     lad_shape_veg_list.append(e.get("shape_z", "parabolic"))
#     lad_peak_veg_list.append(e.get("peak_z",   0.5))
#     lad_shape_y_veg_list.append(e.get("shape_y", "uniform"))
#     gap_frac_veg_list.append(e.get("gap_frac",  0.0))

# N_VEG = len(ESPECES)

# if AVEC_PV:
#         pv = PVPanelParams(
#             'PV', beta_deg=BETA_PV, gamma_deg=GAMMA_PV,
#             rho_pv=RHO_PV, tau_pv=TAU_PV,
#             pas_x=PAS_X, opaque_mask=OPAQUE_MASK,
#         )
#         geo, species = build_agrivoltaic(
#             veg_params        = veg_params_list,
#             lai_per_veg       = lai_per_veg_list,
#             height_fracs_veg  = height_fracs_list,
#             y_fracs_veg       = y_fracs_veg_list,
#             lad_shape_veg     = lad_shape_veg_list,
#             lad_peak_veg      = lad_peak_veg_list,
#             lad_shape_y_veg   = lad_shape_y_veg_list,
#             gap_frac_veg      = gap_frac_veg_list,
#             pv_params         = [pv],
#             l_panneau_pv      = [L_PANNEAU_LARG],
#             y_fracs_pv        = [(Y0_PV, Y1_PV)],
#             z_fracs_pv        = [(z0_pv, z1_pv)],
#             canopy_height     = H_TOTAL,
#             band_width        = BAND_WIDTH,
#             N_z               = N_Z,
#             N_y               = N_Y,
#             lad_shape         = 'parabolic',
#             lad_peak_frac     = 0.5,
#         )
#         N_PV = 1
# else:
#         # Panneau fictif transparent (PAD=0, tau=1) : n'affecte pas le calcul
#         pv_null = PVPanelParams(
#             'PV_nul', beta_deg=0., gamma_deg=180.,
#             rho_pv=0., tau_pv=1., opaque_mask=False,
#         )
#         geo, species = build_agrivoltaic(
#             veg_params        = veg_params_list,
#             lai_per_veg       = lai_per_veg_list,
#             height_fracs_veg  = height_fracs_list,
#             y_fracs_veg       = y_fracs_veg_list,
#             lad_shape_veg     = lad_shape_veg_list,
#             lad_peak_veg      = lad_peak_veg_list,
#             lad_shape_y_veg   = lad_shape_y_veg_list,
#             gap_frac_veg      = gap_frac_veg_list,
#             pv_params         = [pv_null],
#             l_panneau_pv      = [0.],
#             y_fracs_pv        = [(0., 1.)],
#             z_fracs_pv        = [(0., 1. / N_Z)],
#             canopy_height     = H_TOTAL,
#             band_width        = BAND_WIDTH,
#             N_z               = N_Z,
#             N_y               = N_Y,
#             lad_shape         = 'parabolic',
#             lad_peak_frac     = 0.5,
#         )
#         N_PV = 0

# base_cfg = RadiativeConfig(
#     I0=1., theta_sun_deg=30., phi_sun_deg=180., fd=0.15,
#     rho_soil=RHO_SOL, n_az_sky=N_AZ_SKY, n_el_sky=N_EL_SKY,
#     n_beams_per_layer=N_BEAMS, n_radiosity_iter=N_RAD_ITER,
# )

# mode_label = "AGRIVOLTAÏQUE (avec PV)" if AVEC_PV else "VÉGÉTATION SEULE (sans PV)"


# base_cfg = RadiativeConfig(
#     I0=1., theta_sun_deg=30., phi_sun_deg=180., fd=0.15,
#     rho_soil=RHO_SOL, n_az_sky=N_AZ_SKY, n_el_sky=N_EL_SKY,
#     n_beams_per_layer=N_BEAMS, n_radiosity_iter=N_RAD_ITER,
# )



# lad_veg = [geo.LAD_grids[s].mean(axis=1) for s in range(N_VEG)]
# pad_pv  =  geo.LAD_grids[N_VEG].mean(axis=1) if AVEC_PV else np.zeros(N_Z)
# all_lad_vals = lad_veg + ([pad_pv] if AVEC_PV else [])
# lad_max = max((v.max() for v in all_lad_vals), default=1e-6)
# lad_max = max(lad_max, 1e-6)


# LAD_table=pd.DataFrame({"LAD_Vege":lad_veg})

# nonzero = [i for i in range(N_Z)
#            if any(lad_veg[s][i] > 0 for s in range(N_VEG))
#            or (AVEC_PV and pad_pv[i] > 0)]
# i_min = max(0, nonzero[0] - 1) if nonzero else 0
# i_max = min(N_Z - 1, nonzero[-1] + 1) if nonzero else N_Z - 1

# latitude = 46.43
# DOY = 172

# SUN_DIRS = []
# LST_HOURS = []
# VAR=np.arange(4,22,1)
# for hour in VAR:
# #[10,12]:#np.arange(0, 24, 1./4.):
#     s = Sun.Sun()
#     s._set_pos_astro(DOY, hour, 3.14 / 180 * latitude)
#     if math.degrees(s.elev) < 88.:
#         SUN_DIRS.append((math.degrees(s.elev),180.-math.degrees(s.azim)))
#         LST_HOURS.append(hour)

# # Fractions diffuses
# data_meteo=recup_meteo.recup_direct_diffuse (latitude,0.116670,"2025-06-25","2025-06-25")
# FD_VALUES = [0]*len(SUN_DIRS)


# batch = run_batch(
#     geo, species, base_cfg,
#     sun_dirs  = SUN_DIRS,
#     fd_values = FD_VALUES,
#     lst_hours = LST_HOURS,
#     verbose   = False,
#     I0=1
# )


def SCENE_constructor(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y):
    veg_params_list,lai_per_veg_list,height_fracs_list,y_fracs_veg_list,lad_shape_veg_list,lad_peak_veg_list,lad_shape_y_veg_list,gap_frac_veg_list=species_extaction(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y)
    Data_= build_pv(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y)
    
    z0_pv=Data_[6]
    z1_pv =Data_[7]
    H_TOTAL=Data_[2]
    N_Z=Data_[3]
    
    if AVEC_P==True:
        pv = PVPanelParams(
            'PV', beta_deg=BETA_PV, gamma_deg=GAMMA_PV,
            rho_pv=RHO_PV, tau_pv=TAU_PV,
            pas_x=PAS_X, opaque_mask=OPAQUE_MASK,
        )
        geo, species = build_agrivoltaic(
            veg_params        = veg_params_list,
            lai_per_veg       = lai_per_veg_list,
            height_fracs_veg  = height_fracs_list,
            y_fracs_veg       = y_fracs_veg_list,
            lad_shape_veg     = lad_shape_veg_list,
            lad_peak_veg      = lad_peak_veg_list,
            lad_shape_y_veg   = lad_shape_y_veg_list,
            gap_frac_veg      = gap_frac_veg_list,
            pv_params         = [pv],
            l_panneau_pv      = [L_PANNEAU_LARG],
            y_fracs_pv        = [(Y0_PV, Y1_PV)],
            z_fracs_pv        = [(z0_pv, z1_pv)],
            canopy_height     = H_TOTAL,
            band_width        = BAND_WIDTH,
            N_z               = N_Z,
            N_y               = N_Y,
            lad_shape         = 'parabolic',
            lad_peak_frac     = 0.5,
            row_azimuth_deg= 90,
            

        )
        N_PV = 1
    else:
        # Panneau fictif transparent (PAD=0, tau=1) : n'affecte pas le calcul
        pv_null = PVPanelParams(
            'PV_nul', beta_deg=0., gamma_deg=180.,
            rho_pv=0., tau_pv=1., opaque_mask=False,
        )
        geo, species = build_agrivoltaic(
            veg_params        = veg_params_list,
            lai_per_veg       = lai_per_veg_list,
            height_fracs_veg  = height_fracs_list,
            y_fracs_veg       = y_fracs_veg_list,
            lad_shape_veg     = lad_shape_veg_list,
            lad_peak_veg      = lad_peak_veg_list,
            lad_shape_y_veg   = lad_shape_y_veg_list,
            gap_frac_veg      = gap_frac_veg_list,
            pv_params         = [pv_null],
            l_panneau_pv      = [0.],
            y_fracs_pv        = [(0., 1.)],
            z_fracs_pv        = [(0., 1. / N_Z)],
            canopy_height     = H_TOTAL,
            band_width        = BAND_WIDTH,
            N_z               = N_Z,
            N_y               = N_Y,
            lad_shape         = 'parabolic',
            lad_peak_frac     = 0.5,
            row_azimuth_deg = 90,
           
        )
        N_PV = 0
    N_VEG = len(ESPECES)
    return geo, species,N_PV,N_Z,N_VEG

def rad_set_up(theta_sun_deg,phi_sun_deg,fd,rho_soil,n_az_sky,
               n_el_sky,n_beams_per_layer,n_radiosity_iter,I0):
    return RadiativeConfig(I0=1., theta_sun_deg=theta_sun_deg, phi_sun_deg=phi_sun_deg, fd=fd,
    rho_soil=rho_soil, n_az_sky=n_az_sky, n_el_sky=n_el_sky,
    n_beams_per_layer=n_beams_per_layer, n_radiosity_iter=n_radiosity_iter)
    
radiative=rad_set_up(I0=1., theta_sun_deg=30., phi_sun_deg=180., fd=0.15,
     rho_soil=RHO_SOL, n_az_sky=N_AZ_SKY, n_el_sky=N_EL_SKY,
     n_beams_per_layer=N_BEAMS, n_radiosity_iter=N_RAD_ITER)
    
    
mode_label = "AGRIVOLTAÏQUE (avec PV)" if AVEC_PV else "VÉGÉTATION SEULE (sans PV)"

# ═══════════════════════════════════════════════════════════════════════
# 4.  PROFILS LAD/PAD
# ═══════════════════════════════════════════════════════════════════════

def lad_profil(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y):
    geo,species,N_V,N_Z,N_VEG=SCENE_constructor(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y)
    lad_veg = [geo.LAD_grids[s].mean(axis=1) for s in range(N_VEG)]
    pad_pv  =  geo.LAD_grids[N_VEG].mean(axis=1) if AVEC_PV else np.zeros(N_Z)
    all_lad_vals = lad_veg + ([pad_pv] if AVEC_PV else [])
    lad_max = max((v.max() for v in all_lad_vals), default=1e-6)
    lad_max = max(lad_max, 1e-6)

    nonzero = [i for i in range(N_Z)
            if any(lad_veg[s][i] > 0 for s in range(N_VEG))
            or (AVEC_PV and pad_pv[i] > 0)]
    i_min = max(0, nonzero[0] - 1) if nonzero else 0
    i_max = min(N_Z - 1, nonzero[-1] + 1) if nonzero else N_Z - 1
    
    return i_min,i_max
    
def sun_pos_fonction (latitude,doy):
   
    DOY = doy
    SUN_DIRS = []
    LST_HOURS = []
    VAR=[10]
    for hour in VAR:
    #[10,12]:#np.arange(0, 24, 1./4.):
        s = Sun.Sun()
        s._set_pos_astro(DOY, hour, 3.14 / 180 * latitude)
        if math.degrees(s.elev) < 88.:
            SUN_DIRS.append((math.degrees(s.elev),180.-math.degrees(s.azim)))
            LST_HOURS.append(hour)
    return SUN_DIRS,LST_HOURS

def fraction_diffus(data_meteo):
    fd_diffuse = []
    direct_radiation = []
    diffuse_radiation = []
    time = []

    for row in data_meteo.itertuples():

        direct = float(row.direct_radiation)
        diffuse = float(row.diffuse_radiation)
        heure = float(row.decimal_hours)

     
        if (direct > 0) or (diffuse > 0):
            fraction = diffuse / (direct + diffuse)
        else:
            fraction = 0.0

       
        fd_diffuse.append(fraction)
        direct_radiation.append(direct)
        diffuse_radiation.append(diffuse)
        time.append(heure)

    fac_dir_diff = pd.DataFrame({
        "HOURS": time,
        "Direct_radiation": direct_radiation,
        "Diffuse_radiation": diffuse_radiation,
        "fd": fd_diffuse
    }).set_index("HOURS")

    return fd_diffuse, fac_dir_diff


def data_compute (batch_result,name,LST_HOURS,species1_name,species2_name):
    direct_f = pd.DataFrame(batch_result.frac_abs_direct,columns=[f"{sp}_direct" for sp in batch_result.species_names])
    direct_f.insert(0, "HOURS", LST_HOURS)
    direct_f.set_index("HOURS", inplace=True)

    diffuse_f = pd.DataFrame(
    batch_result.frac_abs_diffuse,columns=[f"{sp}_diffuse" for sp in batch_result.species_names])
    diffuse_f.insert(0, "HOURS", LST_HOURS)
    diffuse_f.set_index("HOURS", inplace=True)

    data_final = pd.concat(
    [direct_f, diffuse_f],
    axis=1,
    join="outer")
    data_final["TREATMENTS"]=name
    data_final["species_1"]=species1_name
    data_final["species_2"]=species2_name
    
    return data_final



# # Fractions diffuses
# data_meteo=recup_meteo.recup_direct_diffuse (latitude,0.116670,"2025-06-25","2025-06-25")

def all_simulation(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y,theta_sun_deg,
                   phi_sun_deg,fd,rho_soil,n_az_sky,n_el_sky,n_beams_per_layer,
                   n_radiosity_iter,I0,latitude,doy,debut,fin,name,species1_name,species2_name):
    
    geo,species,_,_,_ =SCENE_constructor(ESPECES,AVEC_P,L_PANNEAU,BETA_PV,H_BAS_PV,BAND_WIDTH, N_Y)
    
    base_confg=rad_set_up(theta_sun_deg,phi_sun_deg,fd,rho_soil,n_az_sky,
               n_el_sky,n_beams_per_layer,n_radiosity_iter,I0)
    
    Sun_dir,lst_hr=sun_pos_fonction (latitude,doy)
    
    data_meteo=recup_meteo.recup_direct_diffuse (latitude,0.116670,debut,fin)
    
    # lst_diffuse,_=fraction_diffus(data_meteo)
    lst_diffuse=[0.0]*len(Sun_dir)
    
    batch=run_batch(geo,species,base_confg,
                    sun_dirs=Sun_dir,
                    fd_values=lst_diffuse,
                    lst_hours=lst_hr,
                    verbose=True,
                    I0=1)
    data_final=data_compute(batch,name,lst_hr,species1_name,species2_name)
    return data_final,batch




if __name__=="__main__":
    
    recup_meteo.log("ALFALFA_FESCUE MIXTURE SIMULATIONS")
    
    Band_HD1=0.31
    Band_LD1=0.34
    Band_WP_300=0.34
    Band_WP_1100=0.42
    Band_FC=0.10
    
    # THERE IS TWO OPTIONS 
    AVEC_PV_TRUE = True 
    AVEC_PV_FALSE= False
    
    COMPARE_TRUE = False # if true that compare soc with sun
    COMPARE_FALSE=False
    
    # geometry ALFALFA_FESCUE HD1 
    BAND_WIDTH = 2.12 # for infinite scene (width band repetitive)
    N_Y        = 25 # horizontal division 
    
    recup_meteo.log("LOADING ALFALFA_FESCUE PARAMETERS_HD1")
    ESPECES_AF_HD1 = [
    {
        "name"    : "ESPECE_1", #ALFLAFA HD1
        "H"       : 0.32,       
        "LAI"     : 3.83,
        "alpha"   : 42.4,       
        "rho"     : 0.0,
        "tau"     : 0.0,
        "y0"      : 0.,      # toute la largeur
        "y1"      : 0.5,
        "z_haut"  : 0.32,   # Height ALFALFA 
        "z_bas"   : 0.00,      # jusqu'au sol
        "shape_z" : "triangular",
        "peak_z"  : 0.5,
        "shape_y" : "uniform",
        "gap_frac": 0.0,
    },
    {
        "name"    : "ESPECE_2",
        "H"       : 0.352,       # hauteur (m) — dominée
        "LAI"     : 3.06,
        "alpha"   : 53.4,       # feuilles quasi-horizontales
        "rho"     : 0.0,
        "tau"     : 0.0,
        "y0"      : 0.5,
        "y1"      : 1.0,
        "z_haut"  : 0.352,
        "z_bas"   : 0.0,
        "shape_z" : "triangular",
        "peak_z"  : 0.5,
        "shape_y" : "uniform",
        "gap_frac": 0.0,
    }]
    
    ESPECES_AF_HD2 = [
        {
            "name"    : "ESPECE_1",
            "H"       : 0.54,       # hauteur (m) — dominante
            "LAI"     : 8.06,
            "alpha"   : 42.4,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.54,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2",
            "H"       : 0.40,      
            "LAI"     : 2.52,
            "alpha"   : 53.4,       
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.35,
            "z_bas"   : 0.0,
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    ESPECES_AF_LD1 = [
        {
            "name"    : "ESPECE_1",
            "H"       : 0.31,       # hauteur (m) — dominante
            "LAI"     : 0.37,
            "alpha"   : 42.4,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.31,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2",
            "H"       : 0.51,       # hauteur (m) — dominée
            "LAI"     : 0.75,
            "alpha"   : 53.4,       # feuilles quasi-horizontales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.35,
            "z_bas"   : 0.0,
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    ESPECES_AF_LD2 = [
        {
            "name"    : "ESPECE_1",
            "H"       : 0.62,       # hauteur (m) — dominante
            "LAI"     : 1.70,
            "alpha"   : 42.4,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.0,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.54,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2",
            "H"       : 0.48,       # hauteur (m) — dominée
            "LAI"     : 0.43,
            "alpha"   : 53.4,       # feuilles quasi-horizontales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.35,
            "z_bas"   : 0.0,
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    recup_meteo.log("WHEAT_PEA PARAMETERS LOADING ")
    ESPECES_WPEA_300 = [
        {
            "name"    : "ESPECE_1", ## PEA 
            "H"       : 0.15,       # hauteur (m) — dominante
            "LAI"     : 0.15,
            "alpha"   : 36,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.15,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2", #WHEAT 
            "H"       : 0.19,       # hauteur (m) — dominée
            "LAI"     : 0.31,
            "alpha"   : 37.1,       # feuilles quasi-horizontales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.19,
            "z_bas"   : 0.0,
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    ESPECES_WPEA_1100 = [
        {
            "name"    : "ESPECE_1",# PEA
            "H"       : 0.29,       # hauteur (m) — dominante
            "LAI"     : 0.19,
            "alpha"   : 36,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.0,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.29,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2", #wheat
            "H"       : 0.43,       # hauteur (m) — dominée
            "LAI"     : 2.56,
            "alpha"   : 37.1,       # feuilles quasi-horizontales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.43,
            "z_bas"   : 0.0,
            "shape_z" :"triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    recup_meteo.log("FESCUE_CLOVER_PARAMETERS LOADING")
    
    ESPECES_FE_AS05C1 = [
        {
            "name"    : "ESPECE_1",# CLOVER
            "H"       : 0.03,       # hauteur (m) — dominante
            "LAI"     : 0.05,
            "alpha"   : 27.2,       # feuilles quasi-verticales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.0,      # toute la largeur
            "y1"      : 0.5,
            "z_haut"  : 0.03,
            "z_bas"   : 0.00,      # jusqu'au sol
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        },
        {
            "name"    : "ESPECE_2", #Fescue
            "H"       : 0.25,       # hauteur (m) — dominée
            "LAI"     : 2.06,
            "alpha"   : 58.3,       # feuilles quasi-horizontales
            "rho"     : 0.0,
            "tau"     : 0.0,
            "y0"      : 0.5,
            "y1"      : 1.0,
            "z_haut"  : 0.25,
            "z_bas"   : 0.0,
            "shape_z" : "triangular",
            "peak_z"  : 0.5,
            "shape_y" : "uniform",
            "gap_frac": 0.0,
        }]
    
    ESPECES_FE_AS05C3 = [
            {
                "name"    : "ESPECE_1",# CLOV
                "H"       : 0.04,       # hauteur (m) — dominante
                "LAI"     : 0.08,
                "alpha"   : 27.2,       # feuilles quasi-verticales
                "rho"     : 0.0,
                "tau"     : 0.0,
                "y0"      : 0.,      # toute la largeur
                "y1"      : 0.5,
                "z_haut"  : 0.04,
                "z_bas"   : 0.00,      # jusqu'au sol
                "shape_z" :"triangular",
                "peak_z"  : 0.5,
                "shape_y" : "uniform",
                "gap_frac": 0.0,
            },
            {
                "name"    : "ESPECE_2", #Fescue
                "H"       : 0.1,       # hauteur (m) — dominée
                "LAI"     : 0.6,
                "alpha"   : 58.3,       # feuilles quasi-horizontales
                "rho"     : 0.0,
                "tau"     : 0.0,
                "y0"      : 0.5,
                "y1"      : 1.0,
                "z_haut"  : 0.1,
                "z_bas"   : 0.0,
                "shape_z" : "triangular",
                "peak_z"  : 0.5,
                "shape_y" : "uniform",
                "gap_frac": 0.0,
            }]
    
    
    recup_meteo.log("LOADING PANELS PARAMETERS AFALFA_FESCUE HD1")
        
    # L_PANNEAU_HD1_HD2      = 0.93   # longueur dans le plan du panneau (m), direction z-y
    # L_PANNEAU_LARG_HD1_HD2 = 0.97    # largeur parallèle aux rangs x (m)
    # L_PANNEAU_LD1_LD2      = 1.02    # longueur dans le plan du panneau (m), direction z-y
    # L_PANNEAU_LARG_LD1_LD2 = 1.14
    
            
    # L_PANNEAU_WH_PEA_300      = 0.84   # longueur dans le plan du panneau (m), direction z-y
    # L_PANNEAU_LARG_WH_PEA_300 = 0.98
    
    # L_PANNEAU_WH_PEA_1100     = 1.02   # longueur dans le plan du panneau (m), direction z-y
    # L_PANNEAU_LARG_WH_PEA_1100 = 0.98 
    
    # L_PANNEAU_FES_CLV      = 1   # longueur dans le plan du panneau (m), direction z-y
    # L_PANNEAU_LARG_FES_CLV = 0.98
    
    L_PANNEAU_HD1_HD2      = 0.11   # longueur dans le plan du panneau (m), direction z-y
    L_PANNEAU_LARG_HD1_HD2 = 0.30  # largeur parallèle aux rangs x (m)
    L_PANNEAU_LD1_LD2      = 0.12   # longueur dans le plan du panneau (m), direction z-y
    L_PANNEAU_LARG_LD1_LD2 = 1.06
    
            
    L_PANNEAU_WH_PEA_300      = 0.12 # longueur dans le plan du panneau (m), direction z-y
    L_PANNEAU_LARG_WH_PEA_300 = 0.34
    
    L_PANNEAU_WH_PEA_1100     = 0.15  # longueur dans le plan du panneau (m), direction z-y
    L_PANNEAU_LARG_WH_PEA_1100 = 0.34
    
    L_PANNEAU_FES_CLV      = 0.04  # longueur dans le plan du panneau (m), direction z-y
    L_PANNEAU_LARG_FES_CLV = 0.36
    
    
    BETA_PV        = 0.   # inclinaison depuis l'horizontale (°) inclinaison azimuthale (par rapport au sol)
    GAMMA_PV       = 180   # azimut de la normale (° ; 180 == plein Sud)
    H_BAS_PV       = 4    
    RHO_PV         = 0.0   
    TAU_PV         = 0.0   
    OPAQUE_MASK    = True   
    PAS_X          = 0.0    
    Y0_PV          = 0.34    
    Y1_PV          = 0.70    


    recup_meteo.log("PARAMETERS USED FOR ALL SIMULATION")
    # ── Conditions radiatives ───────────────────────────────────────────────
    RHO_SOL    = 0.15  # réflectance du sol
    N_AZ_SKY   = 12    # directions azimutales ciel SOC
    N_EL_SKY   = 8     # élévations ciel SOC
    N_BEAMS    = 30    # faisceaux par couche (précision)
    N_RAD_ITER = 6     # itérations Gauss-Seidel radiosités

    
    LONGITUDE=3.256 # longitude Entrains sur Nouhain 
    LATITUDE=47.464 # latitude Entrains sur Nouhain
    DOY= 172 # day of year du 21 juin 
    DEBUT="2025-06-25" # pas de temps 1 heure
    FIN="2025-06-25"
    
    data_meteo=recup_meteo.recup_direct_diffuse (LATITUDE,LONGITUDE,DEBUT,FIN)
    _,dataframe_mult=fraction_diffus(data_meteo)
    
    def concat_table_mult(dataframe, diffus):
        dataf_final=pd.concat([dataframe,diffus],axis=1,ignore_index=False,join="outer")
        return dataf_final
    
    def concat_all_table(list_dataframe):
        dataframe=pd.concat(list_dataframe,axis=0,ignore_index=False,join="outer")
        return dataframe
        
    
    recup_meteo.log("SIMULATION HD1")

    
    HD1_pv,data_1=all_simulation(ESPECES=ESPECES_AF_HD1,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_HD1_HD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_HD1, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="HD1_SUD_0DEG_P_SUD",species1_name="ALFA_PV_HD1_0DEG",species2_name="FESC_PV_HD1_0DEG")
    HD1_tot=concat_table_mult(HD1_pv,dataframe_mult)
    
    
    HD1_no_pv,data_2=all_simulation(ESPECES=ESPECES_AF_HD1,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_HD1_HD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_HD1, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="HD1_SUD_0DEG_NO_SUD",species1_name="ALFA_CONT_HD1_0DEG",species2_name="FESC_CONT_HD1_0DEG")

    HD1_no_tot=concat_table_mult(HD1_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION HD2")
    HD2_pv,data_hd2=all_simulation(ESPECES=ESPECES_AF_HD2,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_HD1_HD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_HD1, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="HD2_SUD_0DEG_P_SUD",species1_name="ALFA_PV_HD2_0DEG",species2_name="FESC_PV_HD2_0DEG")
    HD2_tot=concat_table_mult(HD2_pv,dataframe_mult)
    
    HD2_no_pv,data_no_hd2=all_simulation(ESPECES=ESPECES_AF_HD2,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_HD1_HD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_HD1, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="HD2_SUD_0DEG_NO_SUD",species1_name="ALFA_CONT_HD2_0DEG",species2_name="FESC_CONT_HD2_0DEG")
    HD2_no_tot=concat_table_mult(HD2_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION LD1")
    LD1_pv,data_ld1=all_simulation(ESPECES=ESPECES_AF_LD1,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_LD1_LD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_LD1, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="LD1_SUD_0DEG_P_SUD",species1_name="ALFA_PV_LD1_0DEG",species2_name="FESC_PV_LD1_0DEG")
    LD1_tot=concat_table_mult(LD1_pv,dataframe_mult)
    
    LD1_no_pv,data_no_ld1=all_simulation(ESPECES=ESPECES_AF_LD1,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_LD1_LD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_LD1, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="LD1_SUD_0DEG_NO_SUD",species1_name="ALFA_CONT_LD1_0DEG",species2_name="FESC_CONT_LD1_0DEG")
    LD1_no_tot=concat_table_mult(LD1_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION LD2")
    
    LD2_pv,data_ld2=all_simulation(ESPECES=ESPECES_AF_LD2,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_LD1_LD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_LD1, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="LD2_SUD_0DEG_P_SUD",species1_name="ALFA_PV_LD2_0DEG",species2_name="FESC_PV_LD2_0DEG")
    LD2_pv_tot=concat_table_mult(LD2_pv,dataframe_mult)
    
    LD2_no_pv,data_no_ld2=all_simulation(ESPECES=ESPECES_AF_LD2,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_LD1_LD2,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_LD1, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="LD2_SUD_0DEG_NO_SUD",species1_name="ALFA_CONT_LD2_0DEG",species2_name="FESC_CONT_LD2_0DEG")
    LD2_no_tot=concat_table_mult(LD2_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION WHEAT_PEA 300")
    
    W_PEA_300_pv,data_XP_300=all_simulation(ESPECES=ESPECES_WPEA_300,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_WH_PEA_300,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_WP_300, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="WP_300_SUD_0DEG_P_SUD",species1_name="PEA_PV_300_ODEG",species2_name="WHE_PV_300_0DEG")
    W_PEA_300_tot=concat_table_mult(W_PEA_300_pv,dataframe_mult)
    
    W_PEA_300_no_pv,data_XP_300_no=all_simulation(ESPECES=ESPECES_WPEA_300,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_WH_PEA_300,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_WP_300, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="WP_300_SUD_0DEG_NO_SUD", species1_name="PEA_CONT_300_ODEG",species2_name="WHE_CONT_300_ODEG")
    W_P_NO_300_tot=concat_table_mult(W_PEA_300_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION WHEAT_PEA 1100")
    
    W_PEA_1100_pv,data_XP_1100=all_simulation(ESPECES=ESPECES_WPEA_1100,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_WH_PEA_1100,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_WP_1100, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="WP_1100_SUD_0DEG_P_SUD",species1_name="PEA_PV_1100_0DEG",species2_name="WHE_PV_1100_0DEG")
   
    W_PEA_1100_tot=concat_table_mult(W_PEA_1100_pv,dataframe_mult)
    
    W_PEA_1100_no_pv,data_XP_1100_no=all_simulation(ESPECES=ESPECES_WPEA_1100,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_WH_PEA_1100,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_WP_1100, N_Y=N_Y,theta_sun_deg=30,
                       phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                       n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="WP_1100_SUD_0DEG_NO_SUD", species1_name="PEA_CONT_1100_0DEG",species2_name="WHE_CONT_1100_0DEG")
    
    W_P_NO_1100_tot=concat_table_mult(W_PEA_1100_no_pv,dataframe_mult)
    
    recup_meteo.log("SIMULATION FESCUE_CLOVE AS3C1")
    
    FE_CL_AS3C1_pv,data_XP_AS3C1=all_simulation(ESPECES=ESPECES_FE_AS05C1,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_FES_CLV,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_FC, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="AS3C1_SUD_0DEG_P_SUD",species1_name="CLV_PV_AS3C1_0DEG",species2_name="FES_PV_AS3C1_0DEG")
    
    FE_CL_AS3C1_pv_tot=concat_table_mult(FE_CL_AS3C1_pv,dataframe_mult)
    
    FE_CL_AS3C1_NO,data_XP_AS3C1_NO=all_simulation(ESPECES=ESPECES_FE_AS05C1,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_FES_CLV,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_FC, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="AS3C1_SUD_0DEG_NO_SUD",species1_name="CLV_CONT_AS3C1_0DEG",species2_name="FES_CONT_AS3C1_0DEG")
    
    FE_CL_AS3C1_NO_tot=concat_table_mult(FE_CL_AS3C1_NO,dataframe_mult)
    
    recup_meteo.log("SIMULATION FESCUE CLOVER AS3C3")
    
    FE_CL_AS3C3_pv,data_XP_AS3C3=all_simulation(ESPECES=ESPECES_FE_AS05C3,AVEC_P=AVEC_PV_TRUE,L_PANNEAU=L_PANNEAU_FES_CLV,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_FC, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="AS3C3_SUD_0DEG_P_SUD",species1_name="CLV_PV_AS3C3_0DEG",species2_name="FES_PV_AS3C3_0DEG")
    
    FE_CL_AS3C3_pv_tot=concat_table_mult(FE_CL_AS3C3_pv,dataframe_mult)
    
    FE_CL_AS3C3_NO,data_XP_AS3C3_NO=all_simulation(ESPECES=ESPECES_FE_AS05C3,AVEC_P=AVEC_PV_FALSE,L_PANNEAU=L_PANNEAU_FES_CLV,BETA_PV=BETA_PV,H_BAS_PV=H_BAS_PV,BAND_WIDTH=Band_FC, N_Y=N_Y,theta_sun_deg=30,
                   phi_sun_deg=180,fd=0,rho_soil=RHO_SOL,n_az_sky=N_AZ_SKY,n_el_sky=N_EL_SKY,n_beams_per_layer=N_BEAMS,
                   n_radiosity_iter=N_RAD_ITER,I0=1,latitude=LATITUDE,doy=DOY,debut=DEBUT,fin=FIN,name="AS3C3_SUD_0DEG_NO_SUD",species1_name="CLV_CONT_AS3C3_0DEG",species2_name="FES_CONT_AS3C3_0DEG")
    
    FE_CL_AS3C3_NO_tot=concat_table_mult(FE_CL_AS3C3_NO,dataframe_mult)
    
    recup_meteo.log("COMPUTATION DATA OUTPUTS")
    
    list_dataframe=[HD1_tot,HD1_no_tot,HD2_tot,HD2_no_tot,LD1_tot,LD1_no_tot,LD2_pv_tot,LD2_no_tot,W_P_NO_300_tot,
                    W_PEA_300_tot,W_PEA_1100_tot,W_P_NO_1100_tot,FE_CL_AS3C1_pv_tot,FE_CL_AS3C1_NO_tot,
                    FE_CL_AS3C3_pv_tot,FE_CL_AS3C3_NO_tot]
    
    DATAFINAL=concat_all_table(list_dataframe)
    DATAFINAL["Model simulation"]="TM"
    
    recup_meteo.log("SAVING DATA OUTPUTS")
    
    WD=os.getcwd()
    path_saving=os.path.join(WD,"OUTPUTS_ABSTRACT")
    path_2=os.path.join (path_saving,"TURBID_MEDIUM_LIGHT/ABSTRACT/SIRASCA/")
    
    DATAFINAL.to_csv(path_2 +"TM_SUD_0DEG_CONFIG2.csv")
    
    recup_meteo.log("SIMULATION FINISHED ")
   

    

    
    
    

    
    


