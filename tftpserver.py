import sys
sys.path.append('lib')

import tftpy
import logging
import threading
import isc_dhcp_leases.iscdhcpleases
import cStringIO

logger = logging.getLogger('prog')

class TFTPServer:
  def __init__(self,address="0.0.0.0",port="69",root="/dev/null",leases="/var/lib/dhcp/dhcpd.leases",database={}):
    self.address = address
    self.port = port
    self.root = root
    self.running = False
    self.leases = leases
    self.database = database
  
  def _get(self,filename):
    file = ''
    logger.error('Serving %s'%filename)
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
    logger.info("Starting TFTP server %s:%s"%(self.address,self.port))
    threading.Thread(None, self._run ).start()
  
  def stop(self):
    self.server.stop()
