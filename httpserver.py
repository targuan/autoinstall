from tornado.web import RequestHandler, StaticFileHandler, Application
from tornado.ioloop import IOLoop
from threading import Thread
import logging

logger = logging.getLogger('prog')


class IndexHandler(RequestHandler):
  def initialize(self,database={}):
    self.database = database
  def get(self):
    self.write(self.database)

class HTTPServer:
  def __init__(self,address="0.0.0.0",port="8080",root="/dev/null",database={}):
    self.port = port
    self.address = address
    self.running = False
    self.root = root
    self.database = database
    
    self.application = Application([
        (r"/", IndexHandler,dict(database=database)),
        (r"/static/(.*)", StaticFileHandler, {"path": self.root})
    ])
  
  def _run(self):
    self.running = True
    try:
      self.application.listen(self.port)
      IOLoop.instance().start()
      self.running = False
    except:
      logging.error("Can't start HTTP server")
      self.running = False
    
  def start(self):
    logger.info("Starting HTTP server %s:%s"%(self.address,self.port))
    Thread(None, self._run ).start()
    
  def stop(self):
    IOLoop.instance().stop()

