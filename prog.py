import sys
sys.path.append('lib')


import tftpy
import yaml
import argparse
import os
import logging
import threading
import signal
import time
import cStringIO
import sqlite3
import tornado.ioloop
import tornado.web

def signal_handler(signal, frame):
  tftpserver.stop()
  stop_services = True


signal.signal(signal.SIGINT, signal_handler)



class Configuration:
  def __init__(self):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', help='Configuration file',required=True)
    parser.add_argument('--version', action='version', version='%(prog)s 2.0')
    args = parser.parse_args()
    confFile = args.config
    try:
      with open(confFile) as f:
        config = yaml.load(f)
    except yaml.scanner.ScannerError:
      logging.error("Config file %s is not a Yaml file",confFile)
    except IOError as e:
      logging.error("I can't read \"%s\": %s",confFile,e)
    mergeObject = {'database': '/var/lib/autoinstall/database.db', 
                   'binding': {'tftp': {'port': 69, 'address': '0.0.0.0','root':'/dev/null'}, 
                               'http': {'port': 8080, 'address': '0.0.0.0','root':'/dev/null'}},
                   'leases': '/var/lib/dhcp/dhcpd.leases'}
    self.config = self.mergeObject(config,mergeObject)
  
  def mergeObject(self,object,default):
    value = object
    for key in default:
      if not key in value:
        value[key] = default[key]
      elif type(default[key]) is dict:
        value[key] = self.mergeObject(value[key],default[key])
    return value
  
  def __getitem__(self,value):
    if value in self.config:
      return self.config[value]
    else:
      return None
    
    
    

class TFTPServer:
  
  
  def __init__(self,address="0.0.0.0",port="69",root="/dev/null"):
    self.address = address
    self.port = port
    self.root = root
    self.running = False
  
  def _get(self,filename):
    return cStringIO.StringIO(filename)
  
  def _run(self):
    try:
      self.server = tftpy.TftpServer(self.root,self._get)
      self.running = True
      self.server.listen(self.address, self.port)
      self.running = False
    except Exception as e:
      logging.error("Can't start TFTP server %s",e)
      self.running = False
  
  def start(self):
    threading.Thread(None, self._run ).start()
  
  def stop(self):
    self.server.stop()

class ProfileHandler(tornado.web.RequestHandler):
  def get(self):
    self.write("coucou")

class HTTPServer:
  def __init__(self,address="0.0.0.0",port="8080",root="/dev/null"):
    self.port = port
    self.address = address
    self.running = False
    self.root = root
    
    self.application = tornado.web.Application([
        (r"/", ProfileHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.root})
    ])
  
  def _run(self):
    self.running = True
    try:
      self.application.listen(self.port)
      tornado.ioloop.IOLoop.instance().start()
      self.running = False
    except:
      logging.error("Can't start HTTP server")
      self.running = False
    
  def start(self):
    threading.Thread(None, self._run ).start()
    
  def stop(self):
    tornado.ioloop.IOLoop.instance().stop()
    



logger = logging.getLogger('prog')
config = Configuration()
tftpserver = TFTPServer(**config['binding']['tftp'])
httpserver = HTTPServer(**config['binding']['http'])

tftpserver.start()
httpserver.start()
stop_services = False
while tftpserver.running and httpserver.running and not stop_services:
  time.sleep(1)

tftpserver.stop()
httpserver.stop()
while tftpserver.running or httpserver.running:
  print 'waiting for ',
  if tftpserver.running:
    print "TFTP server",
  if httpserver.running:
    print "HTTP server",
  print ""
  time.sleep(1)

