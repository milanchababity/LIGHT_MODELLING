import sys
import glob,os
import xlwt

row_size={'T3-1-180210_1': [40.820555572302112,34], 'T3-1-120310_1': [44.361878805069807,34],
              'T2-2-300310_1': [34.125359544809193,34], 'T1-2-290310_1': [31.216700680707579,34],
              'T1-2-160210_1': [37.965386425087921,34], 'T3-1-310310_1': [41.875310863530977,34],
              'T2-2-170210_1': [35.200085071807706,34], 'T4-2-010410_1': [28.264705088130821,34],
              'T2-1-090310_1': [34.658443776372877,34], 'T4-2-180210_1': [32.878316902086844,34],
              'T4-1-010410_1': [29.560063521107338,34], 'T1-1-170210_1': [40.822092082022515,34],
              'T1-1-080310_1': [40.177029448585415,34], 'T3-2-170210_1': [42.138351117685595,34],
              'T3-2-310310_1': [39.023610709628528,34], 'T2-2-090310_1': [34.905111597372098,34],
              'T3-2-090310_1': [21.185634303141509,34], 'T4-2-100310_1': [28.524393525542308,34],
              'T1-1-290310_1': [40.062163771014973,34], 'T4-1-110310_1': [31.245557965284981,34],
              'T1-2-080310_1': [42.209317064586848,34], 'T2-1-170210_1': [34.119831201956437,34],
              'T4-1-180210_1': [29.045847372503644,34], 'T2-1-300310_1': [34.189062807058633,34],
              'LD1-asso-luz_1':[106,34],'LD2-asso-luz_1':[106,34],'HD1-asso-luz_1':[30,31],'HD2-asso-luz_1':[30,31],
              'as5c1_1' : [17,10],'as5c2_1' : [17,10],'as5c3_1' : [17,10],'as2c1_1' : [17,10],'as2c2_1' : [17,10],
              'as2c3_1' : [17,10],'as2c4_1' : [17,10],'as3c1_1' : [17,10],'as3c2_1' : [17,10],'as3c3_1' : [17,10]}
def mixture_LAI(dir):
    file_dir = dir + '\\*.log'
    log_list = glob.glob (file_dir) # Lists all log file in the directory

    # Excel treatment
    xls_file = xlwt.Workbook() # open excel file
    xls_sheet = xls_file.add_sheet('LAI')# Open excel sheet
    xls_sheet.write(0,0,'File')
    xls_sheet.write(0,1,'LAI')
    
    r=1
    for log in log_list:
        file_ext = os.path.basename(log)
        file_base = file_ext[:file_ext.index('.')] # Gets filename without extension

        log = open(log,'r')
        log_lines = log.readlines()
        leaf_area = float(log_lines[11].split()[3].split('=')[1])
        LAI = leaf_area/(row_size[file_base][0]*row_size[file_base][1])
        xls_sheet.write(r,0,file_base)
        xls_sheet.write(r,1,LAI)
        r+=1
        
    xls_file.save(r'C:\Documents and Settings\r.barillot\Mes documents\These\Digit\Manip_digit_asso\Rayonnement\Papier_FSPM\LAI_mixture.xls')

if len(sys.argv) < 2:
   print __doc__
   sys.exit(0)
else:
   g = mixture_LAI(sys.argv[1])