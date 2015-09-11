#from utah_soccer import utah_soccer_run
from lets_play import lets_play_run
import time

hours = 12

while True:
  print "==========================================================================================="
  print "Running Let's Play at: %s" % time.ctime()
  lets_play_run()
  print "Finished Let's Play run at: %s" % time.ctime()
  print "==========================================================================================="

#  print "==========================================================================================="
#  print "Running UtahSoccer at: %s" % time.ctime()
#  utah_soccer_run()
#  print "Finished UtahSoccer run at: %s" % time.ctime()
#  print "==========================================================================================="

  time.sleep(hours*60*60)
