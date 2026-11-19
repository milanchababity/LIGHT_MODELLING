"""
sirasca_2d_fusion.py
====================
Script SIRASCA 2D fusionné — partage de rayonnement entre N espèces végétales
avec option panneaux photovoltaïques (agrivoltaïque).

Basé sur Sinoquet & Bonhomme (1992) Agric. Forest Meteorol. 62:219-240.

Configuration en tête de fichier (section "PARAMÈTRES UTILISATEUR") :
    - AVEC_PV      : True → simulation agrivoltaïque, False → végétation seule
    - ESPECES      : liste de N espèces végétales paramétrables
    - Panneaux PV  : inclinaison, azimut, position, hauteur, etc.
    - Conditions   : grille batch de directions solaires × fractions diffuses
    - Comparaison  : SOC (fd=1) vs ensoleillé (fd=0.15) automatique si COMPARE=True

Dépendances :
    sirasca_2d.py  (même répertoire ou PYTHONPATH)
"""

import numpy as np
import sys, os
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun,GenSky
import math
import pandas as pd 

a= 12

if not hasattr(np, 'trapz'):
    np.trapz = np.trapezoid

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
if MODEL_DIR not in sys.path:
    sys.path.insert(0, MODEL_DIR)

from TurbidMedium.sirasca_2d import (
    SpeciesParams, PVPanelParams, RadiativeConfig,
    build_agrivoltaic, build_stratified_mixed,
    run_2d_radiative_balance, run_batch, K_ext,
)

SEP  = "=" * 72
SEP2 = "-" * 72


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    PARAMÈTRES UTILISATEUR                          ║
# ╚══════════════════════════════════════════════════════════════════════╝

# ── Option principale ──────────────────────────────────────────────────
AVEC_PV = True     # True  → simulation agrivoltaïque (végétation + PV)
                    # False → simulation végétation seule (sans PV)

COMPARE = False      # True  → compare automatiquement SOC (fd=1) vs soleil (fd=0.15)
                    # False → uniquement les conditions du batch

# ── Géométrie ──────────────────────────────────────────────────────────
BAND_WIDTH = 2.12    # largeur de la bande répétitive (m)
N_Y        = 25     # tranches horizontales
# N_Z est calculé automatiquement depuis la végétation (dz ≤ 10 cm)

# ── Espèces végétales ──────────────────────────────────────────────────
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
    },
    # {
    #     "name"    : "LLD2",
    #     "H"       : 0.63,       # hauteur (m) — dominante
    #     "LAI"     : 1.7,
    #     "alpha"   : 42.4,       # feuilles quasi-verticales
    #     "rho"     : 0.0,
    #     "tau"     : 0.0,
    #     "y0"      : 0.0,      # toute la largeur
    #     "y1"      : 1.0,
    #     "z_haut"  : 0.63,
    #     "z_bas"   : 0.01,      # jusqu'au sol
    #     "shape_z" : "uniform",
    #     "peak_z"  : 0.5,
    #     "shape_y" : "uniform",
    #     "gap_frac": 0.0,
    # },
    # {
    #     "name"    : "FLD2",
    #     "H"       : 0.49,       # hauteur (m) — dominée
    #     "LAI"     : 0.43,
    #     "alpha"   : 53.4,       # feuilles quasi-horizontales
    #     "rho"     : 0.0,
    #     "tau"     : 0.0,
    #     "y0"      : 0.0,
    #     "y1"      : 1.0,
    #     "z_haut"  : 0.49,
    #     "z_bas"   : 0.0,
    #     "shape_z" : "uniform",
    #     "peak_z"  : 0.5,
    #     "shape_y" : "uniform",
    #     "gap_frac": 0.0,
    # },
    # ── Décommenter pour ajouter une 3e espèce ─────────────────────────
    # {
    #     "name"    : "Espèce 3 (sphérique)",
    #     "H"       : 1.0,
    #     "LAI"     : 1.5,
    #     "alpha"   : 57.,
    #     "rho"     : 0.10,
    #     "tau"     : 0.05,
    #     "y0"      : 0.5,      # demi-bande droite
    #     "y1"      : 1.0,
    #     "z_haut"  : 1.0,
    #     "z_bas"   : None,
    #     "shape_z" : "gaussian",
    #     "peak_z"  : 0.4,
    #     "shape_y" : "uniform",
    #     "gap_frac": 0.0,
    # },
]

