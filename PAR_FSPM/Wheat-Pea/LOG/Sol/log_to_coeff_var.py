import glob,os,sys
from os.path import join
import xlwt
import numpy

path_FA = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Alfalfa\LOG'
path_FC = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Fescue-Clover\LOG'
path_WP = r'C:\Documents and Settings\r.barillot\Mes documents\These\S2V\PAR_FSPM\Wheat-Pea\LOG'
    
def log_to_coeff_var (dir):
    
    mixture = dir.split('\\')[-3]
    file_dir = dir + '\\*.log'
    log_list = glob.glob (file_dir) # Lists all scene file in the directory

    # open excel file
    xls_file = xlwt.Workbook() 
 
    for log in log_list:
        print log
        dictG={}
        dictL={}
        
        file_ext = os.path.basename(log)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension

        # ouverture du fichier log sol
        fich_log = open(log,'r')
        for i in range(20):
            fline= fich_log.readline() # passe les 20 premiers lignes
        ls=[]
        while fline!='\n':
            ls.append(map(float,fline.split())[1])
            fline= fich_log.readline()
        ls.sort()
        ls_ori =ls[0]
        ls_end = ls[-1]
        nbs = len(ls)
        fich_log.close()
        
        # Ouverture log grass
        if mixture == 'Fescue-Alfalfa':
            path = path_FA + '\Profils_Horizontaux_F'
        elif mixture == 'Fescue-Clover':
            path = path_FC + '\Profils_Horizontaux_F'
        elif mixture == 'Wheat-Pea':
            path = path_WP + '\Profils_Horizontaux_W'    
        
        fich_logG = open(join(path,file_base+'.log'),'r')
        for i in range(20):
            fline= fich_logG.readline() # passe les 20 premiers lignes

        lg={}
        #list couches
        while fline!='\n':
            spl=map(float,fline.split())
            lg[spl[1]]=spl[4]
            fline= fich_logG.readline()
        fich_logG.close()

        l_min = min(ls_ori,min(lg.keys()))
        l_max = max(ls_end,max(lg.keys()))

        for k in range(ls_ori,ls_end+1):
            if lg.has_key(k)==False:
                lg[k]= 0

        for l in lg.keys() :
            if l<ls_ori:
                if dictG.has_key(l+nbs):
                    dictG[l + nbs].append(lg[l])
                else:
                    dictG[l + nbs] = []
                    dictG[l + nbs].append(lg[l])

            elif ls_ori <= l <= ls_end:
                keys = dictG.keys()
                keys.sort()
                if dictG.has_key(l):
                    dictG[l].append(lg[l])
                else:
                    dictG[l]= []
                    dictG[l].append(lg[l])

            else:
                if dictG.has_key(l - nbs):
                    dictG[l - nbs].append(lg[l])
                else:
                    dictG[l - nbs]= []
                    dictG[l - nbs].append(lg[l])

        for k in dictG.keys():
            dictG[k]=sum(dictG[k])
  
        # Ouverture log legume
        if mixture == 'Fescue-Alfalfa':
            path = path_FA + '\Profils_Horizontaux_A'
        elif mixture == 'Fescue-Clover':
            path = path_FC + '\Profils_Horizontaux_C'
        elif mixture == 'Wheat-Pea':
            path = path_WP + '\Profils_Horizontaux_P'    
        
        fich_logF = open(join(path,file_base+'.log'),'r')
        for i in range(20):
            fline= fich_logF.readline() # passe les 20 premiers lignes

        ll={}
        #list couches
        while fline!='\n':
            spl=map(float,fline.split())
            ll[spl[1]]=spl[4]
            fline= fich_logF.readline()
        fich_logF.close()

        l_min = min(ls_ori,min(ll.keys()))
        l_max = max(ls_end,max(ll.keys()))
        #print l_min,l_max
        for k in range(ls_ori,ls_end+1):
            if ll.has_key(k)==False:
                ll[k]=0

        for l in ll.keys():
            if l<ls_ori:
                if dictL.has_key(l + nbs):
                    dictL[l + nbs].append(ll[l])
                else:
                    dictL[l + nbs] = []
                    dictL[l + nbs].append(ll[l])

            elif ls_ori <= l <= ls_end:
                keys = dictL.keys()
                keys.sort()
                if dictL.has_key(l):
                    dictL[l].append(ll[l])
                else:
                    dictL[l]= []
                    dictL[l].append(ll[l])

            else:
                if dictL.has_key(l - nbs):
                    dictL[l - nbs].append(ll[l])
                else:
                    dictL[l - nbs]= []
                    dictL[l - nbs].append(ll[l])

        for k in dictL.keys():
            dictL[k]=sum(dictL[k])

        # Open excel sheet
        xls_sheet = xls_file.add_sheet(file_base)
        xls_sheet.write(5,1,'Layer')
        xls_sheet.write(5,2,'LAD Grass')
        xls_sheet.write(5,3,'LAD Legume')
        xls_sheet.write(5,4,'LAD Canopy')
        row=6
        dict_canopy={}
        for l in range (ls_ori,ls_end+1):
            xls_sheet.write(row,1,l)
            xls_sheet.write(row,2,dictG[float(l)])
            xls_sheet.write(row,3,dictL[float(l)])
            dict_canopy[l]=dictG[float(l)]+dictL[float(l)]
            xls_sheet.write(row,4,dict_canopy[float(l)])
            row+=1
        
        xls_sheet.write(row,2,numpy.std(dictG.values())/numpy.average(dictG.values()))
        xls_sheet.write(row,3,numpy.std(dictL.values())/numpy.average(dictL.values()))
        xls_sheet.write(row,4,numpy.std(dict_canopy.values())/numpy.average(dict_canopy.values()))


    xls_file.save(mixture + '.xls')
         
