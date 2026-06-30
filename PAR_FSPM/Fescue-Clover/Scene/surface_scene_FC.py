from openalea.fractalysis.light.directLight import directionalInterception
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl


s=Scene(r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\Scene\as05c1.bgeom')
Viewer.display(s)

scene_F = Scene()
scene_C = Scene()
surf_s =[]
for shp in s:
    if str(shp.id)[0]=='1': # Fescue
        scene_F.add(shp.geometry)
    elif str(shp.id)[0]=='2': # Clover
        scene_C.add(shp.geometry)
    elif shp.id == 0: # Soil
         break
    else:
        print 'problem in id'

    surf_s.append(surface(shp))
print 'totale',sum(surf_s)

surf_F=[]
for shp in scene_F:
    surf_F.append(surface(shp))
print 'Fetuque',sum(surf_F)

surf_C=[]
for shp in scene_C:
    surf_C.append(surface(shp))
print 'Trefle',sum(surf_C)
