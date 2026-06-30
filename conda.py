conda import numpy as np
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *

#scene importatioion
scene_panel_hat =Scene(r"C:\Users\mbabity\Documents\PlantGL\MAPPING_CARIBU\bgeom_USEFUL\chapeau_norm_est.bgeom")
Viewer.display(scene_panel_hat)
scene_sol = Shape(Box(Vector3(20,20,000.1)),Material(Color3(137,81,41)))
scene_panel_hat.add(scene_sol)
Viewer.display(scene_panel_hat)

