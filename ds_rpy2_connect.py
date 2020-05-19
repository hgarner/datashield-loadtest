from rpy2.robjects.packages import importr
importr('DSOpal')
importr('DSLite')
importr('opalr')
importr('dsBaseClient')
login_setup = robjects.r['''setupCNSIMTest''']
login_data = []
login_data = login_setup('dsBase')
dslogin = robjects.r['datashield.login']
conns = dslogin(login_data)
ds_ls = robjects.r['ds.ls']
ds_ls(datasources=conns)
robjects.r.ls()
robjects.r.ls()['CNSIM1']
importr('testthat')
from rpy2.robjects import r
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

