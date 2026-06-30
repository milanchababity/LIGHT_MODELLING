#from openalea.fractalysis.light.directLight import directionalInterception
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl

s=Scene(r'C:\Users\mbabity\Documents\PlantGL\scene_alfafa_HD1.bgeom')
Viewer.display(s)

scene_F = Scene()
scene_L = Scene()
surf_s =[]
for shp in s:
    if shp.geometry.getName() == '100000000000':
        scene_L.add(shp.geometry)
    else:
        scene_F.add(shp.geometry)
    surf_s.append(surface(shp))
print ('totale',sum(surf_s))

surf_L=[]
for shp in scene_L:
    surf_L.append(surface(shp))
print ('Luzerne',sum(surf_L))

surf_F=[]
for shp in scene_F:
    surf_F.append(surface(shp))
zmax = pgl.BoundingBox(scene_F).getZMax()
print (zmax)
print ('Fetuque',sum(surf_F))
