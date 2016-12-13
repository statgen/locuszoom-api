from abc import ABCMeta, abstractmethod
import redis, json
from six import iteritems
from collections import OrderedDict

class IntervalCache:
  __metaclass__ = ABCMeta

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

class RedisIntervalCache(IntervalCache):
  def __init__(self,redis_client=None):
    if redis_client is None:
      raise ValueError("Must supply connected redis client when creating cache")

    self.red = redis_client

  def store(self,key,start,end,data):
    zset = key + "__zset" # name of the redis sorted set
    self.red.hmset(key,{
      "start": start,
      "end": end,
      "zset": zset
    })

    # Start a redis pipeline. All of these actions are committed to the server in batch and within a single
    # transaction, rather than executing each one separately over the network.
    pipe = self.red.pipeline()

    # Store the data. Each key in the data should be a position, and value can be arbitrary data.
    for k, v in iteritems(data):
      v_serial = v
      if not isinstance(v,str):
        v_serial = json.dumps(v)

      pipe.zadd(zset,k,v_serial)

    pipe.execute()

  def retrieve(self,key,start,end,force_subinterval=False):
    # Check if we've tried to store this region before
    if not self.red.exists(key):
      return None

    stored_start = int(self.red.hget(key,"start"))
    stored_end = int(self.red.hget(key,"end"))
    zset = self.red.hget(key,"zset")

    if (stored_start > start or stored_end < end) and not force_subinterval:
      # If the region previously calculated is too small, and we're not forcing
      # the return of subintervals, return None to signify a computation is needed.
      return None

    data = OrderedDict()
    for record in self.red.zrangebyscore(zset,start,end,withscores=True):
      pos = int(record[1])
      value = json.loads(record[0])
      data[pos] = value

    return data

  def delete(self,key):
    zset = self.red.hget(key,"zset")
    self.red.delete(key)
    self.red.delete(zset)
