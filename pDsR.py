import pexpect
from pexpect.exceptions import TIMEOUT
import sys
from queue import Queue, Empty, Full
from time import time
import re

class pDsR():

  # on instantiation, create a new r process and read queue
  def __init__(self, *args, **kwargs):
    self.r = pexpect.spawn('/usr/bin/R --vanilla')
    # todo above uses stderr - need nonblocking read on this
    # note that if we use stderr it seems to break the output of some ds commands (e.g. ds.dim)
    # turn off errors from r
    #self.send('options(error=expression(NULL))\n');
    self.request_stack = []
    # add a default timeout of 1/10000th of a second for
    # expecting output when reading the prompt
    self.r_prompt_timeout = 0.001
    self.r_prompt = '> (.*)'
    self.r_error = 'Error(.*)'
    self.r_test_results = '''OK:\s+\\x1b\[(31m|32m|39m)(?P<ok_count>[0-9]+).*?\r\nFailed:\s+\\x1b\[(31m|32m|39m)(?P<failed_count>[0-9]+)'''
    # default timeout for a request - how long do we wait to gather output?
    self.request_timeout = 5

  # del method to make sure we kill the r process and associated
  # read thread on gc
  def __del__(self):
    self.r.kill(3)

  # get all the output avalable within timeout
  # needs an expectation to break on
  # possibly add mutliple expectation streams for errors etc?
  # which then output to a tuple?
  def gather_output(self, expectation = None, timeout = None):
    output = None
    self.status = None
    self.result = {
      'ok': None,
      'failed': None
    }
    line_output = None
    self.r.timeout = self.r_prompt_timeout
    if timeout is None:
      timeout = self.request_timeout
    start = time()
    while (time() - start) < timeout:
      # while we're still within the timeout,
      # expect a prompt
      # if nothing (TIMEOUT error), continue
      # otherwise add to the compiled output
      try:
        found_index = self.r.expect([self.r_prompt, self.r_error, self.r_test_results], timeout=self.r_prompt_timeout)
      except TIMEOUT:
        if self.status is None:
          self.status = 408
        elif self.status != 408 and self.status is not None and expectation is None:
          break
        continue

      # debugging - print current status
      print(f'self.status: {self.status}')

      # set look to 'before' to add data before match to output
      look = 'before'
      if found_index == 0:
        # found the r prompt
        # at what point should the status be set here?
        # the code passed may not yet have finished

        # check if the group has found anything
        # if so, a further command has been entered, so don't set
        # the status
        print(f'matched group 1 after prompt: {self.r.match.group(1)}')
        if self.r.match.group(1) == b'':
          print('matched group 1 is empty')
        else:
          print('matched group 1 has data')
        # found prompt, so use http status 100 (continue)
        if self.status is None:
          self.status = 100
        elif self.status == 200 or self.status == 500:
          break
      elif found_index == 1:
        # found an error
        self.status = 500
        look = 'after'
      elif found_index == 2:
        # found test_results
        self.status = 200
        try:
          self.result = {
            'ok': int(self.r.match.group('ok_count')),
            'failed': int(self.r.match.group('failed_count'))
          } 
        except ValueError:
          raise ValueError('pDsR.gather_output: error parsing test counts')
        except IndexError:
          raise IndexError('pDsR.gather_output: error in matched group when parsing test counts')
        except Exception as e:
          raise e
        # what to do now? should we still wait for more output?
        # probably not, so why bother gathering more?

      #line_output = getattr(self.r, look).decode('utf-8')
      line_before = self.r.before.decode('utf-8')
      line_after = self.r.after.decode('utf-8')
      line_output = f'{line_before}{line_after}'

      # add the line output to the compiled output
      if output is None:
        output = line_output
      else:
        output += line_output
      # see if anything now matches an expectation (if provided)
      if expectation is not None:
        expected_match = re.search(expectation, output)
        if expected_match is not None:
          print('found!')

    print(f'output: {output}')
    return output

class pDsRRequest:
  def __init__(self):
    self.status = None
    self.output = None
    self.timeout = 5
    
