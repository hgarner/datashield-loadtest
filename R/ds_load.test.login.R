library(waldo)
library(devtools)

source('R/setup.R')

context('testing login')

#compare(
#  'D',
#   ds.ls()[[servers]]$objects.found
#)

test_that('ds.ls', {
  for (server in servers) {
    expect_equal(
      'E',
      ds.ls()[[server]]$objects.found
    )
  }
})