# ── Panneaux PV (utilisés uniquement si AVEC_PV = True) ────────────────
L_PANNEAU      = 0.85    # longueur dans le plan du panneau (m), direction z-y
L_PANNEAU_LARG = 0.93    # largeur parallèle aux rangs x (m)
BETA_PV        = 0.    # inclinaison depuis l'horizontale (°)
GAMMA_PV       = 180.   # azimut de la normale (° ; 180 = plein Sud)
H_BAS_PV       = 2.0    # hauteur du bas du panneau depuis le sol (m)
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

# Grille batch : produit cartésien SUN_DIRS × FD_VALUES
# Directions solaires : (theta_deg, phi_deg)
# 
latitude = 46.43
DOY = 172

SUN_DIRS = []
LST_HOURS = []
VAR=np.arange(4,22,1)
for hour in VAR:
#[10,12]:#np.arange(0, 24, 1./4.):
    s = Sun.Sun()
    s._set_pos_astro(DOY, hour, 3.14 / 180 * latitude)
    if math.degrees(s.elev) < 88.:
        SUN_DIRS.append((math.degrees(s.elev),180.-math.degrees(s.azim)))
        LST_HOURS.append(hour)

# Fractions diffuses
FD_VALUES = [0.0]*len(SUN_DIRS)


# ╚══════════════════════════════════════════════════════════════════════╝


# ═══════════════════════════════════════════════════════════════════════
# 1.  RÉSOLUTION DE LA GRILLE VERTICALE
# ═══════════════════════════════════════════════════════════════════════

H_VEG_MAX = max(e.get("z_haut", e["H"]) for e in ESPECES)
N_VEG_MIN  = max(int(np.ceil(H_VEG_MAX / 0.10)), 5)
dz         = H_VEG_MAX / N_VEG_MIN

if AVEC_PV:
    H_PROJ_PV  = L_PANNEAU * np.sin(np.deg2rad(BETA_PV))
    H_HAUT_PV  = H_BAS_PV + H_PROJ_PV        # hauteur du haut du panneau (m)
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


# ═══════════════════════════════════════════════════════════════════════
# 2.  CONSTRUCTION DES ESPÈCES ET DE LA GÉOMÉTRIE
# ═══════════════════════════════════════════════════════════════════════

veg_params_list      = []
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

N_VEG = len(ESPECES)

if AVEC_PV:
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
    )
    N_PV = 0

base_cfg = RadiativeConfig(
    I0=1., theta_sun_deg=30., phi_sun_deg=180., fd=0.15,
    rho_soil=RHO_SOL, n_az_sky=N_AZ_SKY, n_el_sky=N_EL_SKY,
    n_beams_per_layer=N_BEAMS, n_radiosity_iter=N_RAD_ITER,
)

syms_veg = "▓▒▤▥◈"


# ═══════════════════════════════════════════════════════════════════════
# 3.  AFFICHAGE DE LA CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

mode_label = "AGRIVOLTAÏQUE (avec PV)" if AVEC_PV else "VÉGÉTATION SEULE (sans PV)"
print(SEP)
print(f"  SIRASCA 2D — {mode_label}")
print(f"  Sinoquet & Bonhomme (1992) Agric. Forest Meteorol. 62:219-240")
print(SEP)

print(f"\n  Géométrie   : H={H_TOTAL:.2f}m  W={BAND_WIDTH}m  "
      f"{N_Z}cch×{N_Y}tr  (dz={dz*100:.1f}cm  dy={dy*100:.1f}cm)")

for i, e in enumerate(ESPECES):
    y0s = f"{e.get('y0', 0.) * BAND_WIDTH:.2f}" if e.get('y0') is not None else "0.00"
    y1s = f"{e.get('y1', 1.) * BAND_WIDTH:.2f}" if e.get('y1') is not None else f"{BAND_WIDTH:.2f}"
    z_haut = e.get("z_haut", e["H"])
    z_bas  = e.get("z_bas") or 0.0
    print(f"  {syms_veg[i%len(syms_veg)]} {e['name']:28s} H={z_haut}m  z_bas={z_bas}m  "
          f"LAI={e['LAI']}  α={e['alpha']}°  ρ={e['rho']}  τ={e['tau']}")
    print(f"    {'':30s} y∈[{y0s},{y1s}]m  "
          f"shape_z={e.get('shape_z','parabolic')}  peak_z={e.get('peak_z',0.5)}")

