from openalea.plantgl.all import * 
from math import isnan
import glob,os,sys
from os.path import join

def scene_clean (dir):
    
    file_dir = dir + '\\*.bgeom'
    scene_list = glob.glob (file_dir) # Lists all scene file in the directory

    for scene in scene_list :
        file_ext = os.path.basename(scene)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension
        s_ori = Scene(scene)
        s = s_ori
        count = 0
        for shp in s:
            if shp.geometry.getName() != '100000000000': # Problem only occurs with Fescue which name is different from 100000000000
                pl = shp.geometry.geometry.geometry.geometry.pointList # list of all pointlist
                for vect in pl:
                    for coord in vect: 
                        if isnan(coord) == False : # tests if each coordinate equals to nan
                            test = True
                        else: # Value equals to nan
                            test = False
                            count +=1
                            break
                    if test == False:
                        break
                if test == False:
                    s.remove(shp) # Removes the entire shape from the scene
        
        file_out = file_base + '_2' + '.bgeom'
        
        if count >0 : # Checks whether or not the scene had been modified
            print 'Number of shape deleted : ' , count
            s.save(join(dir,file_out))
        else:
            pass
        
if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = scene_clean(sys.argv[1])