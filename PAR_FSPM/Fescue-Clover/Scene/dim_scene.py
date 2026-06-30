from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
import glob,os

def dim_scene (dir):
    
    file_dir = dir + '\\*.bgeom'
    scene_list = glob.glob (file_dir) # Lists all scene file in the directory

    for scene in scene_list :
        file_ext = os.path.basename(scene)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension

        s=Scene(str(scene))
        Viewer.display(s)
        trans_x = -pgl.BoundingBox(s).getXMin()+0.1
        trans_y = -pgl.BoundingBox(s).getYMin()+0.1
        print file_base,' : ', trans_x ,trans_y
