library(devtools)

context('testing fail')

test_that('ds.fail', {
  expect_equal(
    'brick',
    'wire'
  )
})

