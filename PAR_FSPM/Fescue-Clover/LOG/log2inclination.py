import re
import xlwt
from os.path import join
import os
import sys
import glob

path = r'C:\Documents and Settings\r.barillot\Mes documents\These\Digit\Manip_digit_asso\Rayonnement'

def log2inclination (directory):
    centre_classes = [5,15,25,35,45,55,65,75,85]
    # Excel treatment
    xls_file = xlwt.Workbook() # open excel file
    xls_sheet = xls_file.add_sheet('inclination')# Open excel sheet
    xls_sheet.write(0,0,'Species 1 = Cereal / Species 2 = Legume')
    xls_sheet.write(5,1,'Treatment')
    xls_sheet.write(5,2,'Species')
    xls_sheet.write(5,3,'Height')
    xls_sheet.write(5,4,'Mean inclination')

    file_dir = directory + '\\*.log'
    log_list = glob.glob (file_dir) # Lists all log file in the directory
    
    r=6
    for log in log_list:
        file_ext = os.path.basename(log)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension
        f=open(log,'r')
        f_lines = f.readlines()
        f.close()
        assert f_lines[13] == ' STATISTIQUES PAR CELLULE\n'

        l=15
        while l < len(f_lines)-1:
            if f_lines[l].split()[3] == '1':
                __tmp_mean_incl_1 = []
                __tmp_mean_incl_1.append([f_lines[l+1].split()[i] for i in range(0,len(f_lines[l+1].split()))]) # Appends inclination distribution in each class
                mean_incl_1 = 0
                # Computes mean inclination
                for j in range(len(centre_classes)):
                    mean_incl_1 += float(__tmp_mean_incl_1[0][j]) * centre_classes[j]
                # Writes results
                xls_sheet.write(r,1,file_base)
                xls_sheet.write(r,2,1)
                xls_sheet.write(r,3,int(f_lines[l].split()[2]))
                xls_sheet.write(r,4,mean_incl_1)
                l+=3
                r+=1
                
            elif f_lines[l].split()[3] == '2':
                __tmp_mean_incl_2 = []
                __tmp_mean_incl_2.append([f_lines[l+1].split()[i] for i in range(0,len(f_lines[l+1].split()))]) # Appends inclination distribution in each class
                mean_incl_2 = 0
                # Computes mean inclination
                for j in range(len(centre_classes)):
                    mean_incl_2 += float(__tmp_mean_incl_2[0][j]) * centre_classes[j]
                # Writes results
                xls_sheet.write(r,1,file_base)
                xls_sheet.write(r,2,2)
                xls_sheet.write(r,3,int(f_lines[l].split()[2]))
                xls_sheet.write(r,4,mean_incl_2)
                l+=3
                r+=1
            else :
                print 'error in species id'
                break
        r+=1
    xls_file.save(join(path, 'profil_inclination.xls'))

if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = log2inclination(sys.argv[1])