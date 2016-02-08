#!/usr/bin/python

import sys
sys.path.append('lib')

import yaml
import argparse
import logging



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
