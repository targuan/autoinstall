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

def signal_handler(signal, frame):
  tftpserver.stop()
  stop_services = True


signal.signal(signal.SIGINT, signal_handler)


class tftpServer:
  running = False
  stopping = False
  
  def __init__(self,address="0.0.0.0",port="69"):
    self.address = address
    self.port = port
  
  def _get(self,filename):
    return cStringIO.StringIO(filename)
  
  def _run(self):
    try:
      self.server = tftpy.TftpServer('/home/targuan',self._get)
      self.running = True
      self.server.listen('0.0.0.0', 69)
      self.running = False
    except Exception as e:
      logging.error("Can't start TFTP server %s",e)
      self.running = False
  
  def start(self):
    if self.stopping:
      return False
    threading.Thread(None, self._run ).start()
  
  def stop(self):
    print 'stopping'
    if self.stopping:
      self.server.stop(True)
    self.stopping = True
    self.server.stop()

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-f', help='Configuration file',required=True)
parser.add_argument('--version', action='version', version='%(prog)s 2.0')

args = parser.parse_args()

logger = logging.getLogger('prog')

try:
  with open(args.f) as f:
    config = yaml.load(f)
except yaml.scanner.ScannerError:
  logging.error("Config file %s is not a Yaml file",args.f)
  exit(1)
except IOError as e:
  logging.error("I can't read \"%s\": %s",args.f,e)
  exit(1)

tftpserver = tftpServer()
tftpserver.start()
time.sleep(1)
stop_services = False
while tftpserver.running and not tftpserver.stopping and not stop_services:
  time.sleep(1)

while tftpserver.running:
  print 'waiting for completion'
  time.sleep(1)

