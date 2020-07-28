from pDsR import pDsR
dsr = pDsR()

from pDsR import pDsR, pDsRRequest
dsr = pDsR()
req = pDsRRequest(dsr)

# test an example 'ok'
commands_4 = [
	'library("devtools")',
	'library("testthat")',
	'test_file("test_example_ok.R")'
]

req_4 = pDsRRequest(dsr)
req_4.get(commands_4)

commands_5 = [
	'test_file("test_example_ok.R")'
]

req_5 = pDsRRequest(dsr)
req_5.get(commands_5)

commands = ['ls()']
req.get(commands)

commands_1 = ['Sys.sleep(20)']
commands_2 = ['ls()']
req_1 = pDsRRequest(dsr)
req_2 = pDsRRequest(dsr)

# req_1 should timeout and shouldn't cause an issue with
# req_2 (i.e. it should send Ctrl-c and have a 408 status, req_2 should be able to read its id from the R output)
req_1.get(commands_1)
req_2.get(commands_2)

# test multiple commands
commands_3 = [
  'ls()',
  'a <- c(1, 2, 3, 5, 7, 11, 13)',
  'print(a)'
]

req_3 = pDsRRequest(dsr)
req_3.get(commands_3)

# test an example 'ok'
commands_4 = [
  'library("devtools")',
  'library("testthat")',
  'test_file("test_example_ok.R")'
]

req_4 = pDsRRequest(dsr)
req_4.get(commands_4)

# note that returns a 100 status if repeated
# test is successful but match isn't working for some reason

# test an example with datashield

r_login = '''source('R/setup.R')'''

r_test_ls = '''test_file('ds_load.test.ls.R')'''

r_logout = '''source('R/teardown.R')'''

commands_5 = [
  r_login,
  r_test_ls,
  r_logout
]

req_5 = pDsRRequest(dsr)
req_5.get(commands_5)
