#!/usr/bin/python

import glob
import os
import string
import hashlib
import sys
import progress_bar
from stat import *

debug=0
progress_enabled=1
short_print=1

SILENT=0
ERROR=1
DEBUG=3
EERBOSE=5

FALSE=0
TRUE=1

def log(min_deb, str, vals=None):
  if debug>=min_deb:
    if vals!=None:
      print str % vals
    else:
      print str

def md5sum(filename, buf_size=8192):
  m = hashlib.md5()
  # the with statement makes sure the file will be closed 
  with open(filename) as f:
    # We read the file in small chunk until EOF
    data = f.read(buf_size)
    while data:
      # We had data to the md5 hash
      m.update(data)
      data = f.read(buf_size)
    # We return the md5 hash in hexadecimal format
    f.close()
    return m.hexdigest()

class File:
  name=""
  __md5=""
  size=0
  md5group=0
  sizegroup=0

  def saveToFile(self, fl):
    fl.write("%s:%d:%s\n" % (self.__md5, self.size, self.name))

  def parseStr(self, str):
    sz=""
    self.__md5, sz, self.name=str.split(':')
    self.size=string.atoi(sz)
    self.name=self.name.rstrip()
    try:
      mode=os.stat(self.name)[ST_MODE]
      if S_ISREG(mode):
        log(DEBUG, "restored: md5=%s, size=%d, name=%s" , (self.__md5, self.size, self.name))
	return TRUE
    except OSError:
      log(DEBUG, "file access error, may be removed: '%s'" % self.name)
    return FALSE

  def calcMD5(self):
    if self.__md5=="":
      #print "cache missed: %s" %self.name
      self.__md5=md5sum(self.name)
  
  def getMD5(self, fl):
    if self.__md5=="":
      self.__md5=fl.getCachedMD5(self.name)
      if self.__md5=="":
        self.calcMD5()
    return self.__md5

  def getMD5_2(self):
    if self.__md5=="":
      return "BADBAD"
    else:
      return self.__md5

class FileList:
  files=list()
  samesizefiles=list()
  samemd5files=list()

  __cur_p=0
  __total_p=0

  __scan_progr=None

  __cached_fnames=list()
  __cached_files=list()

  def getCachedMD5(self, name):
    try:
      idx=self.__cached_fnames.index(name)
      res=self.__cached_files[idx].getMD5_2()
      if res=="BADBAD":
        return ""
      return res
    except ValueError:
      return ""

  def scan(self, path):
    print "Scan directories"
    self.__scan_rec(path)
    print ""

  def __scan_rec(self, path):
    dcont=os.listdir(path)
    for f in dcont:
      if f==".ignore_dupes":
        return

    if progress_enabled:
      self.__total_p=self.__total_p+len(dcont)
      self.__scan_progr=progress_bar.ProgressBar(0, self.__total_p, 50, mode='fixed', char='#')
    for f in dcont:
      if progress_enabled:
        self.__cur_p=self.__cur_p+1
        self.__scan_progr.update_amount(self.__cur_p)
        print "cur=%d, tot=%d "% (self.__cur_p, self.__total_p),self.__scan_progr,"\r",
      sys.stdout.flush()
      pn=os.path.join(path, f)
      try:
        mode=os.stat(pn)[ST_MODE]
        if S_ISDIR(mode) and f!=".git" and f!=".svn":
          self.__scan_rec(pn)
        elif S_ISREG(mode):
          self.check(pn)
        else:
          log(ERROR, 'unknown file %s' , pn)
      except OSError:
        log(ERROR, 'file access error %s' , pn)
#    self.__cur_p=self.__cur_p-len(dcont)
 #   self.__total_p=self.__total_p-len(dcont)

  def check(self, filename):
    log (DEBUG, "check %s" , filename)

    #if filename in self.__cached_fnames:
    #  return

    f=File()
    f.name=filename
    f.size=os.stat(filename)[ST_SIZE]
    self.files.append(f)
    log ( DEBUG, "added: %s, (%d)" , (filename, f.size))

  def sortBySize(self):
    print "Sort by size"
    self.files=sorted(self.files, key=lambda File: File.size)

  def saveToFile(self):
    fle=file("uniq_cache.cache", "w")
    for f in self.files:
      if f.getMD5_2()!="BADBAD":
        f.saveToFile(fle)
    fle.close()

  def loadFromFile(self):
    print "Load cache"
    try:
      fle=file("uniq_cache.cache", "r")
      for str in fle:
        fl=File()
        if fl.parseStr(str):
          self.__cached_files.append(fl)
      self.__cached_fnames=list(obj.name for obj in self.__cached_files)
      #for s in self.__cached_fnames:
      #  print "cac=%s" %s

    except IOError:
      log(DEBUG, "Cache not found")
    
  def checkSizes(self):
    print "Check size"
    cursize=self.files[0].size
    curszlist=list()
    append_prev=1

    if progress_enabled:
      pb=progress_bar.ProgressBar(0, len(self.files), 50, mode='fixed', char="#")
    for i in range(1, len(self.files)):
      if progress_enabled:
        pb.increment_amount()
        print pb, '\r', 
      if self.files[i].size==cursize:
