#!/usr/bin/python

import curses
import sys
import string
import locale
import os

class Screen:
  
  def __init__(self):
    locale.setlocale(locale.LC_ALL,"")
    self.scr=curses.initscr()
    curses.noecho()
    curses.cbreak()
    self.scr.keypad(1)

  def destroy(self):
    curses.nocbreak()
    self.scr.keypad(0)
    curses.echo()
    curses.endwin()

  def select(self, variants):
    if len(variants)<2:
      return
    if len(variants)>9:
      return
    while 1:
      self.scr.clear()
      i=1
      for fn in variants:
        self.scr.addstr("%d)  " % i)
        self.scr.addstr(fn)
        self.scr.addstr("\n")
        i+=1
      self.scr.addstr(25, 0, "(%d of %d) Which will stay (1..9, n, q):" %(self.curpos, self.allcount))
      self.scr.refresh()
      c = self.scr.getch()
      if c in(ord('q'),ord('Q')):
        self.destroy()
        sys.exit(0)
      if c in(ord('n'), ord('N'), ord('S'), ord('s')):
        #just skip
        return
      #n=string.atoi(c)
      if c<=ord('9') and c>ord('0'):
        n=c-ord('0')-1
      
        if n<len(variants):
          i=0
          self.scr.addstr(25, 0, "Is it correct? (y/N)                                              ")
          self.scr.refresh()
          win=curses.newwin(12, 180, 11, 0)
          for fn in variants:
            if i!=n:
              win.addstr(i, 0, "rm %s" % (variants[i]))
            i+=1
          win.refresh()
          c=win.getch()
          if c in(ord('y'), ord('Y')):
            i=0
            for fn in variants:
              if i!=n:
                try:
                  os.remove(variants[i])
                except:
                  print "shit"
              i+=1
            return
          win.clear()
          win.refresh()
          del win
    
  def load(self, fname):
    fl=file(fname, "r")
    self.groups=list()
    cur_group=list()
    for str in fl:
      if str=="\n":
        self.groups.append(cur_group)
	del cur_group
	cur_group=list()
      else:
        cur_group.append(str.rstrip())
    if len(cur_group)!=0:
      self.groups.append(cur_group)
    fl.close()

  def go(self):
    self.allcount=len(self.groups)
    self.curpos=1
    for gr in self.groups:
      self.select(gr)
      self.curpos+=1

  def check_librusec(self, variants):
    found=-1
    i=0
    for t in variants:
      if t.find("SpeccyMania/Games")!=-1:
        found=i
        break
      i+=1
    if found!=-1:
      nl=list()
      for t in variants:
        if t.find("SpeccyMania/Games")==-1:
          try:
            #os.remove(t)
            print "rm -f \""+t+"\""
          except:
            print "shit"
        else:
          nl.append(t)
      variants=nl
    return variants

  def parse_librusec(self):
    groups_tmp=list()
    for gr in self.groups:
      gr2=self.check_librusec(gr)
      if len(gr2)>1:
        groups_tmp.append(gr2)
    self.groups=groups_tmp

s = Screen()

s.load(sys.argv[1])
s.parse_librusec()
#s.go()
s.destroy()
