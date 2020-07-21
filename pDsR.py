import pexpect
from pexpect.exceptions import TIMEOUT
import sys
from queue import Queue, Empty, Full
from time import time
import re
from uuid import uuid4

class pDsR():

  # on instantiation, create a new r process and read queue
  def __init__(self, *args, **kwargs):
    self.r = pexpect.spawn('/usr/bin/R --vanilla')
    # output for debugging
    self.r.logfile = sys.stdout.buffer
    # todo above uses stderr - need nonblocking read on this
    # note that if we use stderr it seems to break the output of some ds commands (e.g. ds.dim)
    # turn off errors from r
    #self.send('options(error=expression(NULL))\n');
    self.request_stack = []
    # add a default timeout of 1/10000th of a second for
    # expecting output when reading the prompt
    self.r_prompt_timeout = 0.001
    self.r_prompt = '(.*)> $'
    self.r_error = 'Error(.*)'
    self.r_test_results = '''OK:\s+\\x1b\[(31m|32m|39m)(?P<ok_count>[0-9]+).*?(\\x1b[39m).*?\r\nFailed:\s+\\x1b\[(31m|32m|39m)(?P<failed_count>[0-9]+)'''
    self.r_test_results = '''OK:\s+\\x1b\[(31m|32m|39m)(?P<ok_count>[0-9]+).*?\r\nFailed:\s+\\x1b\[(31m|32m|39m)(?P<failed_count>[0-9]+)'''
    # default timeout for a request - how long do we wait to gather output?
    self.request_timeout = 5

  # del method to make sure we kill the r process and associated
  # read thread on gc
  def __del__(self):
    self.r.kill(3)

  # submit a 'request' (R commands)
  # and then call gather_output to get the results
  # @param string name name of request
  # @param string type type of request - either 'std' or 'test'

  # create a command buffer (list) here (or in pDsRRequest?)
  # for each command, submit and then check for match
  # with output, ignore the command sent (use re.escape to match)
  # note that if the command is still running, we won't see
  # the empty command prompt '> ' so use this?

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

    expectations = [self.r_test_results, self.r_error, self.r_prompt]
    # add the expectation to the list of matches for expect()
    # if present
    if expectation is not None:
      expectations.insert(0, expectation)

    if timeout is None:
      timeout = self.request_timeout

    start = time()
    while (time() - start) < timeout:
      # while we're still within the timeout,
      # expect a prompt
      # if nothing (TIMEOUT error), continue
      # otherwise add to the compiled output
      try:
        found_index = self.r.expect(expectations, timeout=self.r_prompt_timeout)
      except TIMEOUT:
        if self.status is None:
          self.status = 408
        elif self.status != 408 and self.status is not None:
          break
        continue

      # debugging - print current status
      print(f'self.status: {self.status}')
      print(f'found_index: {found_index}')

      # set look to 'before' to add data before match to output
      look = 'before'
      if found_index == 2:
        # found the r prompt
        # at what point should the status be set here?
        # the code passed may not yet have finished

        # check if the group has found anything
        # if so, a further command has been entered, so don't set
        # the status
        print(f'matched group 1 (prompt regex is /{self.r_prompt}/): {self.r.match.group(1)}')
        if self.r.match.group(1) == b'':
          print('matched group 1 is empty')
        else:
          print('matched group 1 has data')
        # found prompt, so use http status 100 (continue)
        if self.status is None or self.status == 408:
          self.status = 100
        elif self.status == 200 or self.status == 500:
          break
      elif found_index == 1:
        # found an error
        self.status = 500
        look = 'after'
      elif found_index == 0:
        # found test_results
        self.status = 200
        try:
          print(f'match for 200: {self.r.match.group(0)}')
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
      elif found_index == 3:
        # found provided expectation
        self.status = 200

      #line_output = getattr(self.r, look).decode('utf-8')
      line_before = self.r.before.decode('utf-8')
      line_after = self.r.after.decode('utf-8')
      line_output = f'{line_before}{line_after}'

      # add the line output to the compiled output
      if output is None:
        output = line_output
      else:
        output += line_output

    #print(f'output: {output}')
    print(f'status: {self.status}')
    print('..........')
    return output

class pDsRRequest:
  def __init__(self, pdsr_instance):
    self.status = None
    self.output = None
    self.result = {
      'ok': None,
      'failed': None
    }
    self.timeout = 10
    self.id = str(uuid4())
    self._command = None
    self.commands = []
    if not isinstance(pdsr_instance, pDsR):
      raise ValueError('error (pDsRRequest.__init__): pdsr_instance must be an instance of a pDsR object')
    else:
      self.pdsr = pdsr_instance
  
  def get(self, commands):
    if self.status is None:
      # self.status is None, so nothing yet sent
  
      ###
      # setup and id
      ###

      # send the request id and check if it appears
      # on the output. this is a crude method of ensuring that 
      # we have a responsive console and to remove left-over output from
      # previous commands
      self.pdsr.r.sendline(f'#{self.id}#')
      # store the current request_timeout
      tmp_timeout = self.pdsr.request_timeout
      self.pdsr.timeout = 0.1
      output = str(self.pdsr.gather_output())
      # if the current status is none, this is the first command sent
      # check for self.id in the output and discard anything prior
      # to this as it is unread output from a previous command
      if output is not None:
        all_output = output.split(f'#{self.id}#')
        if len(all_output) < 2:
          # haven't found the id of this request, so
          # something has gone wrong
          raise ValueError(f'pDsRRequest.get error: unable to find id of this request ({self.id}) in R output')
        # found the id but need to remove any output printed before it
        self.output = all_output[-1]
      else:
        # no output at all so entirely unresponsive
        raise ValueError(f'pDsRRequest.get error: unable to raise reponse from R output')
      # set the request_timeout to the specified value for this request
      self.pdsr.request_timeout = self.timeout

      ###
      # send commands
      ###

      for command in commands:
        self._command = command
        self.pdsr.r.sendline(self._command)
        output = str(self.pdsr.gather_output())
        if output is not None:
          if self.output is not None:
            self.output += output
          else:
            self.output = output

        # if we end up with a timeout, stop everything by
        # sending Ctrl-c
        # and exit with timeout status
        if self.pdsr.status == 408:
          self.pdsr.r.send('\003')
          self.status = 408
          break
        elif self.pdsr.status == 200:
          self.status = self.pdsr.status
          self.result = self.pdsr.result
        else: 
          # if not a timeout, set the status of the request
          # to the pdsr instance's status
          # note that this will mean that the status from any command before
          # the last will be overridden

          # NOTE
          # perhaps it would be better to have self.outputs and status
          # as lists, then push results to these?
          self.status = self.pdsr.status

      # reset the request_timeout
      self.pdsr.request_timeout = tmp_timeout

      return self
    else:
      raise RuntimeError('pDsRRequest.get: error, request has been resolved')



    
