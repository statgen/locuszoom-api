from contextlib import contextmanager

@contextmanager
def timer(name=None):
  import time
  start = time.clock()
  yield
  end = time.clock()

  label = "<no label>" if name is None else name
  print "[{}] Time required: {} ms".format(label,(end - start) * 1000)
