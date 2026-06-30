from openalea.fractalysis.light.directLight import directionalInterception
from openalea.plantgl.all import *
import openalea.plantgl.all as pgl
import xlwt
import glob,os,sys
from os.path import join


row_size={'T3-1-180210': 40.820555572302112, 'T3-1-120310': 44.361878805069807,
              'T2-2-300310': 34.125359544809193, 'T1-2-290310': 31.216700680707579,
              'T1-2-160210': 37.965386425087921, 'T3-1-310310': 41.875310863530977,
              'T2-2-170210': 35.200085071807706, 'T4-2-010410': 28.264705088130821,
              'T2-1-090310': 34.658443776372877, 'T4-2-180210': 32.878316902086844,
              'T4-1-010410': 29.560063521107338, 'T1-1-170210': 40.822092082022515,
              'T1-1-080310': 40.177029448585415, 'T3-2-170210': 42.138351117685595,
              'T3-2-310310': 39.023610709628528, 'T2-2-090310': 34.905111597372098,
              'T3-2-090310': 21.185634303141509, 'T4-2-100310': 28.524393525542308,
              'T1-1-290310': 40.062163771014973, 'T4-1-110310': 31.245557965284981,
              'T1-2-080310': 42.209317064586848, 'T2-1-170210': 34.119831201956437,
              'T4-1-180210': 29.045847372503644, 'T2-1-300310': 34.189062807058633}
inter_row = 34.

def scene2seperate_species (dir):
    
    file_dir = dir + '\\*.bgeom'
    scene_list = glob.glob (file_dir) # Lists all scene file in the directory

    # Excel treatment
    xls_file = xlwt.Workbook() # open excel file
    xls_sheet = xls_file.add_sheet('Canopies paramaters')# Open excel sheet
    xls_sheet.write(5,1,'Treatment')
    xls_sheet.write(5,2,'LAI Cereal')
    xls_sheet.write(5,3,'LAI Legume')
    xls_sheet.write(5,4,'Height ratio (cereal/legume)')
    
    row= 6
    for scene in scene_list :
        file_ext = os.path.basename(scene)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension

        s=Scene(str(scene))
        Viewer.display(s)

        scene_C = Scene()
        scene_L = Scene()
        for shp in s:
            if shp.getName()[-1]=='W': #Selects shape element from wheat
                scene_C.add(shp.geometry)
            elif shp.getName()[-1]=='P': #Selects shape element from pea
                scene_L.add(shp.geometry)
            else:
                print 'not a species', shp.getName()
        surf_s = pgl.surface(s)
        surf_C= pgl.surface(scene_C)
        height_C = pgl.BoundingBox(scene_C).getZMax()-pgl.BoundingBox(scene_C).getZMin()
        surf_L= pgl.surface(scene_L)
        height_L = pgl.BoundingBox(scene_L).getZMax()-pgl.BoundingBox(scene_L).getZMin()
        
        xls_sheet.write(row,1,file_base)
        xls_sheet.write(row,2,float(surf_C / (row_size[file_base]*inter_row)))
        xls_sheet.write(row,3,float(surf_L / (row_size[file_base]*inter_row)))
        xls_sheet.write(row,4,float(height_C / height_L))
        row += 1
    xls_file.save(join(dir, 'canopy_parameter_WP.xls'))
    
if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = scene2seperate_species(sys.argv[1])