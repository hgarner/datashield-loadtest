# install required libraries
library(devtools)
devtools::install_github('https://github.com/datashield/DSI')
devtools::install_github('https://github.com/datashield/DSOpal')
devtools::install_github('https://github.com/datashield/dsBaseClient', ref='v6.1')

# note sure why dsBase and DSLite need to be installed, but it 
# complains if not...
devtools::install_github('https://github.com/datashield/DSLite')
devtools::install_github('https://github.com/datashield/dsBase')
install_version("testthat", version = "2.3.2", repos = "http://cran.us.r-project.org")
