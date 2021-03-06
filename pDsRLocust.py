import time

from locust import User, TaskSet, events, task, between

import sys

from pDsR import pDsR, pDsRRequest

import pexpect

from functools import partial

# implement a simple client that runs an R script
# gets the result and fires locust events on success/failure

class pDsRClient(pDsR):
  _locust_environment = None
  
  # generate a new request object with the locust_environment set
  def request(self, *args, **kwargs):
    request = pDsRClientRequest(locust_environment = self._locust_environment, pdsr_instance = self, *args, **kwargs)
    return request

class pDsRClientRequest(pDsRRequest):
  _locust_environment = None

  def __init__(self, locust_environment, *args, **kwargs):
    self._locust_environment = locust_environment
    super(pDsRClientRequest, self).__init__(*args, **kwargs)

  def get(self, *args, **kwargs):
    start_time = time.time()
    try:
      result = super(pDsRClientRequest, self).get(*args, **kwargs)
    except Exception as e: 
      total_time = int((time.time() - start_time) * 1000)
      events.request_failure.fire(request_type='pDsRRequest', name='get', response_time=total_time, exception=e, response_length=len(repr(e).encode('utf-8')))
      raise e
    else:
      total_time = int((time.time() - start_time) * 1000)
      if self.status == 200:
        # successfully got test results
        # check if any failed tests - if so, error
        if self.result['failed'] != 0:
          events.request_failure.fire(request_type='pDsRRequest', name='get', response_time=total_time, exception=Exception(f"ran tests but {self.result['failed']} tests failed"), response_length=0)
        elif self.result['ok'] > 0:
          events.request_success.fire(request_type='pDsRRequest', name='get', response_time=total_time, response_length=0)
        else:
          # no failed or ok
          # so throw exception
          # will cause issues on skipped
          events.request_failure.fire(request_type='pDsRRequest', name='get', response_time=total_time, exception=Exception('ran tests but no ok/failed results'), response_length=0)
      elif self.status == 100:
        # successfully got any non-error output
        events.request_success.fire(request_type='pDsRRequest', name='get', response_time=total_time, response_length=0)
      elif self.status == 500:
        # error output
        events.request_failure.fire(request_type='pDsRRequest', name='get', response_time=total_time, exception=Exception(result), response_length=0)
      elif self.status == 408:
        # timeout
        events.request_failure.fire(request_type='pDsRRequest', name='get', response_time=total_time, exception=Exception('timeout'), response_length=0)
      # note response_length hardcoded to 0 here, need to hook in at lower lvl
    return result

# extend the Locust User class to add an instance of pDsR
class DsRLocust(User):
  # abstract tells Locust not to create users directly from
  # this class, only from classes derived from it
  abstract = True
  def __init__(self, *args, **kwargs):
    super(DsRLocust, self).__init__(*args, **kwargs)
    self.dsr = pDsRClient()
    self.dsr._locust_environment = self.environment

# extend the default TaskSet to add a run_task method
# this is called from each task with the task_name and 
# list of commands to be run
class DsUserTaskSet(TaskSet):
  # run a task (list of R commands) with specified task_name
  # calls the pDsRClient instance's request() method
  # return the output of the request
  def run_task(self, task_name, commands, debug = True):
    if debug:
      print(f'*** running task: {task_name} ***')
    request = self.user.dsr.request(timeout = self.user.request_timeout)

    if not isinstance(commands, list):
      raise TypeError('DsUserTasks.run_task: error, commands must be a list')

    #commands.insert(0, 'list.files()')
    #commands.insert(0, 'setwd("/datashield-loadtest_parent")')
    try:
      request.get(commands)
    except Exception as e:
      print('DsUserTasks.run_task: Error (task {task_name}) on calling request.get()')
      raise e

    output = None
    try:
      output = request.output
      if output is None:
        raise Exception('DsUserTasks.run_task: Error, task {task_name} returning no output within {self.r_timeout} seconds')
    except Exception as e:
      print('DsUserTasks.run_task: Error (task {task_name}) on getting request output')

    return output

class DsUserTasks(DsUserTaskSet):
  @task(1)
  def ls(self):
    task_name = 'ls'
    commands = [
      'test_file("R/ds_load.test.ls.R")'
    ]

    output = self.run_task(task_name, commands)

    return output

  @task(1)
  # call a test which fails for debugging and testing locust
  def fail(self):
    task_name = 'fail'
    commands = [
      'test_file("R/ds_load.test.fail.R")'
    ]

    output = self.run_task(task_name, commands)

    return output

  #@task(1)
  # call a test which times out for debugging and testing locust
  def timeout(self):
    task_name = 'timeout'
    # this will just call Sys.sleep(10) in R
    commands = [
      'source("R/ds_load.test.timeout.R")'
    ]

    output = self.run_task(task_name, commands)

    return output

  #@task(1)
  def logout(self):
    task_name = 'logout'
    commands = [
      'source("R/teardown.R")',
    ]
    pass  

class DsUser(DsRLocust):
  taskset = DsUserTasks
  wait_time = between(5,15)
  tasks = {DsUserTasks:1}

  # setup is called before anything else, so do some setup
  # (login)
  def on_start(self):
    # set timeout when waiting for request output to 20 seconds
    self.request_timeout = 20
    # login
    self.login()

  def on_stop(self):
    self.logout()

  def logout(self):
    request = self.dsr.request(timeout = self.request_timeout)
    commands = [
      'source("R/teardown.R")',
    ]
    try:
      request.get(commands)
    except Exception as e:
      print('Error on sending logout command')
      raise e

    output = None
    try:
      output = request.output
      if output is None:
        raise Exception('DsUser.login: Error, login returning no output within {self.r_timeout} seconds')
    except Exception as e:
      print('DsUser.logout: Error on getting request output')

    return output

  def login(self):
    request = self.dsr.request(timeout = self.request_timeout)
    # up the timeout waiting for a reponse from R
    # as this often seems to fail here
    request.id_timeout = 5
    commands = [
      'source("R/setup.R")',
      'test_file("R/ds_load.test.ls.R")'
    ]
    try:
      request.get(commands)
    except Exception as e:
      print('Error on sending login data')
      raise e

    output = None
    try:
      output = request.output
      if output is None:
        raise Exception('DsUser.login: Error, login returning no output within {self.r_timeout} seconds')
    except Exception as e:
      print('DsUser.login: Error on getting request output')

    print(f'output: {output}')
    print(f'dsr request status: {request.status}')

    return output

