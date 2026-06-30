from openalea.fractalysis.light.directLight import directionalInterception
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl


s=Scene(r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Wheat-Pea\Scene\T1-1-080310.bgeom')
Viewer.display(s)

scene_W = Scene()
scene_P = Scene()
surf_s =[]
for shp in s:
    if shp.name[-1] == 'W':
        scene_W.add(shp.geometry)
    elif shp.name[-1] == 'P':
        scene_P.add(shp.geometry)
    else:
        pass
    surf_s.append(surface(shp))
print 'totale',sum(surf_s)

surf_W=[]
for shp in scene_W:
    surf_W.append(surface(shp))
print 'Ble :',sum(surf_W)

surf_P=[]
for shp in scene_P:
    surf_P.append(surface(shp))
print 'Pois :',sum(surf_P)
