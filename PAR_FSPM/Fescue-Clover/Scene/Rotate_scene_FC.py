from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
from math import radians

s=Scene(r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\Scene\as3c2.bgeom')

scene = Scene()
for shp in s:
    ax =AxisRotated(Vector3(0,0,1),radians(90),shp.geometry)
    color = shp.appearance.deepcopy()
    shp2= Shape(ax,Material(color),shp.id)
    scene.add(shp2)

scene.save(r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\Scene\as3c2_2.bgeom')
