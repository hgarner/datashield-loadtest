# load required libraries
devtools::install_github('https://github.com/datashield/DSI')
devtools::install_github('https://github.com/datashield/DSOpal')
devtools::install_github('https://github.com/datashield/dsBaseClient', ref='v6.1')

library(DSOpal)
library(dsBaseClient)

# login dataframe
# to be moved to passed args at some point
server <- c('dsloadtest_1')
url <- c('http://192.168.56.100:8080')

user <- 'administrator'
password <- 'datashield_test&'

# tables
# currently as per tutorial that we're trying to replicate 
# to be moved to passed args/config
table <- c('CNSIM.CNSIM1')

ds.test_env <- new.env()

ds.test_env$login.data <- data.frame(server, url, user, password, table)

ds.test_env$stats.var <- c("DIS_AMI", "DIS_CVA", "DIS_DIAB", "GENDER", "LAB_GLUC_ADJUSTED", "LAB_HDL", "LAB_TRIG", "LAB_TSC", "MEDI_LPD", "PM_BMI_CATEGORICAL", "PM_BMI_CONTINUOUS")

# login to opal servers
ds.test_env$connections <- datashield.login(logins=ds.test_env$login.data, assign = TRUE)

options(datashield.env=ds.test_env)

ds.dim(x='D')

# logout of opal servers
datashield.logout(opals)

{ 
  'server': ['dsloadtest_1'],
  'url': ['http://192.168.56.100:8080'],
  'user': ['administrator'],
  'password': ['datashield_test&'],
  'table': ['CNSIM.CNSIM1']
}

