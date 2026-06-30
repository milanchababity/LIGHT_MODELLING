import re
import os
from os.path import join
import sys
import glob


path1 = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\CAN\Fescue'
path2 = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\CAN\Clover'

def mono_can_FC (directory):
    file_dir = directory + '\\*.can'
    can_list = glob.glob (file_dir) # Lists all can file in the directory
    
    for can_file in can_list:
        print can_file
        f=open(can_file,'r')
        flines = f.readlines()
        f.close()

        file_ext = os.path.basename(can_file)
        o1=open(join(path1,file_ext),'w')
        o2=open(join(path2,file_ext),'w')
        for l in range(len(flines)):
            if flines[l].split()[2][0] == '1':
                o1.write(flines[l][0:4] + '111111111111 ' + flines[l][17:])
            else:
                o2.write(flines[l][0:4] + '111111111111 ' + flines[l][17:])
    
    o1.close()
    o2.close()

if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = mono_can_FC(sys.argv[1])