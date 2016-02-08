import sys
sys.path.append('lib')

import sqlite3
import logging
import os

logger = logging.getLogger('prog')

class Database:
  def getList():
    return {}  
  @staticmethod
  def getDatabase(dbInfo):
    if dbInfo == None or "type" not in dbInfo:
      logger.warning("No database configuration found")
      print database
    else:
      try:
        return globals()[dbInfo['type']+"Database"](dbInfo)
      except Exception as ex:
        logger.warning("Database engine not instanciable: %s"%str(ex))
    return Database()

class SQLiteDatabase(Database):
  def __init__(self,dbInfo):
    self.dbInfo = dbInfo
    self.conn = None
    if not "file" in dbInfo:
      logger.error("SQLiteDatabase need a database file")
    elif not os.path.exists(dbInfo['file']):
      logger.warning("SQLiteDatabase did not found the database file. Creating")
      self.conn = sqlite3.connect(dbInfo['file'])
      c = self.conn.cursor()
      c.execute("CREATE TABLE switchs (id,name,serial,basemac,variables)")
      c.execute("INSERT INTO switchs VALUES(0,'name','SN00000000','00:00:00:00:00:00','{a:1,b:3}')")
      self.conn.commit()
    else:
      self.conn = sqlite3.connect(dbInfo['file'])
  def _rowFactory(self,cursor,row):
    d={}
    for idx,col in enumerate(cursor.description):
      d[col[0]] = row[idx]
    return d
  def getList(self):
   self.conn.row_factory = self._rowFactory
   c = self.conn.cursor()
   res = c.execute("SELECT * FROM switchs")
   return res.fetchall()
