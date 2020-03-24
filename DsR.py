from subprocess import Popen, PIPE
import sys
from threading import Thread
from queue import Queue, Empty

class DsR():

  # on instantiation, create a new r process and read queue
  def __init__(self, *args, **kwargs):
    self.r = Popen(['/usr/bin/R --vanilla'], stdin=PIPE, stdout=PIPE, shell=True)
    self.begin_output_queue()

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

  # send a command to R
  # need to queue the input?
  # or do something to stop blocking and deal with errors
  def send(self, command):
    # need to do a check for end of line here
    self.r.stdin.write(command.encode('utf-8'))
    self.r.stdin.flush()

