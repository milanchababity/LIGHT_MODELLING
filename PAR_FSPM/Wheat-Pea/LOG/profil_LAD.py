import os


def profil_LAD (log_list):

    for log in log_list :
        file_ext = os.path.basename(log)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension
        
        f=open(log,'r')
        flines = f.readlines()
        
        LAD=[]
        row=12
        while row != len(flines):
            LAD.append(float(flines[row].split()[4]))
            row+=3
        
        trmt = file_base[:4]
        date = file_base[5:10]
        species = file_base[len(file_base)-1]
        
        if trmt == '