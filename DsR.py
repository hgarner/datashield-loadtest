from subprocess import Popen, PIPE
import sys
from threading import Thread, active_count, get_ident, Lock, Event
from queue import Queue, Empty, Full
from time import time

class DsR():

  # on instantiation, create a new r process and read queue
  def __init__(self, *args, **kwargs):
    #self.r = Popen(['/usr/bin/R --vanilla'], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    # todo above uses stderr - need nonblocking read on this
    # note that if we use stderr it seems to break the output of some ds commands (e.g. ds.dim)
    self.output = {}
    self.output_queue = {}
    #self.begin_output_queue('stdout', self.r.stdout)
    #self.begin_output_queue('stderr', self.r.stderr)
    # turn off errors from r
    #self.send('options(error=expression(NULL))\n');
    self.request_stack = []
    # add a default timeout of 1 second
    self.r_timeout = 1

  def begin(self):
    self.r = Popen(['/usr/bin/R --vanilla'], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

  # del method to make sure we kill the r process and associated
  # read thread on gc
  def __del__(self):
    self.r.kill()

  def expect_output(self, timeout = None):
    if timeout is None:
      timeout = self.r_timeout
    start = time()
    if ('queue' not in self.output_queue.keys()):
      self.begin_output_queue(streams = ['stdout', 'stderr'])
    output = None
    line_output = None
    prev_line_output = None
    while (time() - start) < timeout:
      line_output = self.read_output_queue()
      # store the previous line and if now set, break if it's the 
      # same as line output and we have data in output
      # i.e. we've got some lines and now have two empty lines,
      # so assuming done
      if prev_line_output is not None:
        if (line_output == prev_line_output) and (output is not None and output != ''):
          break
      prev_line_output = line_output
      if output is None:
        output = line_output
      else:
        output += line_output

    self.close_output_queues()
    return output

  # setup a queue for the output of the r process
  # need to open and close this when we send some input
  def begin_output_queue(self, streams):
    ON_POSIX = 'posix' in sys.builtin_module_names
    self.output_queue = {}
    self.output_queue['queue'] = Queue()

    # create listening event to allow thread to terminate
    halt = Event()
    self.output_queue['halt'] = halt

    # create thread that runs enqueue_output, continually adding
    # output from stdout onto the queue until listening event
    # is not set
    self.output_queue['threads'] = []
    for stream_name in streams:
      thread = Thread(name=f'output_{stream_name}_thread', target=self.enqueue_output, args=(halt, stream_name, self.output_queue['queue']))
      thread.daemon = True # make sure thread dies with the prog
      thread.start()
      self.output_queue['threads'].append(thread)

  # close any output queues and threads
  def close_output_queues(self):
    self.output_queue['halt'].set()
    # hacky solution as we need to send something to the streams
    # so they stop blocking
    self.send('write("", stderr())\nwrite("", stdout())\n')
    self.read_output_queue()
    for thread in self.output_queue['threads']:
      print(f'thread {thread} is alive: {thread.isAlive()}')
      #thread.join()

  # read everything that's been output by the r process
  # do timeout - use queue.get with wait
  # or poss get the thread to send a signal
  def read_output_queue(self):
    output = []
    # this is not ideal
    # probably better with asyncio
    while True:
      try:
        #output.append(self.output_queue['queue'].get_nowait())
        # apparently this needs a timeout when used in a subclass
        # fuck knows why. any less time than this and it just returns
        # empty
        output.append(self.output_queue['queue'].get(timeout=0.0001))
        print(f'output: {output}')
      except Empty:
        break
    return output

  # passed an output stream and queue, 
  # will read and put output onto queue
  def enqueue_output(self, halt, stream_name, queue):
    stream = getattr(self.r, stream_name)
    while True:
      for line in iter(stream.readline, b''):
        queue.put((stream_name, line.decode('utf-8')))
        if halt.is_set():
          return True
      stream.close()

  def enqueue_input(self, command, queue):
    try:
      queue.put(self.r.stdin.write(command.encode('utf-8')), block=True)
      queue.put(self.r.stdin.flush(), timeout=1)
    except BrokenPipeError as e:
      print('Command failure, pipe closed')
      raise e
    except Full as e:
      print('Queue full')
      raise e

  def send_queued(self, command):
    print(f'active threads: {active_count()}')
    ON_POSIX = 'posix' in sys.builtin_module_names
    if 'input_queue' not in dir(self):
      self.input_queue = Queue()
    input_thread = Thread(target=self.enqueue_input, args=(command, self.input_queue))
    #input_thread.daemon = True
    input_thread.start()
    input_thread.join(10)
    print(f'active threads: {active_count()}')
    #self.input_queue.get_nowait()
    print(f'active threads: {active_count()}')

  # send a command to R
  # need to queue the input?
  # or do something to stop blocking and deal with errors
  def send(self, command):
    # need to do a check for end of line here
    self.r.stdin.write(command.encode('utf-8'))
    self.r.stdin.flush()