if AVEC_PV:
    surf_pv = geo.LAD_grids[N_VEG].sum() * dz * dy
    print(f"\n  PV : β={BETA_PV}°  γ={GAMMA_PV}°  L_plan={L_PANNEAU}m  L_rang={L_PANNEAU_LARG}m")
    print(f"       h_proj={H_PROJ_PV:.3f}m  ({N_COUCHES_PV} couches)")
    print(f"       y∈[{Y0_PV*BAND_WIDTH:.2f},{Y1_PV*BAND_WIDTH:.2f}]m  "
          f"z_sol∈[{H_BAS_PV:.2f},{H_BAS_PV+H_PROJ_PV:.2f}]m  "
          f"ρ={RHO_PV}  mode={'masque' if OPAQUE_MASK else 'turbide'}")
    print(f"       Surface calculée : {surf_pv:.4f} m²/m rang  (attendu {L_PANNEAU_LARG:.4f})")
else:
    print(f"\n  PV : désactivé  (mettre AVEC_PV = True pour l'activer)")


# ═══════════════════════════════════════════════════════════════════════
# 4.  PROFILS LAD/PAD
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{SEP}")
print("  PROFILS LAD/PAD (densité foliaire / surfacique)")
print(SEP)

lad_veg = [geo.LAD_grids[s].mean(axis=1) for s in range(N_VEG)]
pad_pv  =  geo.LAD_grids[N_VEG].mean(axis=1) if AVEC_PV else np.zeros(N_Z)
all_lad_vals = lad_veg + ([pad_pv] if AVEC_PV else [])
lad_max = max((v.max() for v in all_lad_vals), default=1e-6)
lad_max = max(lad_max, 1e-6)


LAD_table=pd.DataFrame({"LAD_Vege":lad_veg})

hdr_veg = "  ".join(f"{'LAD_'+e['name'][:10]:>12}" for e in ESPECES)
hdr_pv  = f"  {'PAD_PV':>8}" if AVEC_PV else ""
print(f"\n  {'Cche':>4} | {'z_sol(m)':>8} | {hdr_veg}{hdr_pv} | Profil")
print("  " + SEP2)

nonzero = [i for i in range(N_Z)
           if any(lad_veg[s][i] > 0 for s in range(N_VEG))
           or (AVEC_PV and pad_pv[i] > 0)]
i_min = max(0, nonzero[0] - 1) if nonzero else 0
i_max = min(N_Z - 1, nonzero[-1] + 1) if nonzero else N_Z - 1

for i in range(N_Z):
    if i < i_min or i > i_max:
        continue
    z_sol  = H_TOTAL - (i + 0.5) * dz
    vals_v = [lad_veg[s][i] for s in range(N_VEG)]
    pv_val = pad_pv[i] if AVEC_PV else 0.
    bar    = ""
    for s in range(N_VEG):
        bar += syms_veg[s % len(syms_veg)] * int(vals_v[s] / lad_max * 12)
    if AVEC_PV:
        bar += "░" * int(pv_val / lad_max * 12)
    row_v  = "  ".join(f"{vals_v[s]:12.4f}" for s in range(N_VEG))
    row_pv = f"  {pv_val:8.4f}" if AVEC_PV else ""
    zones  = [e["name"][:8] for s, e in enumerate(ESPECES) if vals_v[s] > 0]
    if AVEC_PV and pv_val > 0:
        zones.append("PV")
    print(f"  {i+1:4d} | {z_sol:8.3f} | {row_v}{row_pv} | {bar}  {'+'.join(zones)}")

leg = "  ".join(f"{syms_veg[s%len(syms_veg)]}={ESPECES[s]['name'][:12]}" for s in range(N_VEG))
if AVEC_PV:
    leg += "  ░=PV"
print(f"  Légende : {leg}")

# Vérification LAI
print(f"\n  Vérification LAI reconstruit :")
for s in range(N_VEG):
    lai_rec = lad_veg[s].sum() * dz

    print(f"    {ESPECES[s]['name'][:25]:25s} : LAI={lai_per_veg_list[s]:.2f}  reconstruit={lai_rec:.4f}")
if AVEC_PV:
    surf_rec = pad_pv.sum() * dz * N_Y * dy
    print(f"    {'PV':25s} : L_rang={L_PANNEAU_LARG:.3f}m  reconstruit={geo.LAD_grids[N_VEG].sum()*dz*dy:.4f}m")


