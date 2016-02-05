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
import os
import isc_dhcp_leases.iscdhcpleases


def signal_handler(signal, frame):
  tftpserver.stop()
  stop_services = True


signal.signal(signal.SIGINT, signal_handler)

class Template:
  def __init__(self,config):
    self.config = config['configurations']
  def getConfigForMac(self,mac):
    mac = mac.lower()
    varsar = [a for a in self.config if 'hardwareAddress' in a and  a['hardwareAddress'].lower() == mac]
    return self._getConfig(varsar)
  def getConfigForName(self,name):
    name = name.lower()
    varsar = [a for a in self.config if 'name' in a and a['name'].lower() == name]
    return self._getConfig(varsar)
  def _getConfig(self,varsar):
    if len(varsar) == 0:
      logging.error("No configuration found")
      return None
    if len(varsar) > 1:
      logging.warning("Multiple configuration found. Using first one")
    vars = varsar[0]
    if not 'template' in vars:
      return None
    template = vars['template']
    if not os.path.exists('templates/'+template):
      logging.error("Can't find template %s",template)
      return None
    with open('templates/'+template) as tf:
      templateContent = tf.read()
      for key in vars:
        templateContent = templateContent.replace('<%s>'%key,str(vars[key]))
      return templateContent
    return None
    
    


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
  def __init__(self,address="0.0.0.0",port="69",root="/dev/null",leases="/var/lib/dhcp/dhcpd.leases",configurations={}):
    self.address = address
    self.port = port
    self.root = root
    self.running = False
    self.leases = leases
    self.configurations = configurations
  
  def _get(self,filename):
    file = ''
    logging.error('Serving %s'%filename)
    if 'network-confg' in filename:
      for mac in isc_dhcp_leases.iscdhcpleases.IscDhcpLeases(self.leases).get_current():
        varsar = [a for a in self.configurations if 'hardwareAddress' in a and  a['hardwareAddress'].lower() == mac.lower()]
        logging.error('%s %d',mac,len(varsar))
        if len(varsar) >= 1:
          file += "ip host %s %s\n"%(varsar[0]['name'],varsar[0]['admip'])
    elif '-confg' in filename:
      name = filename[:-6]
      varsar = [a for a in self.configurations if 'name' in a and  a['name'].lower() == name.lower()]
      logging.error("%s %d"%(name,len(varsar)))
      if len(varsar) >= 1:
        file = templates.getConfigForName(name)
    return cStringIO.StringIO(file)
  
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
  def setConfig(self,config):
    self.configurations = config

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
templates = Template(config)

tftpserver = TFTPServer(**config['binding']['tftp'])
tftpserver.setConfig(config['configurations'])
httpserver = HTTPServer(**config['binding']['http'])

tftpserver.start()
httpserver.start()
time.sleep(1)
stop_services = False
while tftpserver.running and httpserver.running and not stop_services:
  time.sleep(1)

logging.error('Stopping all')
print tftpserver.running,httpserver.running,stop_services

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

