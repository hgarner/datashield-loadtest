from subprocess import Popen, PIPE
import sys
from threading import Thread, active_count
from queue import Queue, Empty, Full

class DsR():

  # on instantiation, create a new r process and read queue
  def __init__(self, *args, **kwargs):
    self.r = Popen(['/usr/bin/R --vanilla'], stdin=PIPE, stdout=PIPE, shell=True)
    # todo above uses stderr - need nonblocking read on this
    # note that if we use stderr it seems to break the output of some ds commands (e.g. ds.dim)
    self.begin_output_queue()
    # turn off errors from r
    #self.send('options(error=expression(NULL))\n');

  # del method to make sure we kill the r process and associated
  # read thread on gc
  def __del__(self):
    self.r.kill()

  # setup a queue for the output of the r process
  def begin_output_queue(self):
    ON_POSIX = 'posix' in sys.builtin_module_names
    self.output_queue = Queue()
    self.output_thread = Thread(target=self.enqueue_output, args=(self.r.stdout, self.output_queue))
    self.output_thread.daemon = True # make sure thread dies with the prog
    self.output_thread.start()

  # read everything that's been output by the r process
  def read_output_queue(self):
    output = ''
    # this is not ideal
    # probably better with asyncio
    while True:
      try:
        output += self.output_queue.get_nowait().decode('utf-8')
      except Empty:
        break
    return output

  # passed an output stream and queue, 
  # will read and put output onto queue
  def enqueue_output(self, output, queue):
    for line in iter(output.readline, b''):
      queue.put(line)
    output.close()

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
    input_thread.daemon = True
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