# ═══════════════════════════════════════════════════════════════════════
# 5.  SIMULATION BATCH
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{SEP}")
print(f"  SIMULATION BATCH — {len(SUN_DIRS)} directions × {len(FD_VALUES)} fd = "
      f"{len(SUN_DIRS)*len(FD_VALUES)} conditions")
print(SEP)

batch = run_batch(
    geo, species, base_cfg,
    sun_dirs  = SUN_DIRS,
    fd_values = FD_VALUES,
    lst_hours = LST_HOURS,
    verbose   = True,
)
batch.summary_table()
batch.lad_summary()
batch.to_dict()

print(dir(batch))
print(batch.frac_abs_direct)
direct=pd.DataFrame(batch.frac_abs_direct,columns=[f"{sp}_direct" for sp in batch.species_names])
direct.insert(0, "HOURS",LST_HOURS)
direct.set_index("HOURS",inplace=True)

diffuse_f = pd.DataFrame(batch.frac_abs_diffuse,columns=[f"{sp}_diffuse" for sp in batch.species_names])
diffuse_f.insert(0, "HOURS", LST_HOURS)
diffuse_f.set_index("HOURS", inplace=True)
data_final = pd.concat([direct, diffuse_f],axis=1,join="outer")
data_final["TREATMENTS"]="TM"

print(data_final)




        # conditions        = conditions,
        # frac_abs          = frac_abs,
        # frac_trans        = frac_trans,
        # frac_abs_direct   = frac_abs_dir,
        # frac_abs_diffuse  = frac_abs_dif,
        # frac_abs_scattered= frac_abs_scat,
        # species_names     = [sp.name for sp in species],

# ═══════════════════════════════════════════════════════════════════════
# 6.  COMPARAISON SOC vs ENSOLEILLÉ (si COMPARE=True)
# ═══════════════════════════════════════════════════════════════════════

if COMPARE and 0.15 in FD_VALUES and 1.0 in FD_VALUES:
    print(f"\n{SEP}")
    print("  COMPARAISON — Soleil (fd=0.15) vs SOC (fd=1.0)")
    print(f"  (θ=30°, φ=180°)")
    print(SEP)

    def find_cond(fd_val):
        return next((k for k, c in enumerate(batch.conditions)
                     if abs(c['theta_deg'] - 30.) < 0.1
                     and abs(c['phi_deg']  - 180.) < 0.1
                     and abs(c['fd']       - fd_val) < 1e-6), None)

    k_sun = find_cond(0.15)
    k_soc = find_cond(1.0)

    if k_sun is not None and k_soc is not None:
        header = f"  {'':28s} | {'fd=0.15 (soleil)':>16} | {'fd=1.0 (SOC)':>12} | {'Δ (SOC-sol)':>12}"
        sep_c  = "  " + "-" * (len(header) - 2)
        print(header)
        print(sep_c)

        rows = [("Transmission sol", batch.frac_trans[k_sun], batch.frac_trans[k_soc])]
        tot_sun = batch.frac_abs[k_sun, :N_VEG].sum()
        tot_soc = batch.frac_abs[k_soc, :N_VEG].sum()
        rows.append(("Absorption totale (vég.)", tot_sun, tot_soc))
        for s in range(N_VEG):
            rows.append((f"f_abs {ESPECES[s]['name'][:20]}", batch.frac_abs[k_sun, s], batch.frac_abs[k_soc, s]))
        if AVEC_PV:
            rows.append(("f_abs PV", batch.frac_abs[k_sun, N_VEG], batch.frac_abs[k_soc, N_VEG]))

        for label, v_sun, v_soc in rows:
            delta = v_soc - v_sun
            print(f"  {label:28s} | {v_sun:>16.3f} | {v_soc:>12.3f} | {delta:>+12.3f}")

        print(sep_c)
        print(f"\n  Parts de rayonnement absorbé par espèce (% de l'absorption végétale) :")
        for s in range(N_VEG):
            p_sun = batch.frac_abs[k_sun, s] / max(tot_sun, 1e-9) * 100
            p_soc = batch.frac_abs[k_soc, s] / max(tot_soc, 1e-9) * 100
            print(f"    {ESPECES[s]['name'][:25]:25s} : soleil={p_sun:5.1f}%  SOC={p_soc:5.1f}%  Δ={p_soc-p_sun:+5.1f}%")


# ═══════════════════════════════════════════════════════════════════════
# 7.  VÉRIFICATION ANALYTIQUE K_eff SOC (Beer-Lambert 1er ordre)
# ═══════════════════════════════════════════════════════════════════════

