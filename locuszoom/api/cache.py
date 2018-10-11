from abc import ABCMeta, abstractmethod
import msgpack
from six import iteritems
from six.moves.cPickle import dumps, loads
from collections import OrderedDict
from intervaltree import IntervalTree, Interval

class IntervalCache(metaclass=ABCMeta):
  def __init__(self):
    pass

  @abstractmethod
  def store(self,key,start,end,data):
    """
    Store data into a cache.

    It is normally expected that your key contains something chromosome or region specific,
    though it is not required.

    If you attempt to store data that is within the bounds of what has already been stored, this method is
    essentially a noop.

    If you store data for an interval that is larger than what was previously stored, only the disjoint (new)
    start/end intervals/data will be inserted. Previous data in the cache will be left untouched.

    To completely store new data within an interval, you should delete the key first.

    Args:
      key: str
      start: int
      end: int
      data: dict, mapping a position (int) to a value. e.g.:
        data[19141413] = {
          "variant": "1:1_A/G",
          "r2": 0.34
        }

    Returns:
      None
    """

    pass

  @abstractmethod
  def retrieve(self,key,start,end,force_subinterval=False):
    """
    Returns an interval from the cache.

    If you request a region that is larger than what has been previously stored before, the method will normally return
    None to signify that you need to compute for the larger region. This behavior can be overriden by supplying
    force_subinterval=True, which causes this method to return any data within the interval specified regardless.

    It you request a region that is smaller than the previously stored bounds, it will be returned.

    Args:
      key: str
      start: int
      end: int
      force_subinterval: bool

    Returns:
      dict: data stored for this interval

    Raises:
      ValueError: if key does not exist within cache
    """

    pass

  @abstractmethod
  def delete(self,key):
    """
    Drop a key from the cache.

    It is valid to attempt to delete a key that does not actually exist in the cache.

    Args:
      key: str

    Returns:
      None

    """

    pass

def interval_contained(tree,interval):
  if not isinstance(interval,Interval):
    interval = Interval(*interval)

  return any([i.contains_interval(interval) for i in tree.search(interval)])

# def find_disjoint(tree,query):
#   """
#   Will use this in later iteration if we want to tell LD API exactly what interval
#   it needs to calculate beyond what is already cached
#   """
#
#   overlaps = tree.search(query)
#   qtree = IntervalTree([query])
#
#   for o in overlaps:
#     qtree.chop(o.begin,o.end)
#
#   return qtree

class RedisIntervalCache(IntervalCache):
  def __init__(self,redis_client=None):
    if redis_client is None:
      raise ValueError("Must supply connected redis client when creating cache")

    self.red = redis_client

  def store(self,key,start,end,data):
    # Which intervals have we already stored?
    redis_itree = self.red.hget(key,"itree")
    if redis_itree is None:
      itree = IntervalTree()
    else:
      itree = loads(redis_itree)

    # Add our new interval into the tree
    interval = Interval(start,end)
    itree = itree | IntervalTree([interval])
    itree.merge_overlaps()

    zset = key + "__zset" # name of the redis sorted set
    self.red.hmset(key,{
      "itree": dumps(itree),
      "zset": zset
    })

    # Start a redis pipeline. All of these actions are committed to the server in batch and within a single
    # transaction, rather than executing each one separately over the network.
    pipe = self.red.pipeline()

    # Store the data. Each key in the data should be a position, and value can be arbitrary data.
    for k, v in iteritems(data):
      v_serial = v
      if not isinstance(v,str):
        v_serial = msgpack.packb(v)

      pipe.zadd(zset,k,v_serial)

    pipe.execute()

  def retrieve(self,key,start,end,force_subinterval=False):
    # Check if we've tried to store this region before
    if not self.red.exists(key):
      return None

    itree = loads(self.red.hget(key,"itree"))
    zset = self.red.hget(key,"zset")

    if not self.red.exists(zset):
      # The sorted set was evicted by the LRU mechanism
      # but the master/interval key was not
      self.red.delete(key)
      return None

    interval = Interval(start,end)
    if not interval_contained(itree,interval) and not force_subinterval:
      # If the region previously calculated is too small, and we're not forcing
      # the return of subintervals, return None to signify a computation is needed.
      return None

    data = OrderedDict()
    for record in self.red.zrangebyscore(zset,start,end,withscores=True):
      pos = int(record[1])
      value = msgpack.unpackb(record[0])
      data[pos] = value

    return data

  def delete(self,key):
    zset = self.red.hget(key,"zset")
    self.red.delete(key)
    self.red.delete(zset)
