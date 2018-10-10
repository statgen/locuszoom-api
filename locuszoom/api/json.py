from flask.json import JSONEncoder
import datetime

# Modified JSON encoder to handle datetimes
class CustomJSONEncoder(JSONEncoder):
  def default(self,x):
    if isinstance(x,(datetime.date,datetime.datetime)):
      return x.isoformat()

    return JSONEncoder.default(self,x)

class JSONFloat(float):
  def __repr__(self):
    return "%0.2g" % self
