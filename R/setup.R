library(devtools)
library(testthat)

# helper functions
source('R/ds_expect_variables.R')

# setup the DataSHIELD connection and test env
context('setup connection')

library(DSOpal)
library(dsBaseClient)

# login dataframe
# to be moved to passed args at some point
servers <- c('dsloadtest_1')
urls <- c('http://192.168.56.100:8080')

user <- 'administrator'
password <- 'datashield_test&'

# as an example, use login data for CNSIM
# currently as per tutorial that we're trying to replicate
# to be moved to passed args/config
table <- c('CNSIM.CNSIM1')

# setup the test env
ds.test_env <- new.env()

ds.test_env$login.data <- data.frame(servers, urls, user, password, table)

# stats.var lists the vars we want assigned
# default to getting everything
ds.test_env$stats.var <- c("DIS_AMI", "DIS_CVA", "DIS_DIAB", "GENDER", "LAB_GLUC_ADJUSTED", "LAB_HDL", "LAB_TRIG", "LAB_TSC", "MEDI_LPD", "PM_BMI_CATEGORICAL", "PM_BMI_CONTINUOUS")

# create the connection
ds.test_env$connections <- datashield.login(logins=ds.test_env$login.data, assign = TRUE)

# set the default env to ds.test env
# meaning we don't have to specify the connections every time we call 
# a ds function
options(datashield.env=ds.test_env)

context('setup complete')
