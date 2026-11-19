# MODULES IMPORTATION
# 1- CARIBU AND PLANTGL BIBLIOTEQUES
from openalea.caribu.CaribuScene import CaribuScene
from openalea.caribu.plantgl_adaptor import scene_to_cscene
from openalea.plantgl.all import *

# 2- SCENE CREATION MODULE IMPORTATION 
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import scene_modelling_normal
from MAPPING_CARIBU.MODULE_TRACKING import solar_tracking_caribu
from MAPPING_CARIBU.MODULE_PANEL_NORMAL import recup_meteo
from MAPPING_CARIBU import MODULE_MAPPING

from MAPPING_CARIBU.MODULE_PANEL_NORMAL.scene_modelling_normal import scene_consrtructor_contrl

# 3- NUMPY PANDAS SCIPY AND MATPLOTLIB IMPORTATIONS
import pandas as pd 
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.tri as tri 
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1 import make_axes_locatable

# 4- NATIVE MODULES PYTHON IMPORTATIONS 
import math
import datetime
import multiprocessing

# 1- logging FUNCTION 
def log(message):
    print('{0} {1}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)

## getting uniquely the panels of the scene
def get_panels(scene):
    """_summary_
    Args:
        scene (_panel_): _for plotting in matplotlib_
    Returns:
        _scene_panel plangl_: _description_
    """
    panels=[]
    soil=[]
    for shape in scene:
        if shape.id== 3000000:
            panels.append(shape)
        else:
            soil.append(shape)
    return Scene(panels)













