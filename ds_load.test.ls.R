library(waldo)
library(devtools)

context('testing login')

test_that('ds.ls', {
  for (server in servers) {
    expect_equal(
      'D',
      ds.ls()[[server]]$objects.found
    )
  }
})

