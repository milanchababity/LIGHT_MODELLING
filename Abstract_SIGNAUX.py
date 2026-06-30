from SIGNAUX.MODULES import MODULE_SIGNAUX_AP,SIGNALS_FONCTIONS
import multiprocessing

#wrapper fonction 
def wrapper_Simulation_signaux(args):
    return MODULE_SIGNAUX_AP.Simulation_signaux(**args)

if __name__ == "__main__":
    # congigurations listes 
    params_panel_couvert={
    "orientation":"sud",
    "type_panneau":"normal",
    "longueur_p":0.31, ### panel width
    "largeur_p":0.424,# panel length
    "resolution_p":0.4, # for the mesh when use mesh panel fonction
    "nb_panel":1, # the standard for simulation
    "nb_rangee":1, # the standard for simulation
    "ecart_panel":3.64,# about panel width to concatenate two panels
    "ecart_rangee":2.5, # dtistance between two divide(piqué)
    "hauteur_haut_p":4, # panel heigth max
    "hauteur_bas_p":4, # panel heigth min
    "panel_opacity":1, # beyon 1 for panel semitransparent
    "angle_p":0} # angle beta_p (tilt)
    
    config_panel=[
        {"dicco_paneau":params_panel_couvert,
         "day_of_year":172,
         "heure":12,
         "latitude":45.18,
         "path_bgeom":"C:/Users/mbabity/Documents/PlantGL/PAR_FSPM/Fescue-Alfalfa/Scene/LD2-asso-luz.bgeom",
         "patern":[-0.53,-0.155,0.53,0.155],
         "panel":True,
         "suffixe":"panel"},
        
        {"dicco_paneau":params_panel_couvert,
         "day_of_year":172,
         "heure":12,
         "latitude":45.18,
         "path_bgeom":"C:/Users/mbabity/Documents/PlantGL/PAR_FSPM/Fescue-Alfalfa/Scene/LD2-asso-luz.bgeom",
         "patern":[-0.53,-0.155,0.53,0.155],
         "panel":False,
         "suffixe":"plant"
            
        }
    ]
    MODULE_SIGNAUX_AP.log("Starting simulations with multiprocessing")
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(wrapper_Simulation_signaux, config_panel)
        
    MODULE_SIGNAUX_AP.log("Simulations completed successfully")