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

