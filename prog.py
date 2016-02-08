#!/usr/bin/python

import sys
sys.path.append('lib')


import logging
import signal
import time
import sqlite3
from template import Template
from configuration import Configuration
from tftpserver import TFTPServer
from httpserver import HTTPServer
from database import Database


def signal_handler(signal, frame):
  global stop_services
  stop_services = True


signal.signal(signal.SIGINT, signal_handler)

logger = logging.getLogger('prog')
config = Configuration()
templates = Template(config)

logLevel = logging.ERROR
if(config['debug']):
  try:
    logLevel = {'WARNING':logging.WARNING,'INFO':logging.INFO,'DEBUG':logging.DEBUG}[config['debug']]
  except:
    logLevel = logging.ERROR

logger.setLevel(logLevel)
logger.debug("log level: %d"%logLevel)
database = Database.getDatabase(config['database'])

tftpserver = TFTPServer(database=database,**config['binding']['tftp'])
httpserver = HTTPServer(database=database,**config['binding']['http'])

tftpserver.start()
httpserver.start()
time.sleep(1)

stop_services = False


while tftpserver.running and httpserver.running and not stop_services:
  time.sleep(1)

logger.info("HTTP server running" if httpserver.running else "HTTP server has stopped")
logger.info("TFTP server running" if tftpserver.running else "TFTP server has stopped")
logger.info('Stopping all services')

tftpserver.stop()
httpserver.stop()

while tftpserver.running or httpserver.running:
  logger.info("Waiting for services to stop")
  time.sleep(1)