#        print "append"
	if append_prev!=0:
	  append_prev=0
	  curszlist.append(self.files[i-1])
        curszlist.append(self.files[i])
      else:
#        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#	print "len=%d" % len(curszlist)
#	print "len2=%d" % len(self.samesizefiles)
        if len(curszlist)!=0:
	  self.samesizefiles.append(curszlist)
	if len(curszlist)==1:
	  print "EPIC_FAIL"
	del curszlist
	curszlist=list()
	cursize=self.files[i].size
	append_prev=1
    if len(curszlist)!=0:
      self.samesizefiles.append(curszlist)
    print ""
	
  def sortByMD5(self):
    print "Sort by MD5"
    curmd5group=1
    tmplist=list()
    if progress_enabled:
      pb=progress_bar.ProgressBar(0, len(self.samesizefiles), 50, mode='fixed', char="#")
    for ss in self.samesizefiles:
      #for i in (range(0,len(ss))):
      #  ss[i].calcMD5()
      #  print "sort=%s" % ss[i].name
      ss=sorted(ss, key=lambda File: File.getMD5(self))
      tmplist.append(ss)
      if progress_enabled:
        pb.increment_amount()
        print pb, '\r',
    self.samesizefiles=tmplist
    print ""

  def checkMD5(self):
    print "Check MD5"
    if progress_enabled:
      pb=progress_bar.ProgressBar(0, len(self.samesizefiles), 50, mode='fixed', char="#")
    for ss in self.samesizefiles:
      if progress_enabled:
        pb.increment_amount()
        print pb, '\r', 
      curmd5list=list()
      curmd5=ss[0].getMD5(self)
      ap_pr=1
      for i in range(1, len(ss)):
        log(DEBUG, "i=%d, ifn=%s, sz=%d" , (i, ss[i].name, ss[i].size))
	if curmd5==ss[i].getMD5(self):
	  log(DEBUG, "same")
  	  if ap_pr!=0:
	    ap_pr=0
	    curmd5list.append(ss[i-1])
	  curmd5list.append(ss[i])
	else:
	  log(DEBUG, "diff")
	  if len(curmd5list)!=0:
	    log(DEBUG, "app")
	    self.samemd5files.append(curmd5list)
	  del curmd5list
	  curmd5list=list()
	  curmd5=ss[i].getMD5(self)
	  ap_pr=1
	     #n=n+1
      log(DEBUG, "")
      #n=0
      if len(curmd5list)!=0:
        log(DEBUG, "app")
        self.samemd5files.append(curmd5list)
      del curmd5list
    print ""
       
  def printResult(self, resfile):
    fle=file(resfile, "w")

    for ss in fl.samemd5files:
      for t in ss:
        if short_print:
	  fle.write("%s\n" % (t.name))
        else:
          fle.write("%s\t%d\t%s\n" % (t.name, t.size, t.getMD5_2()))
      fle.write("\n")
   
    fle.close()


  def printFiles(self):
    for t in self.files:
      print "file=%s, md5=%s" % (t.name, t.getMD5_2())


resfile=sys.argv[1]

pathes=list()
i=2
if len(sys.argv):
  while i<len(sys.argv):
    print "pathes=%s" %sys.argv[i]
    pathes.append(sys.argv[i])
    i+=1
    
#exit()
fl=FileList()

fl.loadFromFile()

i=0
while i<len(pathes):
  print "scan path=%s" % pathes[i]
  fl.scan(pathes[i])
  i+=1

#fl.scan(path)
fl.sortBySize()
fl.checkSizes()
fl.sortByMD5()
#fl.printFiles()
#exit()

fl.checkMD5()

fl.saveToFile()

fl.printResult(resfile)

exit()
#for t in fl.files:
#  log(DEBUG, "fn=%s, sz=%d" ,(t.name, t.size))
#exit()
n=0

for ss in fl.samemd5files:
    for t in ss:
      print "n=%d, ifn=%s, sz=%d" % (n, t.name, t.size)
      n=n+1
    print ""
    n=0

