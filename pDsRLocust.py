import time

from locust import User, Locust, TaskSet, events, task, between

import sys

from pDsR import pDsR
import pexpect

# implement a simple client that runs an R script
# gets the result and fires locust events on success/failure
# what does it need to do?
# is something returned? (exit code)
# is it what we expect? compare against predefined result
# save some terminal output? 
#  ( use subprocess.run([cmds], stdout=subprocess.PIPE) )
# what about killing the script if timeout exceeded?
# OR
# do it using rpy2
# take the script line by line
# reformat this to pass through rpy2
# exec and return result
# OR
# pass /single/ command to be run by rpy2
# AND/OR
# define a set of methods here to e.g.
#   - connect
#   - exit
#   - run ds command
# so a task set might be:
#   - connect()
#   - random command from list of commands
#   - * n.b. commands could be tagged to allow grouping
#   - repeat n times
#   - exit()

class pDsRClient(pDsR):
  _locust_environment = None

  def gather_output(self, *args, **kwargs):
    start_time = time.time()
    try:
      result = super(pDsRClient, self).gather_output(*args, **kwargs)
    except Exception as e: 
      total_time = int((time.time() - start_time) * 1000)
      events.request_failure.fire(request_type='pdsr', name='gather_output', response_time=total_time, exception=e)
      raise e
    else:
      print(result)
      total_time = int((time.time() - start_time) * 1000)
      if self.status == 200:
        # successfully got test results
        # check if any failed tests - if so, error
        if self.result['failed'] != 0:
          events.request_failure.fire(request_type='pdsr', name='gather_output', response_time=total_time, exception=Exception(f"ran tests but {self.result['failed']} tests failed"))
        elif self.result['ok'] > 0:
          events.request_success.fire(request_type='pdsr', name='gather_output', response_time=total_time, response_length=0)
        else:
          # no failed or ok
          # so throw exception
          # will cause issues on skipped
          events.request_failure.fire(request_type='pdsr', name='gather_output', response_time=total_time, exception=Exception('ran tests but no ok/failed results'))
      elif self.status == 100:
        # successfully got any non-error output
        events.request_success.fire(request_type='pdsr', name='gather_output', response_time=total_time, response_length=0)
      elif self.status == 500:
        # error output
        events.request_failure.fire(request_type='pdsr', name='gather_output', response_time=total_time, exception=Exception(result))
      elif self.status == 408:
        # timeout
        events.request_failure.fire(request_type='pdsr', name='gather_output', response_time=total_time, exception=Exception('timeout'))
      # note response_length hardcoded to 0 here, need to hook in at lower lvl
    return result

  def getattr(self, name):
    func = pDsR.__get_attr__(self, name)
    def wrapper(*args, **kwargs):
      start_time = time.time()
      try:
        result = func(*args, **kwargs)
      except Exception as e: 
        total_time = int((time.time() - start_time) * 1000)
        events.request_failure.fire(request_type='pdsr', name=name, response_time=total_time, exception=e)
        raise e
      else:
        print(result)
        total_time = int((time.time() - start_time) * 1000)
        if self.status == 200:
          # successfully got test results
          # check if any failed tests - if so, error
          if self.result['failed'] != 0:
            events.request_failure.fire(request_type='pdsr', name=name, response_time=total_time, exception=Exception(f"ran tests but {self.result['failed']} tests failed"))
          elif self.result['ok'] > 0:
            events.request_success.fire(request_type='pdsr', name=name, response_time=total_time, response_length=0)
          else:
            # no failed or ok
            # so throw exception
            # will cause issues on skipped
            events.request_failure.fire(request_type='pdsr', name=name, response_time=total_time, exception=Exception('ran tests but no ok/failed results'))
        elif self.status == 100:
          # successfully got any non-error output
          events.request_success.fire(request_type='pdsr', name=name, response_time=total_time, response_length=0)
        elif self.status == 500:
          # error output
          events.request_failure.fire(request_type='pdsr', name=name, response_time=total_time, exception=Exception(result))
        elif self.status == 408:
          # timeout
          events.request_failure.fire(request_type='pdsr', name=name, response_time=total_time, exception=Exception('timeout'))
        # note response_length hardcoded to 0 here, need to hook in at lower lvl
      return result
    return wrapper

# extend the Locust User class to add an instance of pDsR
class DsRLocust(User):
  # abstract tells Locust not to create users directly from
  # this class, only from classes derived from it
  abstract = True
  def __init__(self, *args, **kwargs):
    super(DsRLocust, self).__init__(*args, **kwargs)
    self.dsr = pDsRClient()
    self.dsr._locust_environment = self.environment

class DsUserTasks(TaskSet):
  @task(1)
  def ls(self):
    command = '''
    test_file('ds_load.test.ls.R')
    '''    
    try:
      self.user.dsr.r.send(command)
    except Exception as e:
      print('DsUser.dim: Error on sending command')
      raise e

    output = None
    try:
      output = self.user.dsr.gather_output()
      if output is None:
        raise Exception('DsUser.dim: Error, dim returning no output within {self.r_timeout} seconds')
    except Exception as e:
      print(f'DsUserTasks.ls: Error on calling gather_output ({e})')

    return output

  #@task(1)
  def logout(self):
    command = '''
    source('R/teardown.R')
    '''
    pass  

class DsUser(DsRLocust):
  taskset = DsUserTasks
  wait_time = between(5,15)
  tasks = {DsUserTasks:1}
  # setup is called before anything else, so do some setup
  # (login)
  def on_start(self):
    # set timeout when waiting for r output to 5 seconds
    self.dsr.r.r_timeout = 5
    # login
    self.login()

  def login(self):
    try:
      self.dsr.r.send(
        '''
        source('R/setup.R')
        source('ds_load.test.ls.R')
        '''
      )
    except Exception as e:
      print('Error on sending login data')
      raise e

    output = None
    try:
      output = self.dsr.gather_output()
      if output is None:
        raise Exception('DsUser.login: Error, login returning no output within {self.r_timeout} seconds')
    except Exception as e:
      print('DsUser.login: Error on calling expect_output')

    print(f'output: {output}')
    print(f'dsr status: {self.dsr.status}')

    return output

