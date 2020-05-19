library(waldo)
library(devtools)

source('R/setup.R')

context('testing login')

#ds.dim(x='D')$'dimensions of D in combined studies'

#print("try forcing an error:")
#foo()

print('expect equal:')
compare(ds.dim(x='D')$'dimensions of D in combined studies', as.double(c(2163, 11)))
print('expect unequal:')
compare(ds.dim(x='D')$'dimensions of D in combined studies', as.double(c(2222, 11)))
print('expect error:')
compare(ds.dim(x='D')$'dimensions of D in combined studies', list(2222, 11))
###
test_that('dims', {
  expect_equal(
    ds.dim(x='D')$'dimensions of D in combined studies', 
    as.double(c(2163, 11))
  )
})
###

source('R/teardown.R')