if COMPARE:
    print(f"\n{SEP}")
    print("  VÉRIFICATION ANALYTIQUE — K_eff SOC (Beer-Lambert 1er ordre)")
    print(SEP)
    print("  K_eff = ∫ K(θ)·L_SOC(θ)·cos(θ)·sin(θ)dθ  (intégration numérique)")

    thetas  = np.linspace(np.deg2rad(1), np.deg2rad(89), 500)
    L_SOC   = (1. + 2. * np.cos(thetas)) / 3.
    weights = L_SOC * np.cos(thetas) * np.sin(thetas)
    weights /= np.trapz(weights, thetas)

    K_effs  = [np.trapz([K_ext(t, sp.alpha) for t in thetas] * weights, thetas)
               for sp in veg_params_list]
    K_dirs  = [K_ext(np.deg2rad(30.), sp.alpha) for sp in veg_params_list]

    print(f"\n  {'Espèce':28s} | {'K(θ=30°) direct':>16} | {'K_eff SOC':>10}")
    print("  " + "-" * 58)
    for s, sp in enumerate(veg_params_list):
        print(f"  {sp.name[:28]:28s} | {K_dirs[s]:>16.4f} | {K_effs[s]:>10.4f}")

    K_tot_soc = sum(K_effs[s] * lai_per_veg_list[s] for s in range(N_VEG))
    T_soc_th  = np.exp(-K_tot_soc)
    print(f"\n  T_SOC théorique (Beer-Lambert)    : {T_soc_th:.4f}")
    for s in range(N_VEG):
        frac_int = K_effs[s] * lai_per_veg_list[s] / max(K_tot_soc, 1e-9)
        abs_th   = (1. - T_soc_th) * frac_int * veg_params_list[s].absorptance
        print(f"  f_abs théorique {ESPECES[s]['name'][:18]:18s} : {abs_th:.4f}  (frac_int={frac_int:.3f})")

    # Trouver la simulation SOC pour comparaison
    k_soc2 = next((k for k, c in enumerate(batch.conditions)
                   if abs(c['fd'] - 1.0) < 1e-6), None)
    if k_soc2 is not None:
        print(f"\n  Comparaison simulation vs théorie (fd=1.0) :")
        for s in range(N_VEG):
            frac_int = K_effs[s] * lai_per_veg_list[s] / max(K_tot_soc, 1e-9)
            abs_th   = (1. - T_soc_th) * frac_int * veg_params_list[s].absorptance
            delta    = batch.frac_abs[k_soc2, s] - abs_th
            print(f"    {ESPECES[s]['name'][:20]:20s} : sim={batch.frac_abs[k_soc2,s]:.4f}  "
                  f"théorie={abs_th:.4f}  Δ={delta:+.4f}  (radiosités incluses)")


# ═══════════════════════════════════════════════════════════════════════
# 8.  PROFILS D'ABSORPTION (1re condition du batch)
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{SEP}")
print(f"  PROFILS D'ABSORPTION DÉTAILLÉS")
print(f"  (condition 1 du batch : θ={batch.conditions[0]['theta_deg']}°  "
      f"fd={batch.conditions[0]['fd']})")
print(SEP)

cfg_ref = RadiativeConfig(
    I0=1.,
    theta_sun_deg = batch.conditions[0]['theta_deg'],
    phi_sun_deg   = batch.conditions[0]['phi_deg'],
    fd            = batch.conditions[0]['fd'],
    rho_soil      = RHO_SOL,
    n_az_sky      = N_AZ_SKY, n_el_sky=N_EL_SKY,
    n_beams_per_layer=N_BEAMS, n_radiosity_iter=N_RAD_ITER,
)
res_ref = run_2d_radiative_balance(geo, species, cfg_ref, verbose=False)

# ── Profil vertical ───────────────────────────────────────────────────
print(f"\n  ── Profil vertical d'absorption (haut → bas) ────────────────────")
vp_veg = [res_ref.vertical_profile(s) for s in range(N_VEG)]
vp_pv  =  res_ref.vertical_profile(N_VEG) if AVEC_PV else np.zeros(N_Z)
vp_max = max(max(v.max() for v in vp_veg), vp_pv.max() if AVEC_PV else 0., 1e-9)

