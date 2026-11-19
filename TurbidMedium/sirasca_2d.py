"""
sirasca_2d.py  —  Sinoquet & Bonhomme (1992)  Agric. Forest Meteorol. 62:219-240
Modèle 2D complet de transfert radiatif en interculture par rangs.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import warnings; warnings.filterwarnings("ignore")
from openalea.caribu.sky_tools import GetLight,GetLightsSun,Sun,Gensun,GenSky

# Compatibilité NumPy < 2.0 (trapz) et >= 2.0 (trapezoid)
if not hasattr(np, 'trapz'):
    np.trapz = np.trapezoid


# ────────────────────────────────────────────────────────────────────────────
# 1.  OPTIQUE FOLIAIRE
# ────────────────────────────────────────────────────────────────────────────

def G_function(theta: float, alpha: float,
               sigma_deg: float = 30.0) -> float:
    """G(θ,α) = ∫f(ψ)·A(θ,ψ)dψ  (Ross 1981; Eq. implicite §2.1).

    Parameters
    ----------
    theta     : angle zénithal du faisceau (rad).
    alpha     : angle moyen d inclinaison foliaire (rad).
    sigma_deg : écart-type de la distribution angulaire foliaire (°).
                30° → distribution gaussienne large (défaut article).
                0°  → toutes les feuilles exactement à l angle alpha
                      (distribution de Dirac : G = A(theta, alpha)).
    """
    N = 72
    psi = np.linspace(1e-6, np.pi/2 - 1e-6, N)

    # Distribution angulaire foliaire
    if sigma_deg <= 0.0:
        # Dirac en alpha : toutes les feuilles ont exactement l angle alpha
        # On évalue A(theta, alpha) directement (pas d intégrale)
        sin_t = max(np.sin(theta), 1e-9)
        cos_t = np.cos(theta)
        cot_t = cos_t / sin_t
        cos_a = np.cos(alpha)
        sin_a = max(np.sin(alpha), 1e-9)
        cot_a = cos_a / sin_a
        x = cot_t * cot_a
        if abs(x) >= 1.0:
            G_val = cos_t * cos_a
        else:
            phi_prime = np.arccos(np.clip(x, -1., 1.))
            G_val = cos_t * cos_a * (1. + (2./np.pi)*(np.tan(phi_prime) - phi_prime))
        return float(np.clip(G_val, 1e-6, 1.))

    sigma_d = np.deg2rad(sigma_deg)
    w = np.exp(-0.5*((psi - alpha)/sigma_d)**2)
    denom = np.trapz(w, psi)
    w = w / denom if denom > 1e-12 else np.ones(N)/(N*(psi[1]-psi[0]))

    sin_t = max(np.sin(theta), 1e-9)
    cos_t = np.cos(theta)
    cot_t = cos_t / sin_t
    cos_p = np.cos(psi);  sin_p = np.sin(psi)
    cot_p = cos_p / np.maximum(sin_p, 1e-9)
    x = cot_t * cot_p

    phi_prime = np.arccos(np.clip(x, -1., 1.))
    A_ov = cos_t * cos_p * (1. + (2./np.pi)*(np.tan(phi_prime) - phi_prime))
    A    = np.where(np.abs(x) >= 1., cos_t*cos_p, A_ov)
    return float(np.clip(np.trapz(A*w, psi), 1e-6, 1.))


_GCACHE: Dict[Tuple,float] = {}
def G_cached(theta, alpha, sigma_deg=30.0):
    k = (round(theta,3), round(alpha,3), round(sigma_deg,1))
    if k not in _GCACHE: _GCACHE[k] = G_function(theta, alpha, sigma_deg)
    return _GCACHE[k]

def K_ext(theta: float, alpha: float, sigma_deg: float = 30.0) -> float:
    """K(θ,α) = G(θ,α,σ)/cos(θ)  — Eq. (1).

    Parameters
    ----------
    sigma_deg : dispersion angulaire foliaire (°). 0 = angle fixe (Dirac).
    """
    cos_t = max(np.cos(theta), 1e-4)
    return G_cached(theta, alpha, sigma_deg) / cos_t




# ────────────────────────────────────────────────────────────────────────────
# 1b.  OPTIQUE PANNEAU PHOTOVOLTAÏQUE (surface plane orientée)
# ────────────────────────────────────────────────────────────────────────────

def G_pv(theta_ray: float, phi_ray: float,
         beta_pv: float, gamma_pv: float) -> float:
    """
    Coefficient de projection d un panneau PV plan sur le plan perpendiculaire
    à la direction du faisceau incident (θ_ray, φ_ray).

    Un panneau PV est une surface plane de normale n_pv :
        n_pv = (sin β cos γ, sin β sin γ, cos β)
    avec β = inclinaison depuis l horizontale (rad), γ = azimut (rad).

    La projection sur le plan ⊥ au faisceau est :
        G_pv = |n_pv · d_ray| = |cos(angle entre normale et faisceau)|
             = |sin β sin θ cos(φ_ray - γ) + cos β cos θ|

    Si G_pv < 0 : le faisceau arrive par l arrière du panneau.
    On retourne max(0, G_pv) : le panneau n intercepte que les rayons
    arrivant du côté actif (face avant, par convention face Sud inclinée).

    Réf. : Liu & Jordan (1960), transposition sur surface inclinée.

    Parameters
    ----------
    theta_ray : angle zénithal du faisceau incident (rad). 0 = zénith.
    phi_ray   : azimut du faisceau incident (rad). 0=N, π=S.
    beta_pv   : inclinaison du panneau depuis l horizontale (rad).
                0 = horizontal, π/2 = vertical.
    gamma_pv  : azimut de la normale du panneau (rad).
                0=N, π/2=E, π=S, 3π/2=O.
                Convention : panneau orienté Sud → gamma_pv = π.

    Returns
    -------
    float   G_pv ∈ [0, 1].
    """
    # Cosinus de l angle d incidence sur la face active du panneau
    cos_inc = (np.sin(beta_pv) * np.sin(theta_ray) * np.cos(phi_ray - gamma_pv)
               + np.cos(beta_pv) * np.cos(theta_ray))
    return float(np.clip(cos_inc, 0., 1.))


def K_pv(theta_ray: float, phi_ray: float,
          beta_pv: float, gamma_pv: float) -> float:
    """
    Coefficient d extinction K d un panneau PV pour une direction de faisceau
    (θ_ray, φ_ray).

    K_pv = G_pv(θ, φ) / cos(θ)

    Le panneau est assimilé à un milieu turbide de densité surfacique PAD
    [m² panneau / m² sol horizontale], jouant le même rôle que le LAD pour
    les feuilles. L extinction optique dans une cellule de hauteur dz est :
        τ_optique = K_pv · PAD · dz

    Parameters
    ----------
    theta_ray, phi_ray : direction du faisceau (rad).
    beta_pv, gamma_pv  : orientation du panneau (rad).

    Returns
    -------
    float   K_pv ≥ 0.
    """
    cos_t = max(np.cos(theta_ray), 1e-4)
    return G_pv(theta_ray, phi_ray, beta_pv, gamma_pv) / cos_t


# ────────────────────────────────────────────────────────────────────────────
# 1c.  PARAMÈTRES D UN PANNEAU PHOTOVOLTAÏQUE
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class PVPanelParams:
    """
    Paramètres d un rang de panneaux photovoltaïques intégrés dans le couvert.

    Les panneaux PV sont traités comme une "espèce" supplémentaire dans la
    grille LAD, avec leur propre coefficient d extinction dépendant de
    l azimut du faisceau (contrairement aux feuilles qui ont une distribution
    azimutale aléatoire).

    La densité de panneau PAD (Panel Area Density, m² panneau / m³ cellule)
    joue le rôle du LAD : c est elle qui est stockée dans la grille LAD
    correspondant aux panneaux.

    Attributes
    ----------
    name       : Identifiant du rang de panneaux.
    beta_deg   : Inclinaison des panneaux depuis l horizontale (°).
                 0° = horizontal, 90° = vertical.
    gamma_deg  : Azimut de la normale du panneau (°).
                 0=N, 90=E, 180=S (face Sud), 270=O.
                 Convention standard : 180° pour exposition plein Sud.
    rho_pv     : Réflectance du panneau (face active, PAR).
                 Typiquement 0.05–0.10 pour un panneau standard.
    tau_pv     : Transmittance du panneau (0.0 = opaque, standard).
    is_pv      : Marqueur interne pour distinguer panneaux et végétation.

    Exemples
    --------
    # Panneau à 30° incliné, orienté plein Sud, opaque
    pv = PVPanelParams("PV_Sud_30", beta_deg=30., gamma_deg=180., rho_pv=0.05)

    # Panneau vertical orienté Est-Ouest (γ=90°)
    pv = PVPanelParams("PV_Vertical_EO", beta_deg=90., gamma_deg=90., rho_pv=0.08)
    """
    name:             str
    beta_deg:         float = 30.0    # inclinaison panneau (°)
    gamma_deg:        float = 180.0   # azimut normale panneau (°) : 180 = plein Sud
    row_azimuth_deg:  float = 0.0     # azimut des rangs PV (°) par rapport à l axe x
                                      # 0° = rangs PV parallèles aux rangs végétaux (axe x)
                                      # 90° = rangs PV perpendiculaires à l axe x
    rho_pv:           float = 0.05    # réflectance face active
    tau_pv:           float = 0.0     # transmittance (0 = opaque)
    pas_x:            float = 0.0     # pas entre panneaux dans la direction x (m)
                                      # 0.0 = panneaux continus (infini en x) — défaut
                                      # > 0 = espacement entre centres de panneaux
                                      # gap_x = pas_x - l_panneau (calculé dans K_for_direction)
                                      # Physique : un faisceau incliné peut passer
                                      # dans le gap entre deux panneaux successifs.
                                      # Formule (Nilson 1971) :
                                      #   Δx = h_proj × tan(θ) × |cos(φ - φ_rangs)|
                                      #   Si Δx ≤ gap_x : cov_eff = l_pan / pas_x
                                      #   Si Δx >  gap_x : cov_eff = l_pan / (l_pan + Δx)
    l_pan_x:          float = 0.0     # largeur du panneau dans la direction x (m)
                                      # Nécessaire seulement si pas_x > 0.
                                      # Calculé automatiquement depuis l_panneau_pv
                                      # dans build_agrivoltaic si non fourni.
    h_proj_x:         float = 0.0     # hauteur projetée verticalement du panneau (m)
                                      # = L_panneau × sin(β). Calculé automatiquement
                                      # dans build_agrivoltaic.
    opaque_mask:      bool  = False   # masque géométrique pur (T=0 dans la cellule)
                                      # True  → comportement masque opaque :
                                      #         tout le flux incident est intercepté
                                      #         (f_abs = frac_W × absorptance)
                                      # False → modèle turbide Beer-Lambert (défaut)
                                      #         T = exp(-K·PAD·dz) ≥ 0
    is_pv:            bool  = True    # marqueur panneau PV

    @property
    def beta(self)        -> float: return np.deg2rad(self.beta_deg)
    @property
    def gamma(self)       -> float: return np.deg2rad(self.gamma_deg)
    @property
    def row_azimuth(self) -> float: return np.deg2rad(self.row_azimuth_deg)
    @property
    def sigma(self)       -> float: return self.rho_pv + self.tau_pv
    @property
    def absorptance(self) -> float: return max(1. - self.sigma, 1e-6)

    # Compatibilité avec l interface SpeciesParams
    @property
    def alpha(self)     -> float: return self.beta    # réutilisé pour stockage
    @property
    def sigma_deg(self) -> float: return 0.0          # non utilisé pour PV

    def coverage_x(self, theta_ray: float, phi_ray: float) -> float:
        """Fraction de la largeur x interceptée par les panneaux pour (θ, φ).

        Sans discontinuité (pas_x=0) : coverage = 1.0 (panneaux continus).
        Avec discontinuité (pas_x > 0) :
          Δx = h_proj_x × tan(θ) × |cos(φ - row_azimuth)|
          Si Δx ≤ gap_x : coverage = l_pan_x / pas_x    (géométrique)
          Si Δx >  gap_x : coverage = l_pan_x / (l_pan_x + Δx)  (Nilson 1971)

        Réf. : Nilson T. (1971). A theoretical analysis of the frequency
               of gaps in plant stands. Agric. Meteorol. 8, 25–38.
        """
        if self.pas_x <= 0. or self.l_pan_x <= 0.:
            return 1.0                          # panneaux continus — défaut

        gap_x    = max(self.pas_x - self.l_pan_x, 0.)
        cov_geom = self.l_pan_x / self.pas_x   # coverage géométrique

        if self.h_proj_x <= 0.:
            # Panneau horizontal (β=0°) : aucun décalage x entre couches.
            # Le faisceau traverse toujours la même rangée de panneaux.
            # La coverage est purement géométrique : l_pan_x / pas_x.
            return self.l_pan_x / self.pas_x if self.pas_x > 0. else 1.0

        # Composante du faisceau dans la direction x (parallèle aux rangs PV)
        phi_rel = phi_ray - self.row_azimuth
        cx      = abs(np.cos(phi_rel))
        delta_x = self.h_proj_x * np.tan(max(theta_ray, 0.)) * cx

        if delta_x <= gap_x:
            return cov_geom                     # faisceau reste dans la même cellule x
        else:
            return self.l_pan_x / (self.l_pan_x + delta_x)  # Nilson 1971

    def K_for_direction(self, theta_ray: float, phi_ray: float) -> float:
        """K effectif du panneau pour la direction de faisceau (θ, φ).

        Intègre deux corrections par rapport à K_pv de base :
        1. Azimut des rangs PV : phi_eff = phi + row_azimuth_veg - row_azimuth_pv
           (appliqué dans beam_path_2d avant d appeler cette méthode)
        2. Discontinuité en x : K_eff = K_pv × coverage_x(θ, φ)
           La coverage_x < 1 quand le faisceau peut passer entre deux panneaux
           successifs (pas_x > 0, formule de Nilson 1971).
        """
        K_base   = K_pv(theta_ray, phi_ray, self.beta, self.gamma)
        cov      = self.coverage_x(theta_ray, phi_ray)
        return K_base * cov




# ────────────────────────────────────────────────────────────────────────────
# 1d.  CONSTRUCTEUR PV EN CHAPEAU (double versant)
# ────────────────────────────────────────────────────────────────────────────

def make_pv_chapeau(
    name:             str,
    beta_deg:         float = 30.0,
    row_azimuth_deg:  float = 0.0,
    gamma_faite_deg:  float = 180.0,
    rho_pv:           float = 0.05,
    tau_pv:           float = 0.0,
    opaque_mask:      bool  = False,
) -> Tuple["PVPanelParams", "PVPanelParams"]:
    """
    Crée une paire de panneaux PV en configuration "chapeau" (double pente /
    toit à deux versants).

    Un chapeau est constitué de deux versants inclinés en sens opposés qui se
    rejoignent au faîte. Chaque versant est un PVPanelParams indépendant avec
    le même beta mais des gamma opposés (symétrie par rapport au plan vertical
    contenant le faîte).

    Géométrie
    ---------
    Le faîte est orienté selon l axe des rangs PV (row_azimuth_deg).
    gamma_faite_deg définit l azimut du faîte (direction du faîte, pas de la
    normale). Les deux normales de versant sont à ±90° du faîte dans le plan
    horizontal :
      - Versant 1 : normale à gamma_faite_deg + 90°  (versant "droit")
      - Versant 2 : normale à gamma_faite_deg - 90°  (versant "gauche")

    Exemple : chapeau avec faîte N-S (gamma_faite=0° ou 180°) :
      → Versant Est  : gamma = 90°   (face vers l Est)
      → Versant Ouest: gamma = 270°  (face vers l Ouest)

    Exemple : chapeau avec faîte E-O (gamma_faite=90°) :
      → Versant Sud  : gamma = 180°  (face vers le Sud)
      → Versant Nord : gamma = 0°    (face vers le Nord)

    Parameters
    ----------
    name            : Préfixe du nom (suffixes "_V1" et "_V2" ajoutés).
    beta_deg        : Inclinaison de chaque versant depuis l horizontale (°).
                      0° = chapeau plat (horizontal), 90° = chapeau droit (vertical).
    row_azimuth_deg : Azimut des rangs PV par rapport à l axe x (°).
    gamma_faite_deg : Azimut du FAÎTE (°). Détermine l orientation des versants.
                      Exemple : 180° pour un faîte orienté N-S avec versants E-O.
    rho_pv          : Réflectance de chaque versant.
    tau_pv          : Transmittance de chaque versant (0 = opaque).

    Returns
    -------
    (pv_v1, pv_v2) : Tuple de deux PVPanelParams, un par versant.
                     À utiliser ensemble dans build_agrivoltaic :
                         pv_params    = list(make_pv_chapeau(...))
                         l_panneau_pv = [L_versant, L_versant]
                         y_fracs_pv   = [(y0, y1), (y0, y1)]  # même position
                         z_fracs_pv   = [(z0, z1), (z0, z1)]  # même position

    Exemples
    --------
    # Chapeau E-O (faîte N-S), β=30°, au-dessus d une culture
    pv_v1, pv_v2 = make_pv_chapeau("chapeau", beta_deg=30.,
                                    gamma_faite_deg=0., rho_pv=0.05)
    # → versant Est  (gamma=90°)  et versant Ouest (gamma=270°)

    # Chapeau N-S (faîte E-O), β=25°
    pv_v1, pv_v2 = make_pv_chapeau("chapeau_NS", beta_deg=25.,
                                    gamma_faite_deg=90.)
    # → versant Sud  (gamma=180°) et versant Nord  (gamma=0°)
    """
    gamma_v1 = (gamma_faite_deg + 90.)  % 360.
    gamma_v2 = (gamma_faite_deg - 90.)  % 360.

    pv_v1 = PVPanelParams(
        name            = f"{name}_V1",
        beta_deg        = beta_deg,
        gamma_deg       = gamma_v1,
        row_azimuth_deg = row_azimuth_deg,
        rho_pv          = rho_pv,
        tau_pv          = tau_pv,
        opaque_mask     = opaque_mask,
    )
    pv_v2 = PVPanelParams(
        name            = f"{name}_V2",
        beta_deg        = beta_deg,
        gamma_deg       = gamma_v2,
        row_azimuth_deg = row_azimuth_deg,
        rho_pv          = rho_pv,
        tau_pv          = tau_pv,
        opaque_mask     = opaque_mask,
    )
    return pv_v1, pv_v2


# ────────────────────────────────────────────────────────────────────────────
# 2.  STRUCTURES DE DONNÉES
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class SpeciesParams:
    """Paramètres optiques/architecturaux d'une espèce.

    Attributes
    ----------
    name       : Identifiant de l espèce.
    alpha_deg  : Angle MOYEN d inclinaison foliaire (°).
                 0° = planophile (feuilles horizontales).
                 90° = érectophile (feuilles verticales).
    sigma_deg  : Ecart-type de la distribution angulaire foliaire (°).
                 30° = distribution gaussienne large (défaut, article).
                 0°  = toutes les feuilles exactement à alpha_deg
                       (feuilles à angle fixe, distribution de Dirac).
    rho        : Réflectance foliaire PAR ∈ [0, 1].
    tau_leaf   : Transmittance foliaire PAR ∈ [0, 1].
                 0.0 = feuilles complètement opaques (rho + tau = rho seule).

    Exemples
    --------
    # Feuilles à 45°, complètement opaques
    sp = SpeciesParams("opaque_45", alpha_deg=45., sigma_deg=0., rho=0., tau_leaf=0.)

    # Distribution gaussienne étroite autour de 30°, légèrement translucides
    sp = SpeciesParams("etroite_30", alpha_deg=30., sigma_deg=10., rho=.08, tau_leaf=.03)
    """
    name:      str
    alpha_deg: float = 57.3   # angle moyen inclinaison foliaire (°)
    sigma_deg: float = 30.0   # écart-type distribution angulaire (°) ; 0 = angle fixe
    rho:       float = 0.10   # réflectance foliaire PAR
    tau_leaf:  float = 0.05   # transmittance foliaire PAR

    @property
    def alpha(self): return np.deg2rad(self.alpha_deg)
    @property
    def sigma(self): return self.rho + self.tau_leaf          # coeff. diffusion
    @property
    def absorptance(self): return max(1. - self.sigma, 1e-6)  # absorptance


@dataclass
class RowIntercropGeometry:
    """
    Grille 2D du couvert (couches i × tranches j).
      i = 0..N_z-1  : couches horizontales (haut→bas)
      j = 0..N_y-1  : tranches perpendiculaires aux rangs
    LAD_grids : liste de n_espèces tableaux (N_z, N_y) en [m² feuille / m³].
    """
    W: float                           # largeur bande répétitive (m)
    H: float                           # hauteur couvert (m)
    N_y: int                           # tranches transversales
    N_z: int                           # couches verticales
    row_azimuth_deg: float = 0.0       # azimut des rangs (°)
    LAD_grids: List[np.ndarray] = field(default_factory=list)

    @property
    def dy(self): return self.W / self.N_y
    @property
    def dz(self): return self.H / self.N_z
    @property
    def n_species(self): return len(self.LAD_grids)
    @property
    def row_azimuth(self): return np.deg2rad(self.row_azimuth_deg)

    def validate(self):
        assert self.W>0 and self.H>0
        for s, g in enumerate(self.LAD_grids):
            assert g.shape==(self.N_z, self.N_y), \
                f"Espèce {s}: shape {g.shape} ≠ ({self.N_z},{self.N_y})"


@dataclass
class RadiativeConfig:
    """Paramètres de la simulation radiative."""
    I0:                float = 1.0
    theta_sun_deg:     float = 30.0
    phi_sun_deg:       float = 180.0
    fd:                float = 0.15
    rho_soil:          float = 0.10
    n_az_sky:          int   = 8
    n_el_sky:          int   = 5
    n_beams_per_layer: int   = 20
    n_radiosity_iter:  int   = 6

    @property
    def theta_sun(self):  return np.deg2rad(self.theta_sun_deg)
    @property
    def phi_sun(self):    return np.deg2rad(self.phi_sun_deg)
    @property
    def I0_direct(self):  return self.I0 * (1. - self.fd)
    @property
    def I0_diffuse(self): return self.I0 * self.fd


# ────────────────────────────────────────────────────────────────────────────
# 3.  PROPAGATION D'UN FAISCEAU ÉLÉMENTAIRE DANS LA GRILLE 2D
# ────────────────────────────────────────────────────────────────────────────

def beam_path_2d(
    geo: RowIntercropGeometry,
    species: list,          # List[SpeciesParams | PVPanelParams]
    theta: float,
    phi: float,
    y_entry: float,
    K_s: np.ndarray,
) -> Tuple[np.ndarray, float]:
    """
    Propage un faisceau élémentaire de haut en bas à travers la grille 2D.

    Gère à la fois les espèces végétales (SpeciesParams) et les panneaux
    photovoltaïques (PVPanelParams). La différence clé est que K des PV
    dépend de l azimut φ du faisceau (surface plane orientée), alors que
    K des feuilles ne dépend que de θ (distribution azimutale aléatoire).

    Pour les PV, K_s[s] passé en argument est ignoré et recalculé ici
    selon la direction (θ, φ) du faisceau via K_pv(θ, φ, β, γ).

    Transmittance de la cellule (i,j) :
        T(i,j) = exp(−Σ_s K_s(θ,φ) · LAD_s(i,j) · dz)     Eq. (2)
    Interception partagée :
        I_abs_s = I_flux·(1−T)·f_s·absorptance_s            Eq. (3)
    Déplacement latéral :
        Δy = dz · tan(θ) · |sin(φ − φ_rangs)|               §2.2

    Returns: I_abs_cell (n_sp, N_z, N_y), I_trans (float)
    """
    N_z = geo.N_z; N_y = geo.N_y; dz = geo.dz; dy = geo.dy
    n_sp = geo.n_species

    phi_rel = phi - geo.row_azimuth
    dy_step = dz * np.tan(theta) * abs(np.sin(phi_rel))
    dy_sign = np.sign(np.sin(phi_rel)) if abs(np.sin(phi_rel)) > 1e-9 else 1.

    # Coefficients d extinction effectifs pour ce faisceau (θ, φ)
    # Pour les PV, K dépend de φ ET de l azimut des rangs PV.
    # L azimut apparent du faisceau dans le repère des rangs PV vaut :
    #   phi_eff = phi + (geo.row_azimuth - sp.row_azimuth)
    # car la grille y-z est définie perpendiculairement aux rangs végétaux
    # (azimut geo.row_azimuth), et les rangs PV ont leur propre azimut.
    K_eff = np.array([
        sp.K_for_direction(theta, phi + geo.row_azimuth - sp.row_azimuth)
        if isinstance(sp, PVPanelParams)
        else K_s[s]
        for s, sp in enumerate(species)
    ])

    # Grilles KLAD et transmittance par cellule
    KLAD = np.array([K_eff[s] * geo.LAD_grids[s] for s in range(n_sp)])

    # Masque géométrique : cellules occupées par un PV opaque_mask=True.
    # La transmittance effective tient compte de la coverage_x (discontinuité
    # en x) : T_masque = 1 - coverage_x × (1 - tau_pv)
    # coverage_x = 1 → T=0 (masque total, comportement précédent)
    # coverage_x < 1 → fraction (1-coverage_x) du flux passe dans les gaps x
    mask_opaque = np.zeros((geo.N_z, geo.N_y), dtype=bool)
    T_masque    = np.ones((geo.N_z, geo.N_y))    # transmittance masque par cellule
    for s, sp in enumerate(species):
        if isinstance(sp, PVPanelParams) and sp.opaque_mask:
            occ = geo.LAD_grids[s] > 0
            mask_opaque |= occ
            # coverage_x pour cette direction de faisceau
            cov = sp.coverage_x(theta, phi + geo.row_azimuth - sp.row_azimuth)
            # T_masque = 1 - cov  (transmission géométrique pure entre panneaux)
            # La semi-transparence (tau_pv) est traitée séparément via tau_eff,
            # comme en mode turbide : I_flux_next += I_int * tau_eff
            T_pv = 1. - cov
            T_masque = np.where(occ, np.minimum(T_masque, T_pv), T_masque)

    KLAD_tot = KLAD.sum(axis=0)
    T_cell   = np.where(mask_opaque, T_masque, np.exp(-KLAD_tot * dz))

    # Dans les cellules masque, les espèces végétales ne reçoivent rien
    # (le PV intercepte toute la fraction (1-T_masque)).
    KLAD_for_frac = KLAD_tot.copy()
    for s, sp in enumerate(species):
        if isinstance(sp, PVPanelParams) and sp.opaque_mask:
            occupied = geo.LAD_grids[s] > 0
            KLAD_for_frac = np.where(occupied,
                np.maximum(KLAD[s], 1e-12), KLAD_for_frac)

    safe = np.maximum(KLAD_for_frac, 1e-12)
    frac = np.where(KLAD_for_frac > 1e-12, KLAD / safe, 0.)
    for s, sp in enumerate(species):
        if not (isinstance(sp, PVPanelParams) and sp.opaque_mask):
            frac[s] = np.where(mask_opaque, 0., frac[s])
    frac_pv_tot = sum(
        frac[s] for s, sp in enumerate(species)
        if isinstance(sp, PVPanelParams) and sp.opaque_mask
    )
    for s, sp in enumerate(species):
        if isinstance(sp, PVPanelParams) and sp.opaque_mask:
            frac[s] = np.where(mask_opaque,
                np.where(frac_pv_tot > 1e-12,
                         frac[s] / np.maximum(frac_pv_tot, 1e-12), 1.),
                frac[s])

    absorb = np.array([sp.absorptance for sp in species])

    # Fraction du flux intercepté qui est transmise à travers le matériau PV
    # (semi-transparence). Ce flux doit être réinjecté dans I_flux après
    # chaque couche pour continuer vers le bas.
    # tau_eff[i,j] = Σ_{s PV} frac[s,i,j] × tau_pv[s]
    tau_pv_arr = np.array([
        (sp.tau_pv if isinstance(sp, PVPanelParams) else 0.)
        for sp in species
    ])                                                   # (n_sp,)
    # tau_eff(i,j) = Σ_s frac[s,i,j] × tau_pv_arr[s]
    tau_eff = np.einsum('s,sij->ij', tau_pv_arr, frac)  # (N_z, N_y)

    I_abs = np.zeros((n_sp, N_z, N_y))
    I_flux = 1.
    y_cur  = y_entry % geo.W

    for i in range(N_z):
        j = int(y_cur / dy) % N_y
        T_ij   = T_cell[i, j]
        I_int  = I_flux * (1. - T_ij)          # flux intercepté par la cellule

        # Réinjecter le flux transmis à travers le matériau PV
        # (valable en mode turbide ET masque : tau_eff = Σ frac[s]*tau_pv[s])
        I_trans_pv = I_int * tau_eff[i, j]
        I_flux = I_flux * T_ij + I_trans_pv

        for s in range(n_sp):
            I_abs[s, i, j] += I_int * frac[s, i, j] * absorb[s]
        y_cur = (y_cur + dy_sign * dy_step) % geo.W

    return I_abs, I_flux


# ────────────────────────────────────────────────────────────────────────────
# 4.  INTÉGRATION DU RAYONNEMENT DIRECT (N faisceaux)
# ────────────────────────────────────────────────────────────────────────────

def compute_direct(
    geo: RowIntercropGeometry,
    species: List[SpeciesParams],
    cfg: RadiativeConfig,
) -> Tuple[np.ndarray, float]:
    """
    Intègre N_beams faisceaux élémentaires uniformément distribués sur W.
    Réf. article §2.2.
    """
    theta = cfg.theta_sun; phi = cfg.phi_sun; n_b = cfg.n_beams_per_layer
    K_s = np.array([K_ext(theta, sp.alpha, sp.sigma_deg) for sp in species])
    y_entries = np.linspace(0, geo.W, n_b, endpoint=False) + geo.dy*.5

    I_abs_acc = np.zeros((geo.n_species, geo.N_z, geo.N_y))
    I_tr_acc  = 0.
    for y0 in y_entries:
        ab, tr = beam_path_2d(geo, species, theta, phi, y0, K_s)
        I_abs_acc += ab;  I_tr_acc += tr

    return I_abs_acc/n_b * cfg.I0_direct, I_tr_acc/n_b * cfg.I0_direct


# ────────────────────────────────────────────────────────────────────────────
# 5.  INTÉGRATION DU RAYONNEMENT DIFFUS (voûte céleste SOC)
# ────────────────────────────────────────────────────────────────────────────

def sky_SOC(n_el: int, n_az: int) -> List[Tuple[float,float,float]]:
    """
    Discrétisation de la voûte céleste SOC (Moon & Spencer 1942).
    L(θ) = (1+2·cos θ)/3 ; poids ∝ L·cos θ·sin θ.   Réf. §2.3.
    """
    thetas = np.linspace(np.deg2rad(5), np.deg2rad(85), n_el)
    phis   = np.linspace(0, 2*np.pi, n_az, endpoint=False) + np.pi/n_az
    dirs = []
    for t in thetas:
        L = (1. + 2.*np.cos(t))/3.
        for p in phis:
            dirs.append((float(t), float(p), L*np.cos(t)*np.sin(t)))
    total = sum(d[2] for d in dirs)
    return [(t, p, w/total) for t,p,w in dirs]


def compute_diffuse(
    geo: RowIntercropGeometry,
    species: List[SpeciesParams],
    cfg: RadiativeConfig,
) -> Tuple[np.ndarray, float]:
    """Intègre le rayonnement diffus sur la voûte SOC.  Réf. §2.3."""
    sky = sky_SOC(cfg.n_el_sky, cfg.n_az_sky)
    n_b = max(cfg.n_beams_per_layer//2, 5)
    y_entries = np.linspace(0, geo.W, n_b, endpoint=False) + geo.dy*.5

    I_abs_acc = np.zeros((geo.n_species, geo.N_z, geo.N_y))
    I_tr_acc  = 0.
    for theta_k, phi_k, w_k in sky:
        K_s = np.array([K_ext(theta_k, sp.alpha, sp.sigma_deg) for sp in species])
        I_ab_k = np.zeros((geo.n_species, geo.N_z, geo.N_y));  I_tr_k = 0.
        for y0 in y_entries:
            ab, tr = beam_path_2d(geo, species, theta_k, phi_k, y0, K_s)
            I_ab_k += ab;  I_tr_k += tr
        I_abs_acc += w_k * I_ab_k / n_b
        I_tr_acc  += w_k * I_tr_k / n_b

    return I_abs_acc * cfg.I0_diffuse, I_tr_acc * cfg.I0_diffuse


# ────────────────────────────────────────────────────────────────────────────
# 6.  SOLVEUR DE RADIOSITÉS (diffusion interne multi-ordre)
# ────────────────────────────────────────────────────────────────────────────

def radiosity_solver(
    geo: RowIntercropGeometry,
    species: List[SpeciesParams],
    cfg: RadiativeConfig,
    I_abs_prim: np.ndarray,
    I_trans_prim: float,
) -> np.ndarray:
    """
    Calcule l'absorption due aux ordres de diffusion ≥ 2 par Gauss-Seidel.

    À chaque itération, chaque cellule émet une source secondaire isotrope
    proportionnelle à σ_s, propagée vers le haut et vers le bas.
    Le sol réfléchit ρ_sol × flux_descendant.  Réf. §2.4.

    θ_eff = 57.3° : angle effectif pour la propagation du diffus isotrope
    (Warren Wilson 1963 — G(57.3°) ≈ 0.5 indépendamment de α).
    """
    N_z = geo.N_z;  N_y = geo.N_y;  n_sp = geo.n_species
    THETA_EFF = np.deg2rad(57.3)

    # Transmittances cellules pour propagation diffuse verticale
    K_eff = np.array([K_ext(THETA_EFF, sp.alpha, sp.sigma_deg) for sp in species])
    KLAD  = np.array([K_eff[s]*geo.LAD_grids[s] for s in range(n_sp)])
    KLAD_tot = KLAD.sum(axis=0)
    T_cell   = np.exp(-KLAD_tot * geo.dz)
    safe     = np.maximum(KLAD_tot, 1e-12)
    frac_s   = np.where(KLAD_tot > 1e-12, KLAD/safe, 0.)
    absorb   = np.array([sp.absorptance for sp in species])
    sigma    = np.array([sp.sigma       for sp in species])

    # Sources secondaires initiales (moitié haut, moitié bas)
    Q_dn = np.zeros((N_z, N_y));  Q_up = np.zeros((N_z, N_y))
    for s in range(n_sp):
        q = I_abs_prim[s] / absorb[s] * sigma[s] * .5
        Q_dn += q;  Q_up += q

    I_scat = np.zeros((n_sp, N_z, N_y))

    for it in range(cfg.n_radiosity_iter):
        # ─ Descente ─────────────────────────────────────────────────────────
        flux_base = np.zeros(N_y)
        I_dn_it = np.zeros((n_sp, N_z, N_y))
        for i in range(N_z):
            F = flux_base + Q_dn[i]
            I_int = F * (1. - T_cell[i])
            flux_base = F * T_cell[i]
            for s in range(n_sp):
                I_dn_it[s,i] += I_int * frac_s[s,i] * absorb[s]

        # Réflexion sol
        refl_soil = cfg.rho_soil * (flux_base + I_trans_prim/N_y)

        # ─ Montée ───────────────────────────────────────────────────────────
        flux_top = refl_soil
        I_up_it  = np.zeros((n_sp, N_z, N_y))
        for i in range(N_z-1, -1, -1):
            F = flux_top + Q_up[i]
            I_int = F * (1. - T_cell[i])
            flux_top = F * T_cell[i]
            for s in range(n_sp):
                I_up_it[s,i] += I_int * frac_s[s,i] * absorb[s]

        I_scat += I_dn_it + I_up_it

        # ─ Mise à jour sources (amortissement géom. par σ_moy^(it+1)) ──────
        decay = sigma.mean() ** (it+1)
        Q_dn = np.zeros((N_z, N_y));  Q_up = np.zeros((N_z, N_y))
        for s in range(n_sp):
            q = (I_dn_it[s]+I_up_it[s]) / absorb[s] * sigma[s] * .5 * decay
            Q_dn += q;  Q_up += q

    return I_scat


# ────────────────────────────────────────────────────────────────────────────
# 7.  RÉSULTAT ET BILAN FINAL
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class RadiativeBalance2D:
    I_abs_total:        np.ndarray   # (n_sp, N_z, N_y)  absorption totale
    I_abs_per_species:  np.ndarray   # (n_sp,)  intégrale spatiale
    frac_abs_species:   np.ndarray   # (n_sp,)  fraction de I0
    frac_transmitted:   float
    I_abs_direct:       np.ndarray
    I_abs_diffuse:      np.ndarray
    I_abs_scattered:    np.ndarray
    species_names:      List[str]
    geo:                RowIntercropGeometry
    cfg:                RadiativeConfig

    # ── Profils LAD / PAD ────────────────────────────────────────────────
    def lad_vertical_profile(self, s: int = 0) -> np.ndarray:
        """Profil vertical de LAD/PAD de la composante s  (N_z,).

        Retourne la moyenne du LAD/PAD sur toutes les tranches y de la grille.
        Pour une espèce végétale : [m² feuille / m³]
        Pour un panneau PV       : [m² panneau / m³]
        """
        return self.geo.LAD_grids[s].mean(axis=1)   # (N_z,)

    def lad_horizontal_slice(self, s: int = 0, z_frac: float = 0.5) -> np.ndarray:
        """Profil horizontal de LAD/PAD à une hauteur donnée  (N_y,).

        Parameters
        ----------
        s       : indice de la composante.
        z_frac  : position verticale dans [0, 1]  (0=sommet, 1=sol).
        """
        i = int(np.clip(z_frac * self.geo.N_z, 0, self.geo.N_z - 1))
        return self.geo.LAD_grids[s][i, :]          # (N_y,)

    def lad_grid(self, s: int = 0) -> np.ndarray:
        """Grille complète LAD/PAD de la composante s  (N_z, N_y)."""
        return self.geo.LAD_grids[s]

    def lad_summary(self) -> None:
        """Affiche les profils verticaux de LAD/PAD pour toutes les composantes."""
        dz = self.geo.dz; H = self.geo.H; N_z = self.geo.N_z
        print(f"\n  ── Profils LAD/PAD verticaux  (moyenne sur y) ──────────────")
        header = f"  {'Cche':>4} | {'z_sol':>6} | "
        header += "  ".join(f"{'LAD_'+str(s+1):>9}" for s in range(self.geo.n_species))
        print(header)
        print("  " + "-" * (20 + 11*self.geo.n_species))
        for i in range(N_z):
            z_sol = H - (i + 0.5)*dz
            vals  = [self.geo.LAD_grids[s][i].mean() for s in range(self.geo.n_species)]
            row   = f"  {i+1:4d} | {z_sol:6.3f} | "
            row  += "  ".join(f"{v:9.4f}" for v in vals)
            print(row)
        print(f"  Légende : " + "  ".join(
            f"LAD_{s+1}={self.species_names[s]}" for s in range(self.geo.n_species))
        )

    def print_summary(self, verbose=True):
        total_abs = float(self.frac_abs_species.sum())
        print("\n" + "═"*64)
        print("  BILAN RADIATIF 2D — Sinoquet & Bonhomme (1992)")
        print("═"*64)
        print(f"  θ_sun={self.cfg.theta_sun_deg}°  φ_sun={self.cfg.phi_sun_deg}°  "
              f"fd={self.cfg.fd}  I0={self.cfg.I0}")
        print(f"  Grille {self.geo.N_z}×{self.geo.N_y}  W={self.geo.W}m  H={self.geo.H}m")
        print("─"*64)
        print(f"  Transmission sol  : {self.frac_transmitted:.3f}")
        print(f"  Absorption couvert: {total_abs:.3f}")
        refl = max(0., 1. - self.frac_transmitted - total_abs)
        print(f"  Réflexion estimée : {refl:.3f}")
        print("─"*64)
        for i, nm in enumerate(self.species_names):
            fa = float(self.frac_abs_species[i])
            part = fa/max(total_abs,1e-9)*100
            print(f"  {nm:25s}: f_abs={fa:.3f}  ({part:.1f}% couvert)")
        if verbose:
            print("─"*64)
            I0 = self.cfg.I0
            for i, nm in enumerate(self.species_names):
                fd  = self.I_abs_direct[i].sum()    / I0
                fdif= self.I_abs_diffuse[i].sum()   / I0
                fs  = self.I_abs_scattered[i].sum() / I0
                print(f"  {nm:25s}: dir={fd:.3f}  diff={fdif:.3f}  scat={fs:.3f}")
        print("═"*64)

    def vertical_profile(self, s=0):
        return self.I_abs_total[s].mean(axis=1)   # (N_z,)

    def horizontal_profile(self, s=0):
        return self.I_abs_total[s].mean(axis=0)   # (N_y,)

    def print_profiles(self, max_bar=30):
        for label, fn in [("verticaux (haut→bas)", self.vertical_profile),
                          ("horizontaux (j tranches)", self.horizontal_profile)]:
            print(f"\n  ── Profils {label} ──")
            for s, nm in enumerate(self.species_names):
                v = fn(s); mx = max(v.max(), 1e-9)
                print(f"  {nm}:")
                for k, val in enumerate(v):
                    print(f"    [{k+1:2d}] {val:.5f} | {'█'*int(val/mx*max_bar)}")


def run_2d_radiative_balance(
    geo: RowIntercropGeometry,
    species: List[SpeciesParams],
    cfg: RadiativeConfig,
    verbose: bool = True,
) -> RadiativeBalance2D:
    """
    Bilan radiatif 2D complet (Sinoquet & Bonhomme 1992).
    Étapes : Direct → Diffus SOC → Radiosités → Agrégation.
    """
    geo.validate()
    if verbose:
        print(f"\n  ┌── SIRASCA 2D ─────────────────────────────────────────")
        print(f"  │  θ_sun={cfg.theta_sun_deg}° fd={cfg.fd} "
              f"W={geo.W}m H={geo.H}m {geo.N_z}×{geo.N_y} cells")

    if verbose: print("  │  [1/4] Direct...", end=" ", flush=True)
    I_abs_dir, I_tr_dir = compute_direct(geo, species, cfg)
    if verbose: print(f"trans={I_tr_dir:.3f}")

    if verbose: print("  │  [2/4] Diffus SOC...", end=" ", flush=True)
    I_abs_dif, I_tr_dif = compute_diffuse(geo, species, cfg)
    if verbose: print(f"trans={I_tr_dif:.3f}")

    I_abs_prim = I_abs_dir + I_abs_dif
    I_tr_prim  = I_tr_dir  + I_tr_dif

    if verbose: print(f"  │  [3/4] Radiosités ({cfg.n_radiosity_iter} it.)...", end=" ", flush=True)
    I_abs_scat = radiosity_solver(geo, species, cfg, I_abs_prim, I_tr_prim)
    if verbose: print("OK")

    I_abs_tot = I_abs_prim + I_abs_scat

    # Normalisation : sum(I_abs_tot[s]) donne directement la fraction de I0
    # absorbée par l espèce s. beam_path_2d dépose le flux dans UNE cellule par
    # couche et compute_direct/diffuse divisent par n_beams → la somme spatiale
    # est une moyenne correcte sur la section W, indépendante de N_y.
    I_abs_sp = np.array([I_abs_tot[s].sum() for s in range(geo.n_species)])
    frac_abs = I_abs_sp / max(cfg.I0, 1e-12)
    frac_tr   = I_tr_prim / max(cfg.I0, 1e-12)

    if verbose:
        print(f"  └── OK  Σf_abs={frac_abs.sum():.3f}  f_trans={frac_tr:.3f}")

    return RadiativeBalance2D(
        I_abs_total=I_abs_tot, I_abs_per_species=I_abs_sp,
        frac_abs_species=frac_abs, frac_transmitted=frac_tr,
        I_abs_direct=I_abs_dir, I_abs_diffuse=I_abs_dif, I_abs_scattered=I_abs_scat,
        species_names=[sp.name for sp in species], geo=geo, cfg=cfg,
    )




# ────────────────────────────────────────────────────────────────────────────
# 7b.  SIMULATION EN BATCH (liste de directions solaires × fractions diffuses)
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class BatchResults:
    """
    Résultats d une simulation en batch : N_sim conditions radiatives
    appliquées à une géométrie fixe.

    Attributes
    ----------
    conditions : list[dict]
        Liste des N_sim conditions simulées.
        Chaque entrée contient : theta_deg, phi_deg, fd, I0.

    frac_abs   : np.ndarray (N_sim, n_sp)
        Fraction de I0 absorbée par chaque composante pour chaque condition.

    frac_trans : np.ndarray (N_sim,)
        Fraction de I0 transmise au sol pour chaque condition.

    frac_abs_direct   : np.ndarray (N_sim, n_sp)
    frac_abs_diffuse  : np.ndarray (N_sim, n_sp)
    frac_abs_scattered: np.ndarray (N_sim, n_sp)
        Décomposition de l absorption par type de rayonnement.

    species_names : list[str]
        Noms des composantes (végétaux puis PV).

    geo : RowIntercropGeometry
    """
    conditions:          List[dict]
    frac_abs:            np.ndarray   # (N_sim, n_sp)
    frac_trans:          np.ndarray   # (N_sim,)
    frac_abs_direct:     np.ndarray   # (N_sim, n_sp)
    frac_abs_diffuse:    np.ndarray   # (N_sim, n_sp)
    frac_abs_scattered:  np.ndarray   # (N_sim, n_sp)
    species_names:       List[str]
    geo:                 RowIntercropGeometry

    @property
    def N_sim(self) -> int:
        return len(self.conditions)

    @property
    def n_species(self) -> int:
        return len(self.species_names)

    def summary_table(self) -> None:
        """Affiche le tableau récapitulatif de toutes les conditions."""
        n_sp = self.n_species
        print("\n" + "═"*80)
        print("  RÉSULTATS BATCH  —  SIRASCA 2D")
        print("═"*80)
        hdr = (f"  {'#':>3}| {'Hour':>5}  | {'θ(°)':>5} | {'φ(°)':>5} | {'fd':>5} | "
               + "  ".join(f"{'fabs_'+str(s+1):>8}" for s in range(n_sp))
               + f"  | {'f_trans':>8}")
        print(hdr)
        print("  " + "-"*(len(hdr)-2))
        for k, cond in enumerate(self.conditions):
            row = (f"  {k+1:3d} | {cond['hour']:5.2f} | {cond['theta_deg']:5.1f} | {cond['phi_deg']:5.1f}"
                   f" | {cond['fd']:5.2f} | ")
            row += "  ".join(f"{self.frac_abs[k,s]:8.4f}" for s in range(n_sp))
            row += f"  | {self.frac_trans[k]:8.4f}"
            print(row)
        print("  " + "-"*(len(hdr)-2))
        # Moyennes
        row = f"  {'MOY':>3} | {'':>5} | {'':>5} | {'':>5} | "
        row += "  ".join(f"{self.frac_abs[:,s].mean():8.4f}" for s in range(n_sp))
        row += f"  | {self.frac_trans.mean():8.4f}"
        print(row)
        print("═"*80)
        print("  Légende : " + "  ".join(
            f"fabs_{s+1}={self.species_names[s]}" for s in range(n_sp)))

    def lad_summary(self) -> None:
        """Affiche les profils LAD/PAD (communs à toutes les simulations)."""
        dz = self.geo.dz; H = self.geo.H; N_z = self.geo.N_z
        n_sp = self.n_species
        print(f"\n  ── Profils LAD/PAD verticaux  (moyenne sur y) ─────────────")
        print(f"  {'Cche':>4} | {'z_sol':>6} | "
              + "  ".join(f"{'LAD_'+str(s+1):>9}" for s in range(n_sp)))
        print("  " + "-"*(20 + 11*n_sp))
        for i in range(N_z):
            z_sol = H - (i+0.5)*dz
            vals  = [self.geo.LAD_grids[s][i].mean() for s in range(n_sp)]
            print(f"  {i+1:4d} | {z_sol:6.3f} | "
                  + "  ".join(f"{v:9.4f}" for v in vals))
        print("  Légende : " + "  ".join(
            f"LAD_{s+1}={self.species_names[s]}" for s in range(n_sp)))

    def absorption_by_condition(self, s: int = 0) -> np.ndarray:
        """Retourne f_abs de la composante s pour toutes les conditions  (N_sim,)."""
        return self.frac_abs[:, s]

    def to_dict(self) -> dict:
        """Exporte les résultats sous forme de dictionnaire numpy."""
        out = {
            'theta_deg'   : np.array([c['theta_deg'] for c in self.conditions]),
            'phi_deg'     : np.array([c['phi_deg']   for c in self.conditions]),
            'fd'          : np.array([c['fd']         for c in self.conditions]),
            'frac_trans'  : self.frac_trans.copy(),
        }
        for s, nm in enumerate(self.species_names):
            key = nm.replace(' ', '_').replace('(', '').replace(')', '')
            out[f'frac_abs_{key}']       = self.frac_abs[:, s]
            out[f'frac_dir_{key}']       = self.frac_abs_direct[:, s]
            out[f'frac_dif_{key}']       = self.frac_abs_diffuse[:, s]
            out[f'frac_scat_{key}']      = self.frac_abs_scattered[:, s]
        return out


def run_batch(
    geo:          RowIntercropGeometry,
    species:      list,
    base_cfg:     RadiativeConfig,
    sun_dirs:     List[Tuple[float, float]],
    fd_values:    List[float],
    lst_hours:    List[float],
    I0:           float = 1.0,
    verbose:      bool  = True,
    verbose_each: bool  = False,
) -> BatchResults:
    """
    Simule une liste de conditions radiatives (θ_sun, φ_sun, fd) sur une
    géométrie fixe et retourne un BatchResults.

    Les conditions sont le produit cartésien sun_dirs × fd_values :
        N_sim = len(sun_dirs) × len(fd_values)

    Parameters
    ----------
    geo          : Géométrie 2D (fixe pour toutes les simulations).
    species      : Liste des composantes (SpeciesParams ou PVPanelParams).
    base_cfg     : Configuration de base. Seuls I0, n_az_sky, n_el_sky,
                   n_beams_per_layer, n_radiosity_iter, rho_soil sont utilisés.
                   theta_sun_deg, phi_sun_deg et fd sont remplacés par sun_dirs
                   et fd_values.
    sun_dirs     : Liste de (theta_deg, phi_deg) — directions solaires à simuler.
    fd_values    : Liste de fd — fractions diffuses à simuler.
                   Chaque fd correspond à chaque direction solaire.
    I0           : Irradiance incidente (normalisée à 1 par défaut).
    verbose      : Afficher le tableau de progression.
    verbose_each : Afficher le détail de chaque simulation (lent).

    Returns
    -------
    BatchResults contenant les N_sim résultats.

    Exemple à changer
    -------
    res = run_batch(geo, species, cfg,
        sun_dirs  = [(0., 180.), (30., 180.), (45., 180.), (60., 180.)],
        fd_values = [0.0, 0.15, 1.0])
    res.summary_table()
    res.lad_summary()
    """
    geo.validate()
    n_sp = geo.n_species

    # Construire la liste complète des conditions
    conditions = []
    id_fd = 0
    for theta_deg, phi_deg in sun_dirs:        
        conditions.append({
            'theta_deg': float(theta_deg),
            'phi_deg':   float(phi_deg),
            'fd':        float(fd_values[id_fd]),
            'hour':      float(lst_hours[id_fd]),
            'I0':        float(I0)
        })
        id_fd += 1
    N_sim = len(conditions)

    # Tableaux de résultats
    frac_abs      = np.zeros((N_sim, n_sp))
    frac_trans    = np.zeros(N_sim)
    frac_abs_dir  = np.zeros((N_sim, n_sp))
    frac_abs_dif  = np.zeros((N_sim, n_sp))
    frac_abs_scat = np.zeros((N_sim, n_sp))

    if verbose:
        print(f"\n  ┌── SIRASCA 2D  BATCH  ({'×'.join(str(x) for x in [len(sun_dirs), len(fd_values)])} = {N_sim} simulations)")
        print(f"  │  Grille {geo.N_z}×{geo.N_y}  W={geo.W}m  H={geo.H}m")
        print(f"  │  Composantes : {', '.join([sp.name for sp in species])}")
        hdr = (f"  │  {'#':>3} | {'θ(°)':>5} | {'φ(°)':>5} | {'fd':>4} | "
               + "  ".join(f"{'fabs_'+str(s+1):>7}" for s in range(n_sp))
               + f"  | {'f_tr':>6}")
        print(hdr)
        print("  │  " + "-"*(len(hdr)-5))

    for k, cond in enumerate(conditions):
        cfg_k = RadiativeConfig(
            I0               = cond['I0'],
            theta_sun_deg    = cond['theta_deg'],
            phi_sun_deg      = cond['phi_deg'],
            fd               = cond['fd'],
            rho_soil         = base_cfg.rho_soil,
            n_az_sky         = base_cfg.n_az_sky,
            n_el_sky         = base_cfg.n_el_sky,
            n_beams_per_layer= base_cfg.n_beams_per_layer,
            n_radiosity_iter = base_cfg.n_radiosity_iter,
        )
        res_k = run_2d_radiative_balance(geo, species, cfg_k, verbose=verbose_each)

        frac_abs[k]      = res_k.frac_abs_species
        frac_trans[k]    = res_k.frac_transmitted
        frac_abs_dir[k]  = np.array([res_k.I_abs_direct[s].sum()    for s in range(n_sp)]) / max(I0, 1e-12)
        frac_abs_dif[k]  = np.array([res_k.I_abs_diffuse[s].sum()   for s in range(n_sp)]) / max(I0, 1e-12)
        frac_abs_scat[k] = np.array([res_k.I_abs_scattered[s].sum() for s in range(n_sp)]) / max(I0, 1e-12)

        if verbose:
            row = (f"  │  {k+1:3d} | {cond['theta_deg']:5.1f} | {cond['phi_deg']:5.1f}"
                   f" | {cond['fd']:4.2f} | ")
            row += "  ".join(f"{frac_abs[k,s]:7.4f}" for s in range(n_sp))
            row += f"  | {frac_trans[k]:6.4f}"
            print(row)

    if verbose:
        print(f"  └── Batch terminé  ({N_sim} simulations)")

    return BatchResults(
        conditions        = conditions,
        frac_abs          = frac_abs,
        frac_trans        = frac_trans,
        frac_abs_direct   = frac_abs_dir,
        frac_abs_diffuse  = frac_abs_dif,
        frac_abs_scattered= frac_abs_scat,
        species_names     = [sp.name for sp in species],
        geo               = geo,
    )


# ────────────────────────────────────────────────────────────────────────────
# 8.  CONSTRUCTEURS DE GÉOMÉTRIES
# ────────────────────────────────────────────────────────────────────────────

def build_row_intercrop(
    species_params:   List[SpeciesParams],
    lai_total:        List[float],
    y_fracs:          List[Tuple[float,float]],   # (y0,y1) ∈ [0,1] par espèce
    canopy_height:    float = 2.0,
    band_width:       float = 4.0,
    N_z: int = 10, N_y: int = 20,
    row_azimuth_deg:  float = 0.0,
    lad_shape:        str   = "uniform",   # profil vertical : voir lad_profile()
    lad_peak_frac:    float = 0.5,         # position du pic (fraction de H)
) -> RowIntercropGeometry:
    """
    Géométrie en rangs juxtaposés. Chaque espèce occupe la bande transversale
    [y0_frac·W, y1_frac·W] avec un profil vertical de LAD paramétrable.

    Parameters
    ----------
    lad_shape     : Forme du profil vertical de LAD.
                    "uniform" | "parabolic" | "triangular" | "gaussian"
    lad_peak_frac : Position relative du pic dans [0, H]. 0 = sommet, 1 = sol.
    """
    LAD_grids = []
    dz = canopy_height / N_z
    for s, (y0, y1) in enumerate(y_fracs):
        grid = np.zeros((N_z, N_y))
        j0 = int(round(y0*N_y)); j1 = int(round(y1*N_y))
        j0, j1 = max(0,j0), min(N_y, max(j0+1,j1))
        n_cols = max(j1 - j0, 1)

        # Profil vertical normalisé
        w = lad_profile(N_z, z0_frac=0.0, z1_frac=1.0,
                        shape=lad_shape, peak_frac=lad_peak_frac)
        # Convention de l article : LAD(i,j) = LAI_s · w(i) / dz
        for i in range(N_z):
            grid[i, j0:j1] = lai_total[s] * w[i] / dz
        LAD_grids.append(grid)
    return RowIntercropGeometry(W=band_width, H=canopy_height,
        N_y=N_y, N_z=N_z, row_azimuth_deg=row_azimuth_deg, LAD_grids=LAD_grids)


# ────────────────────────────────────────────────────────────────────────────
# 8b. PROFIL VERTICAL DE LAD
# ────────────────────────────────────────────────────────────────────────────

def lad_profile(
    N_z:      int,
    z0_frac:  float = 0.0,
    z1_frac:  float = 1.0,
    shape:    str   = "uniform",
    peak_frac: float = 0.5,
) -> np.ndarray:
    """
    Calcule un profil vertical de LAD normalisé sur N_z couches.

    Le profil est défini sur la plage [z0_frac, z1_frac] (fractions de H,
    haut→bas). En dehors de cette plage, LAD = 0.

    Parameters
    ----------
    N_z       : Nombre de couches.
    z0_frac   : Début de la plage occupée (0 = sommet, 1 = sol).
    z1_frac   : Fin de la plage occupée.
    shape     : Forme du profil vertical :
                  "uniform"   — densité constante (LAD uniforme)
                  "parabolic" — parabole concave avec pic à peak_frac
                                dans la plage [z0, z1] ;
                                LAD(z) ∝ -(z - z_pic)²  + max
                                → nul aux bords, maximum au pic
                  "triangular"— triangle avec pic à peak_frac
                  "gaussian"  — gaussienne centrée à peak_frac,
                                σ = 0.25 × (z1-z0)
    peak_frac : Position relative du pic dans [z0_frac, z1_frac],
                en fraction de (z1-z0). 0 = haut de la plage, 1 = bas.
                Utilisé par "parabolic", "triangular", "gaussian".

    Returns
    -------
    w : np.ndarray (N_z,) — poids normalisés (somme = 1 sur la plage).
        w[i] est la fraction du LAI total attribuée à la couche i.

    Notes
    -----
    Pour un couvert homogène, utiliser shape="uniform".
    Pour un profil réaliste de graminées ou céréales, utiliser
    shape="parabolic" avec peak_frac≈0.3 (pic dans le tiers supérieur).
    """
    # Centres des couches en fraction de H (haut→bas)
    z_centers = (np.arange(N_z) + 0.5) / N_z   # (N_z,)
    span = z1_frac - z0_frac

    # Masque : couches dans la plage [z0_frac, z1_frac]
    mask = (z_centers >= z0_frac) & (z_centers < z1_frac)

    if not mask.any():
        # Plage trop étroite → on affecte la couche la plus proche
        idx = np.argmin(np.abs(z_centers - (z0_frac + z1_frac) / 2))
        w = np.zeros(N_z)
        w[idx] = 1.0
        return w

    # Position relative dans la plage [0, 1]
    z_rel = (z_centers[mask] - z0_frac) / span   # ∈ [0, 1]

    if shape == "uniform":
        vals = np.ones_like(z_rel)

    elif shape == "parabolic":
        # Parabole concave vers le bas : LAD(z) = -(z_rel - pic)² + offset
        # → nul aux bords (z_rel=0 et z_rel=1), maximum à z_rel=peak_frac
        # Formule : LAD(z) ∝ (z_rel)(1-z_rel) pour pic=0.5 (forme standard)
        # Généralisation à pic quelconque :
        #   LAD(z) ∝ (z_rel - a)(b - z_rel)  avec a≤0, b≥1 ajustés
        #   pour que le maximum soit en z_rel = peak_frac.
        # Ici on utilise la forme la plus simple : parabole symétrique
        # étirée pour placer le pic à peak_frac :
        p = float(np.clip(peak_frac, 0.01, 0.99))
        # Parabole passant par 0 en z_rel=0, 0 en z_rel=1, max en z_rel=p
        # f(z) = C * (z - 0)(1 - z) * correction_asymetrie
        # Version robuste : chapeau triangulaire lissé
        vals = -((z_rel - p) ** 2) + p * (1.0 - p)
        vals = np.maximum(vals, 0.0)

    elif shape == "triangular":
        p = float(np.clip(peak_frac, 0.01, 0.99))
        vals = np.where(z_rel <= p,
                        z_rel / max(p, 1e-6),
                        (1.0 - z_rel) / max(1.0 - p, 1e-6))
        vals = np.maximum(vals, 0.0)

    elif shape == "gaussian":
        p   = float(np.clip(peak_frac, 0.01, 0.99))
        sig = 0.25 * span          # σ = quart de la plage
        vals = np.exp(-0.5 * ((z_rel - p) / sig) ** 2)

    else:
        raise ValueError(f"shape='{shape}' inconnu. "
                         "Choisir : 'uniform', 'parabolic', 'triangular', 'gaussian'.")

    # Normalisation : les poids doivent sommer à 1
    total = vals.sum()
    if total < 1e-12:
        vals = np.ones_like(vals)
        total = vals.sum()
    vals /= total

    # Remise en place dans le vecteur complet
    w = np.zeros(N_z)
    w[mask] = vals
    return w


def build_stratified_mixed(
    species_params:  List[SpeciesParams],
    lai_per_species: List[float],
    height_fracs:    List[Tuple[float,float]],   # (z0,z1) ∈ [0,1] par espèce (haut→bas)
    canopy_height:   float = 2.0,
    band_width:      float = 4.0,
    N_z: int = 10, N_y: int = 20,
    row_azimuth_deg: float = 0.0,
    lad_shape:       str   = "uniform",   # profil vertical : voir lad_profile()
    lad_peak_frac:   float = 0.5,         # position du pic (fraction de la plage)
) -> RowIntercropGeometry:
    """
    Couvert bien mélangé horizontalement, stratifié verticalement.
    Chaque espèce occupe la plage de couches [z0·H, z1·H] avec un profil
    vertical de LAD de forme paramétrable.

    Parameters
    ----------
    lad_shape     : Forme du profil vertical de LAD pour toutes les espèces.
                    "uniform" | "parabolic" | "triangular" | "gaussian"
                    Voir lad_profile() pour le détail.
    lad_peak_frac : Position relative du pic dans la plage de chaque espèce.
                    0 = sommet de la plage, 1 = bas de la plage.
    """
    LAD_grids = []
    dz = canopy_height / N_z
    for s, (z0, z1) in enumerate(height_fracs):
        # Poids normalisés du profil vertical (somme = 1)
        w = lad_profile(N_z, z0_frac=z0, z1_frac=z1,
                        shape=lad_shape, peak_frac=lad_peak_frac)
        # Convention de l article (Sinoquet & Bonhomme 1992) :
        # LAD(i,j) = LAI_s · w(i) / dz    [m² feuille / m³]
        # Le LAI est référencé à la projection verticale de la couche,
        # indépendamment de la largeur de bande W. Cette convention est
        # identique à celle du code original de l article.
        grid = np.zeros((N_z, N_y))
        for i in range(N_z):
            grid[i, :] = lai_per_species[s] * w[i] / dz
        LAD_grids.append(grid)
    return RowIntercropGeometry(W=band_width, H=canopy_height,
        N_y=N_y, N_z=N_z, row_azimuth_deg=row_azimuth_deg, LAD_grids=LAD_grids)




# ────────────────────────────────────────────────────────────────────────────
# 8c. PROFIL HORIZONTAL DE LAD ET CAS H0 / H1 / H2 (article §4)
# ────────────────────────────────────────────────────────────────────────────

def lad_horizontal_profile(
    N_y:       int,
    y0_frac:   float = 0.0,
    y1_frac:   float = 1.0,
    shape:     str   = "uniform",
    gap_frac:  float = 0.0,
    gap_side:  str   = "both",
) -> np.ndarray:
    """
    Calcule un profil horizontal de LAD normalisé sur N_y tranches.

    La bande de l espèce couvre [y0_frac·W, y1_frac·W].
    A l intérieur de cette bande, le profil latéral peut varier.

    Cas de l article (§4, Fig. 1) :
      H0 : couvert homogène → shape="uniform", gap_frac=0
      H1 : rangs contigus   → shape="uniform", gap_frac=0  (même que H0
                               mais chaque espèce a sa propre bande)
      H2 : rangs avec espace libre (gap) inter-rang
           → shape="uniform", gap_frac > 0
           Le gap est positionné sur les bords de la bande (gap_side).

    Parameters
    ----------
    N_y      : Nombre de tranches horizontales.
    y0_frac  : Début de la bande (fraction de W, 0=gauche).
    y1_frac  : Fin de la bande (fraction de W).
    shape    : Forme du profil à l intérieur de la bande :
               "uniform"   → LAD constant dans la bande
               "parabolic" → pic au centre de la bande, nul aux bords
               "gaussian"  → cloche gaussienne centrée dans la bande
    gap_frac : Fraction de la demi-largeur de bande laissée vide
               de chaque côté (H2). gap_frac ∈ [0, 0.5[.
               Exemple : gap_frac=0.2 → 20% de la bande côté gauche
               et 20% côté droit sont vides (sol nu).
    gap_side : "both" (défaut) → gap des deux côtés de la bande
               "left"         → gap uniquement à gauche
               "right"        → gap uniquement à droite

    Returns
    -------
    h : np.ndarray (N_y,) — poids horizontaux normalisés (somme = 1).
        h[j] est la fraction du LAI total attribuée à la tranche j.
    """
    y_centers = (np.arange(N_y) + 0.5) / N_y     # centres des tranches ∈ [0,1]
    span = y1_frac - y0_frac

    # Masque : tranches dans la bande de l espèce
    mask_band = (y_centers >= y0_frac) & (y_centers < y1_frac)

    if not mask_band.any():
        # Bande trop étroite → tranche la plus proche
        j_mid = int(np.argmin(np.abs(y_centers - (y0_frac + y1_frac) / 2)))
        h = np.zeros(N_y)
        h[j_mid] = 1.0
        return h

    # Position relative dans la bande ∈ [0, 1]
    y_rel = (y_centers[mask_band] - y0_frac) / span

    # ── Masque du gap (H2) ────────────────────────────────────────────────
    gf = float(np.clip(gap_frac, 0.0, 0.49))
    if gf > 0:
        if gap_side == "both":
            in_gap = (y_rel < gf) | (y_rel > 1.0 - gf)
        elif gap_side == "left":
            in_gap = y_rel < gf
        elif gap_side == "right":
            in_gap = y_rel > 1.0 - gf
        else:
            in_gap = np.zeros_like(y_rel, dtype=bool)
    else:
        in_gap = np.zeros_like(y_rel, dtype=bool)

    # Position relative dans la zone végétalisée (hors gap)
    if gap_side == "both":
        y_veg = (y_rel - gf) / max(1.0 - 2*gf, 1e-6)
    elif gap_side == "left":
        y_veg = (y_rel - gf) / max(1.0 - gf, 1e-6)
    elif gap_side == "right":
        y_veg = y_rel / max(1.0 - gf, 1e-6)
    else:
        y_veg = y_rel
    y_veg = np.clip(y_veg, 0.0, 1.0)

    # ── Profil horizontal dans la zone végétalisée ────────────────────────
    if shape == "uniform":
        vals = np.ones(len(y_rel))

    elif shape == "parabolic":
        # Parabole concave : max au centre, nul aux bords de la bande végétalisée
        vals = 4.0 * y_veg * (1.0 - y_veg)   # max = 1 en y_veg=0.5

    elif shape == "gaussian":
        sig  = 0.25
        vals = np.exp(-0.5 * ((y_veg - 0.5) / sig) ** 2)

    else:
        raise ValueError(f"shape horizontal \'{shape}\' inconnu. "
                         "Choisir : \'uniform\', \'parabolic\', \'gaussian\'.")

    # Annuler le gap
    vals = np.where(in_gap, 0.0, vals)

    # Normalisation
    total = vals.sum()
    if total < 1e-12:
        vals = np.where(~in_gap, 1.0, 0.0)
        total = vals.sum()
    if total > 1e-12:
        vals /= total

    h = np.zeros(N_y)
    h[mask_band] = vals
    return h


def build_H_case(
    case:            str,
    species_params:  List[SpeciesParams],
    lai_per_species: List[float],
    height_fracs:    List[Tuple[float,float]],   # (z0,z1) ∈ [0,1] vertical par espèce
    y_fracs:         List[Tuple[float,float]],   # (y0,y1) ∈ [0,1] horizontal par espèce
    canopy_height:   float = 2.0,
    band_width:      float = 4.0,
    N_z:             int   = 10,
    N_y:             int   = 20,
    row_azimuth_deg: float = 0.0,
    lad_shape_z:     str   = "parabolic",  # profil vertical
    lad_peak_frac_z: float = 0.5,
    gap_frac:        float = 0.1,          # fraction de gap inter-rang (H2 seulement)
) -> RowIntercropGeometry:
    """
    Construit l une des trois géométries canoniques de Sinoquet & Bonhomme (1992).

    Cas H0, H1, H2 (article §4, Table 1 et Fig. 1) :

    H0 — Couvert horizontalement homogène (référence 1D)
         Chaque espèce est distribuée uniformément sur toute la largeur W.
         LAD(i,j) constant en j pour une espèce donnée à la couche i.
         → équivalent à la version 1D bien mélangée de SIRASCA.

    H1 — Rangs contigus sans espace libre (row intercrop, pas de gap)
         Chaque espèce occupe une bande transversale [y0·W, y1·W]
         avec une distribution horizontale uniforme à l intérieur de sa bande.
         Les espèces se touchent sans espace entre elles.

    H2 — Rangs avec espace libre inter-rang (gap entre les bandes)
         Comme H1, mais avec une zone de sol nu de largeur gap_frac·bande
         de chaque côté de la bande de chaque espèce.
         Reproduit les inter-rangs observés en interculture réelle.

    Dans les trois cas, le profil vertical suit lad_shape_z.

    Parameters
    ----------
    case             : "H0", "H1", ou "H2"
    species_params   : Paramètres optiques des espèces.
    lai_per_species  : LAI total de chaque espèce.
    height_fracs     : (z0, z1) par espèce (fraction de H, vertical).
    y_fracs          : (y0, y1) par espèce (fraction de W, horizontal).
                       Utilisé pour H1 et H2. Pour H0, ignoré (toute la largeur).
    canopy_height    : Hauteur totale du couvert (m).
    band_width       : Largeur de la bande répétitive (m).
    N_z, N_y         : Résolution de la grille.
    lad_shape_z      : Forme du profil vertical ("parabolic", "uniform", etc.)
    lad_peak_frac_z  : Position du pic vertical.
    gap_frac         : Fraction de la demi-bande laissée libre de chaque côté (H2).
                       Exemple : 0.1 → 10% de vide de chaque côté de la bande.

    Returns
    -------
    RowIntercropGeometry avec grilles LAD (N_z, N_y) par espèce.

    Notes
    -----
    Référence : Sinoquet & Bonhomme (1992), §4 "Canopy structures" et Fig. 1.
    Les cas H0/H1/H2 correspondent aux structures simulées dans les figures
    de résultats (Figs 5-9 de l article).
    """
    case = case.upper()
    assert case in ("H0", "H1", "H2"), f"cas={case} invalide. Choisir H0, H1 ou H2."

    n_sp = len(species_params)
    dz   = canopy_height / N_z
    LAD_grids = []

    for s in range(n_sp):
        z0, z1 = height_fracs[s]
        y0, y1 = y_fracs[s]

        # ── Profil vertical normalisé (commun aux 3 cas) ──────────────────
        w_z = lad_profile(N_z, z0_frac=z0, z1_frac=z1,
                          shape=lad_shape_z, peak_frac=lad_peak_frac_z)
        # w_z[i] : fraction du LAI attribuée à la couche i

        # ── Profil horizontal normalisé selon le cas ──────────────────────
        if case == "H0":
            # Couvert homogène : espèce distribuée sur toute la largeur
            h_y = lad_horizontal_profile(N_y, y0_frac=0.0, y1_frac=1.0,
                                         shape="uniform", gap_frac=0.0)

        elif case == "H1":
            # Rangs contigus : espèce dans [y0, y1], profil uniforme en y
            h_y = lad_horizontal_profile(N_y, y0_frac=y0, y1_frac=y1,
                                         shape="uniform", gap_frac=0.0)

        elif case == "H2":
            # Rangs avec gap : espace libre aux bords de chaque bande
            h_y = lad_horizontal_profile(N_y, y0_frac=y0, y1_frac=y1,
                                         shape="uniform", gap_frac=gap_frac,
                                         gap_side="both")

        # ── Construction de la grille LAD 2D ─────────────────────────────
        # Convention de l article (Sinoquet & Bonhomme 1992) :
        # LAD(i,j) = LAI_s · w_z(i) / dz    dans les cellules occupées
        #          = 0                         dans les cellules vides (gap ou hors bande)
        #
        # h_y(j) est utilisé comme MASQUE binaire (1 = cellule occupée, 0 = vide)
        # et non comme pondération normalisée. Le LAD dans la bande est identique
        # à build_stratified_mixed : LAI_s · w_z(i) / dz.
        #
        # H0 : h_y > 0 partout → même LAD que couvert homogène
        # H1 : h_y > 0 dans la demi-bande, 0 ailleurs → LAD concentré = ×2 vs H0
        # H2 : comme H1 mais avec sol nu en bordure de bande
        mask_y = (h_y > 0).astype(float)   # 1 si cellule occupée, 0 sinon
        grid = np.zeros((N_z, N_y))
        for i in range(N_z):
            grid[i, :] = lai_per_species[s] * w_z[i] / dz * mask_y

        LAD_grids.append(grid)

    return RowIntercropGeometry(
        W=band_width, H=canopy_height,
        N_y=N_y, N_z=N_z,
        row_azimuth_deg=row_azimuth_deg,
        LAD_grids=LAD_grids,
    )




# ────────────────────────────────────────────────────────────────────────────
# 8d. CONSTRUCTEUR AGRIVOLTAÏQUE (végétation + panneaux PV)
# ────────────────────────────────────────────────────────────────────────────

def build_agrivoltaic(
    # ── Végétation ──────────────────────────────────────────────────────
    veg_params:      List[SpeciesParams],
    lai_per_veg:     List[float],
    height_fracs_veg: List[Tuple[float,float]],  # (z0,z1) ∈ [0,1] par espèce végétale
    # ── Panneaux PV ─────────────────────────────────────────────────────
    pv_params:       List[PVPanelParams],
    l_panneau_pv:    List[float],                # largeur physique du panneau (m), parallèle aux rangs PV
    y_fracs_pv:      List[Tuple[float,float]],   # (y0,y1) ∈ [0,1] position horizontale
    z_fracs_pv:      List[Tuple[float,float]],   # (z0,z1) ∈ [0,1] position verticale
    # ── Géométrie commune ────────────────────────────────────────────────
    canopy_height:   float = 3.0,
    band_width:      float = 6.0,
    N_z:             int   = 12,
    N_y:             int   = 24,
    row_azimuth_deg: float = 0.0,
    lad_shape:       str   = "uniform",
    lad_peak_frac:   float = 0.5,
    y_fracs_veg:     list  = None,   # (y0,y1) ∈ [0,1] par espèce végétale
                                     # None → chaque espèce sur toute la largeur W
    lad_shape_veg:   list  = None,   # forme profil vertical par espèce
                                     # None → lad_shape pour toutes
    lad_peak_veg:    list  = None,   # position pic vertical par espèce
                                     # None → lad_peak_frac pour toutes
    lad_shape_y_veg: list  = None,   # profil horizontal par espèce dans la bande
                                     # "uniform"|"parabolic"|"gaussian"
                                     # None → "uniform" (H1, masque binaire)
    gap_frac_veg:    list  = None,   # gap inter-rang par espèce (fraction bande)
                                     # None → 0.0 (pas de gap)
) -> Tuple[RowIntercropGeometry, list]:
    # Note : l azimut des rangs PV est porté par PVPanelParams.row_azimuth_deg
    # et non par ce constructeur. Chaque rang PV peut avoir son propre azimut.
    """
    Construit une géométrie 2D pour un système agrivoltaïque :
    végétation sous/entre des rangs de panneaux photovoltaïques.

    La grille LAD contient d abord les espèces végétales, puis les panneaux PV.
    Les panneaux sont représentés par leur PAD (Panel Area Density) en m²/m³,
    dans la couche et la bande transversale qu ils occupent.

    Parameters
    ----------
    veg_params       : Paramètres optiques des espèces végétales.
    lai_per_veg      : LAI de chaque espèce végétale (convention article).
    height_fracs_veg : (z0, z1) fractions verticales par espèce végétale.
    pv_params        : Paramètres des rangs de panneaux PV.
    l_panneau_pv     : Largeur physique de chaque rang PV (m), dimension
                       parallèle aux rangs (axe x non discrétisé).
                       Le PAD par cellule est calculé automatiquement :
                           PAD(i,j) = l_panneau / (dy × dz)
                       de sorte que l intégration spatiale redonne exactement
                       l_panneau m² de panneau par m de rang.
    y_fracs_pv       : (y0, y1) positions horizontales des rangs PV ∈ [0,1].
    z_fracs_pv       : (z0, z1) positions verticales des rangs PV ∈ [0,1].
                       Exemple : (0.0, 0.1) pour panneaux en haut du couvert.
    canopy_height    : Hauteur totale de la grille (m) — doit englober les PV.
    band_width       : Largeur de la bande répétitive (m).
    lad_shape        : Forme du profil vertical de LAD pour la végétation.
    lad_peak_frac    : Position du pic de LAD pour la végétation.

    Returns
    -------
    geo      : RowIntercropGeometry contenant toutes les grilles LAD
               (végétation + PV dans l ordre).
    all_sp   : list[SpeciesParams | PVPanelParams] dans le même ordre.

    Notes
    -----
    Les panneaux PV sont opaques par convention (tau_pv=0) et ne diffusent
    que par leur réflectance rho_pv. Leur coefficient d extinction K_pv(θ,φ)
    est calculé à la volée dans beam_path_2d selon la direction du faisceau.

    L azimut des rangs PV (angle des rangées par rapport à l axe x des rangs
    végétaux) est spécifié via PVPanelParams.row_azimuth_deg. Cet angle modifie
    l azimut apparent du faisceau dans le repère des PV, ce qui affecte K_pv
    et donc l extinction optique par les panneaux. Il est distinct de gamma_deg
    (azimut de la NORMALE du panneau, qui détermine son orientation active).

    Exemples d orientation :
      row_azimuth_deg=0°  → rangs PV // aux rangs végétaux (axe x) — défaut
      row_azimuth_deg=90° → rangs PV ⊥ aux rangs végétaux (axe y)
      row_azimuth_deg=45° → rangs PV à 45° des rangs végétaux

    Exemple
    -------
    # Agrivoltaïque : maïs sous panneaux inclinés à 30° plein Sud
    geo, sp = build_agrivoltaic(
        veg_params=[SpeciesParams("Maïs", alpha_deg=75.)],
        lai_per_veg=[3.0],
        height_fracs_veg=[(0.33, 1.0)],       # maïs dans les 2/3 inférieurs
        pv_params=[PVPanelParams("PV", beta_deg=30., gamma_deg=180., rho_pv=0.05)],
        l_panneau_pv=[1.0],                    # panneau de 1 m de large (// aux rangs)
        y_fracs_pv=[(0.2, 0.8)],              # panneaux sur 60% de la largeur
        z_fracs_pv=[(0.0, 0.15)],             # panneaux dans le tiers supérieur
        canopy_height=4.0,
        band_width=8.0,
    )
    """
    n_veg = len(veg_params)
    n_pv  = len(pv_params)
    dz    = canopy_height / N_z
    LAD_grids = []

    # ── Grilles LAD végétation ────────────────────────────────────────────
    # Résolution des paramètres par espèce (avec valeurs par défaut globales)
    _y_fracs_veg    = y_fracs_veg    if y_fracs_veg    is not None else [(0.0, 1.0)] * n_veg
    _lad_shape_veg  = lad_shape_veg  if lad_shape_veg  is not None else [lad_shape]     * n_veg
    _lad_peak_veg   = lad_peak_veg   if lad_peak_veg   is not None else [lad_peak_frac] * n_veg
    _lad_shape_y    = lad_shape_y_veg if lad_shape_y_veg is not None else ["uniform"]   * n_veg
    _gap_frac_veg   = gap_frac_veg   if gap_frac_veg   is not None else [0.0]           * n_veg

    dy = band_width / N_y
    for s in range(n_veg):
        z0, z1     = height_fracs_veg[s]
        y0_v, y1_v = _y_fracs_veg[s]
        shape_z    = _lad_shape_veg[s]
        peak_z     = _lad_peak_veg[s]
        shape_y    = _lad_shape_y[s]
        gap_f      = _gap_frac_veg[s]

        # Profil vertical normalisé (somme = 1)
        w = lad_profile(N_z, z0_frac=z0, z1_frac=z1,
                        shape=shape_z, peak_frac=peak_z)

        # Profil horizontal dans la bande [y0_v, y1_v]
        #
        # Convention article : LAD(i,j) = LAI_s * w(i) / dz  dans chaque cellule occupée.
        # Le LAD est défini PAR CELLULE et ne dépend pas de la largeur de la bande.
        #
        # lad_horizontal_profile retourne h_y normalisé (Σ = 1), qui sert de
        # PONDÉRATION relative entre cellules (parabolic, gaussian...).
        # Pour respecter la convention article, on multiplie par n_cols_eff afin
        # que le LAD dans une cellule typiquement occupée vaille LAI × w(i) / dz.
        #
        # n_cols_eff = nombre de colonnes effectivement occupées (hors gap)
        h_y = lad_horizontal_profile(
            N_y, y0_frac=y0_v, y1_frac=y1_v,
            shape=shape_y, gap_frac=gap_f, gap_side="both"
        )
        # Nombre de colonnes occupées (h_y > 0)
        n_cols_eff = max((h_y > 0).sum(), 1)
        # Dénormalisation : h_y × n_cols_eff → valeur moyenne = 1 dans les cellules occupées
        # → LAD moyen = LAI × w(i) / dz  (convention article par cellule)
        h_y_denorm = h_y * n_cols_eff

        grid = np.zeros((N_z, N_y))
        for i in range(N_z):
            grid[i, :] = lai_per_veg[s] * w[i] / dz * h_y_denorm
        LAD_grids.append(grid)

    # ── Grilles PAD panneaux PV ───────────────────────────────────────────
    # Convention physique :
    #   Le panneau occupe l_panneau mètres dans la direction x (parallèle aux rangs).
    #   PAD(i,j) = l_panneau / (n_cols × dy × dz)   [m² panneau / m³ cellule]
    #   Vérif : Σ_{i,j occupés} PAD × dy × dz = l_panneau ✓
    #
    # Les paramètres h_proj_x et l_pan_x sont injectés dans PVPanelParams
    # pour permettre le calcul de coverage_x (discontinuité en x).
    for p in range(n_pv):
        # Injecter h_proj_x et l_pan_x dans PVPanelParams pour coverage_x
        h_proj_p = l_panneau_pv[p] * np.sin(pv_params[p].beta)                    if hasattr(pv_params[p], 'beta') else 0.
        # On modifie les attributs de l instance directement
        object.__setattr__(pv_params[p], 'h_proj_x', float(h_proj_p))
        object.__setattr__(pv_params[p], 'l_pan_x',  float(l_panneau_pv[p]))
        grid = np.zeros((N_z, N_y))
        z0_pv, z1_pv = z_fracs_pv[p]
        y0_pv, y1_pv = y_fracs_pv[p]

        # Colonnes (tranches y) occupées par les panneaux
        j0 = int(round(y0_pv * N_y)); j1 = int(round(y1_pv * N_y))
        j0, j1 = max(0, j0), min(N_y, max(j0 + 1, j1))
        n_cols = j1 - j0   # nombre de tranches y occupées

        # PAD dans chaque cellule occupée :
        #   Σ_{i,j} PAD(i,j) × dy × dz = l_panneau  [m² panneau / m de rang]
        #   PAD(i,j) = l_panneau / (n_cols × n_cz_eff × dy × dz)
        # où n_cz_eff est le nombre effectif de couches occupées (peut être
        # fractionnaire si les limites ne coïncident pas avec les couches).
        # On calcule n_cz_eff comme la somme des fractions overlap/dz :
        #   n_cz_eff = Σ_i overlap_i / dz = (z1_pv - z0_pv) × N_z
        # PAD(i,j) = l_panneau / (n_cols × dy × dz)
        #
        # Démonstration :
        #   Σ_{i,j} PAD(i,j) × dy × dz
        #   = [l / (n_cols×dy×dz)] × dy × dz × n_cols × Σ_i(overlap_i/span)
        #   = l × Σ_i(overlap_i/span) = l × 1 = l  [m² panneau / m rang]  ✓
        #
        # La pondération overlap/span répartit le PAD proportionnellement
        # sur les couches qui chevauchent la plage des panneaux.
        span = z1_pv - z0_pv
        pad_cellule = l_panneau_pv[p] / max(n_cols * dy * dz, 1e-12)

        # Couches (tranches z) occupées par les panneaux.
        # Cas général  (β > 0°) : span > 0, répartition proportionnelle au chevauchement.
        # Cas horizontal (β = 0°) : z0_pv = z1_pv → span = 0.
        #   Le panneau est infiniment mince en z ; on l'affecte à la couche
        #   qui contient la hauteur H_BAS_PV (= H_TOTAL × z0_pv).
        #   PAD(i,j) = l_panneau / (n_cols × dy × dz) dans cette unique couche,
        #   de sorte que Σ PAD·dy·dz = l_panneau  ✓  (même convention que β>0°).
        if span <= 1e-9:
            # Panneau horizontal : une seule couche à z_frac = z0_pv
            z_mid = z0_pv  # fraction depuis le haut (0=sommet, 1=sol)
            i_flat = int(np.clip(np.floor(z_mid * N_z), 0, N_z - 1))
            # Si z0_pv == 1.0 (sol), on prend la dernière couche
            if i_flat >= N_z:
                i_flat = N_z - 1
            grid[i_flat, j0:j1] = pad_cellule
        else:
            for i in range(N_z):
                top = i / N_z; bot = (i + 1) / N_z
                overlap = max(0., min(bot, z1_pv) - max(top, z0_pv))
                if overlap > 0:
                    grid[i, j0:j1] = pad_cellule * (overlap / span)
        LAD_grids.append(grid)

    geo = RowIntercropGeometry(
        W=band_width, H=canopy_height,
        N_y=N_y, N_z=N_z,
        row_azimuth_deg=row_azimuth_deg,
        LAD_grids=LAD_grids,
    )

    all_sp = list(veg_params) + list(pv_params)
    return geo, all_sp


# ────────────────────────────────────────────────────────────────────────────
# 9.  EXEMPLES D'UTILISATION
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Ex 1 : interculture en rangs séparés ─────────────────────────────────
    print("\n▶  EX 1 — Rangs séparés : Maïs (érect.) | Légumineuse (plano.)")
    sp_M = SpeciesParams("Maïs",        alpha_deg=75., rho=.10, tau_leaf=.05)
    sp_L = SpeciesParams("Légumineuse", alpha_deg=30., rho=.10, tau_leaf=.05)

    geo1 = build_row_intercrop(
        [sp_M, sp_L], [3., 2.], [(0., .5), (.5, 1.)],
        canopy_height=2., band_width=4., N_z=10, N_y=20)

    cfg1 = RadiativeConfig(theta_sun_deg=30., phi_sun_deg=180., fd=.15, rho_soil=.10,
                           n_az_sky=6, n_el_sky=4, n_beams_per_layer=20, n_radiosity_iter=5)

    res1 = run_2d_radiative_balance(geo1, [sp_M, sp_L], cfg1)
    res1.print_summary()

    # ── Ex 2 : couvert homogène (validation vs version 1D) ───────────────────
    print("\n▶  EX 2 — Couvert homogène bien mélangé (LAI_A=3, LAI_B=2)")
    sp_A = SpeciesParams("Espèce A (érigée)",    alpha_deg=57.3, rho=.10, tau_leaf=.05)
    sp_B = SpeciesParams("Espèce B (planophile)", alpha_deg=30.,  rho=.10, tau_leaf=.05)

    geo2 = build_stratified_mixed(
        [sp_A, sp_B], [3., 2.], [(0.,1.),(0.,1.)],
        canopy_height=2., band_width=4., N_z=10, N_y=20)

    cfg2 = RadiativeConfig(theta_sun_deg=30., phi_sun_deg=180., fd=.15, rho_soil=.10,
                           n_az_sky=8, n_el_sky=5, n_beams_per_layer=20, n_radiosity_iter=6)

    res2 = run_2d_radiative_balance(geo2, [sp_A, sp_B], cfg2)
    res2.print_summary()

    # ── Ex 3 : stratification verticale ──────────────────────────────────────
    print("\n▶  EX 3 — Stratification verticale : A (60% haut) / B (40% bas)")
    sp_C = SpeciesParams("A (sphérique, haute)",  alpha_deg=57.3, rho=.10, tau_leaf=.05)
    sp_D = SpeciesParams("B (planophile, basse)",  alpha_deg=20.,  rho=.10, tau_leaf=.05)

    geo3 = build_stratified_mixed(
        [sp_C, sp_D], [3., 3.], [(0.,.6),(.6,1.)],
        canopy_height=2., band_width=4., N_z=10, N_y=20)

    res3 = run_2d_radiative_balance(geo3, [sp_C, sp_D], cfg2)
    res3.print_summary()

    # ── Ex 4 : effet de l'orientation des rangs ───────────────────────────────
    print("\n▶  EX 4 — Effet orientation des rangs (soleil à l'Est, θ=45°)")
    for az, lbl in [(0., "Rangs N-S"), (90., "Rangs E-O")]:
        g = build_row_intercrop(
            [sp_M, sp_L], [3., 2.], [(0.,.5),(.5,1.)],
            canopy_height=2., band_width=4., N_z=10, N_y=20,
            row_azimuth_deg=az)
        cfgE = RadiativeConfig(theta_sun_deg=45., phi_sun_deg=90., fd=.15, rho_soil=.10,
                               n_az_sky=6, n_el_sky=4, n_beams_per_layer=20, n_radiosity_iter=5)
        r = run_2d_radiative_balance(g, [sp_M, sp_L], cfgE, verbose=True)
        fa = r.frac_abs_species
        print(f"  {lbl:12s}: Maïs={fa[0]:.3f}  Légumineuse={fa[1]:.3f}  Trans={r.frac_transmitted:.3f}")
        print(f"\n {fa}")
        # print(f"\n {r}")