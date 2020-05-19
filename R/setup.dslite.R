library(devtools)
library(testthat)
# setup the DataSHIELD connection and test env
context('setup connection')

# just use dslite for the moment as proof of concept
library(DSOpal)
library(DSLite)
library(dsBaseClient)

# setup the test env
ds.test_env <- new.env()

# as an example, use login data for CNSIM
ds.test_env$login.data <- DSLite::setupCNSIMTest('dsBase', env=ds.test_env)

# stats.var lists the vars we want assigned
# default to getting everything
ds.test_env$stats.var <- ls(ds.test_env$CNSIM1)

# create the connection
ds.test_env$connections <- datashield.login(logins=ds.test_env$login.data, assign=TRUE, variables=ds.test_env$stats.var)

# set the default env to ds.test env
# meaning we don't have to specify the connections every time we call 
# a ds function
options(datashield.env=ds.test_env)

context('setup complete')