hdr_abs = "  ".join(f"{'Abs_'+e['name'][:10]:>12}" for e in ESPECES)
hdr_pv_r = f"  {'Abs_PV':>8}" if AVEC_PV else ""
print(f"  {'Cche':>4} | {'z_sol(m)':>8} | {hdr_abs}{hdr_pv_r} | Profil")
print("  " + SEP2)

for i in range(N_Z):
    vals_v = [vp_veg[s][i] for s in range(N_VEG)]
    ap     = vp_pv[i] if AVEC_PV else 0.
    if all(v < 1e-7 for v in vals_v) and ap < 1e-7:
        continue
    z_sol = H_TOTAL - (i + 0.5) * dz
    bar   = ""
    for s in range(N_VEG):
        bar += syms_veg[s % len(syms_veg)] * int(vals_v[s] / vp_max * 14)
    if AVEC_PV:
        bar += "░" * int(ap / vp_max * 14)
    row_v  = "  ".join(f"{vals_v[s]:12.5f}" for s in range(N_VEG))
    row_pv = f"  {ap:8.5f}" if AVEC_PV else ""
    print(f"  {i+1:4d} | {z_sol:8.3f} | {row_v}{row_pv} | {bar}")

print(f"  Légende : {leg}")

# ── Profil horizontal ─────────────────────────────────────────────────
print(f"\n  ── Profil horizontal d'absorption (tranche y) ───────────────────")
hp_veg = [res_ref.horizontal_profile(s) for s in range(N_VEG)]
hp_pv  =  res_ref.horizontal_profile(N_VEG) if AVEC_PV else np.zeros(N_Y)
hp_max = max(max(v.max() for v in hp_veg), hp_pv.max() if AVEC_PV else 0., 1e-9)

hdr_abs_h = "  ".join(f"{'Abs_'+e['name'][:10]:>12}" for e in ESPECES)
print(f"  {'j':>4} | {'y (m)':>6} | {hdr_abs_h}{hdr_pv_r} | Profil")
print("  " + SEP2)
for j in range(N_Y):
    y      = (j + 0.5) * dy
    vals_v = [hp_veg[s][j] for s in range(N_VEG)]
    ap     = hp_pv[j] if AVEC_PV else 0.
    bar    = ""
    for s in range(N_VEG):
        bar += syms_veg[s % len(syms_veg)] * int(vals_v[s] / hp_max * 14)
    if AVEC_PV:
        bar += "░" * int(ap / hp_max * 14)
    row_v  = "  ".join(f"{vals_v[s]:12.5f}" for s in range(N_VEG))
    row_pv = f"  {ap:8.5f}" if AVEC_PV else ""
    print(f"  {j+1:4d} | {y:6.3f} | {row_v}{row_pv} | {bar}")
print(f"  Légende : {leg}")


# ═══════════════════════════════════════════════════════════════════════
# 9.  BILAN FINAL ET EXPORT
# ═══════════════════════════════════════════════════════════════════════

print(f"\n{SEP}")
print(f"  BILAN FINAL — {mode_label}")
print(SEP)

print(f"\n  Moyennes sur les {batch.N_sim} conditions simulées :")
for s, nm in enumerate(batch.species_names):
    if not AVEC_PV and nm == 'PV_nul':
        continue
    fa_mean = batch.frac_abs[:, s].mean()
    fa_min  = batch.frac_abs[:, s].min()
    fa_max  = batch.frac_abs[:, s].max()
    print(f"  {nm[:30]:30s} : f_abs_moy={fa_mean:.4f}  [{fa_min:.4f}, {fa_max:.4f}]")

ft_mean = batch.frac_trans.mean()
print(f"  {'Transmission sol':30s} : f_trans_moy={ft_mean:.4f}  "
      f"[{batch.frac_trans.min():.4f}, {batch.frac_trans.max():.4f}]")

utile = (batch.frac_abs[:, :N_VEG].sum(axis=1) + batch.frac_trans).mean()
print(f"\n  Rayonnement utile végétation + sol  : {utile:.4f}  (abs_veg + trans)")

if AVEC_PV:
    pv_moy = batch.frac_abs[:, N_VEG:].sum(axis=1).mean()
    print(f"  Interception PV moyenne             : {pv_moy:.4f}")

# Export numpy
d = batch.to_dict()
print(f"\n  Clés numpy disponibles (batch.to_dict()) :")
for key, val in d.items():
    print(f"  {key:45s} : shape={val.shape}  "
          f"min={val.min():.4f}  max={val.max():.4f}")
