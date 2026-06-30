from openalea.fractalysis.light.directLight import directionalInterception
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
import xlwt
import glob,os,sys
from os.path import join


row_size={'as05c1' : 17,'as05c2' : 17,'as05c3' : 17,'as2c1' : 17,'as2c2' : 17,
          'as2c3' : 17,'as2c4' : 17,'as3c1' : 17,'as3c2' : 17,'as3c3' : 17}

inter_row = 10.

def scene2seperate_species(dir):

    file_dir = dir + '\\*.bgeom'
    scene_list = glob.glob(file_dir)

    # Excel
    xls_file = xlwt.Workbook()
    xls_sheet = xls_file.add_sheet('Canopies parameters')

    xls_sheet.write(5,1,'Treatment')
    xls_sheet.write(5,2,'LAI Cereal')
    xls_sheet.write(5,3,'LAI Legume')
    xls_sheet.write(5,4,'Height ratio (cereal/legume)')

    row = 6

    for scene in scene_list:

        file_ext = os.path.basename(scene)
        file_base = file_ext[:file_ext.index('.')]
        s = Scene(str(scene))
        # INITIALISATION SCENE
        scene_F = []
        scene_C = []
        # SCENE SEPARATION BETWEEN FESCUE AND CLOVER
        for shp in s:
            if str(shp.id).startswith('1'):      # Fescue
                scene_F.append(shp.geometry)

            elif str(shp.id).startswith('2'):    # Clover
                scene_C.append(shp.geometry)

            elif shp.id == 0:                    # Soil
                continue
            else:
                print("problem in id :", shp.id)
        # SCENE PLANTGL GENERATION 
        scene_fescue = Scene(scene_F)
        scene_clover = Scene(scene_C)
        # Cheking
        if len(scene_F) == 0 or len(scene_C) == 0:
            print("Empty scene :", file_base)
            continue
        # Surfaces
        surf_F = pgl.surface(scene_fescue)
        surf_C = pgl.surface(scene_clover)
        # Heigths
        bbox_F = pgl.BoundingBox(scene_fescue)
        bbox_C = pgl.BoundingBox(scene_clover)

        height_F = bbox_F.getZMax() - bbox_F.getZMin()
        height_C = bbox_C.getZMax() - bbox_C.getZMin()

        # LAI
        ground_area = row_size[file_base] * inter_row

        lai_F = surf_F / ground_area
        lai_C = surf_C / ground_area

        # Ratio Heights
        if height_F > 0:
            ratio = height_C / height_F
        else:
            ratio = 0

        print(file_base)
        print("surface Fescue :", surf_F)
        print("surface Clover :", surf_C)
        print("height Fescue :", height_F)
        print("height Clover :", height_C)

        # Excel
        xls_sheet.write(row,1,file_base)
        xls_sheet.write(row,2,lai_F)
        xls_sheet.write(row,3,lai_C)
        xls_sheet.write(row,4,ratio)

        row += 1

    # Sauvegarde une seule fois
    xls_file.save(join(dir, 'canopy_parameter_WP.xls'))
    
    
scene2seperate_species (r"PAR_FSPM\Fescue-Clover\Scene")


    