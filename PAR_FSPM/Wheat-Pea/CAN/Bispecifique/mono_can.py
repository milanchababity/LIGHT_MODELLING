import re
import os
from os.path import join
import sys
import glob


path1 = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Wheat-Pea\CAN\Wheat'
path2 = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Wheat-Pea\CAN\Pea'

def mono_can (directory):
    file_dir = directory + '\\*.can'
    can_list = glob.glob (file_dir) # Lists all can file in the directory
    
    for can_file in can_list:
        f=open(can_file,'r')
        flines = f.readlines()
        f.close()

        file_ext = os.path.basename(can_file)
        o1=open(join(path1,file_ext),'w')
        o2=open(join(path2,file_ext),'w')
        label2={}
        for l in range(len(flines)):
            if flines[l].split()[2][0] == '2':
                label2[l]=(str(1) + flines[l].split()[2][1:])
            else:
                o1.write(str(flines[l]))
        
        flines2=[]
        row = 0
        while flines[row].split()[2][0] == '1':
            row+=1
        for i in range (row,len(flines)):
            flines2.append(flines[i][0:4] + str(label2[i]) + flines[i][16:])
        
        for l in range(len(flines2)):
            o2.write(str(flines2[l]))
    
    o1.close()
    o2.close()

if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = mono_can(sys.argv[1])