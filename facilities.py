from utah_soccer import utah_soccer_run
from lets_play import lets_play_run
from distutils.core import setup, Command
import time

setup(name='dryscrape',
      version='1.0',
      description='a lightweight Javascript-aware, headless web scraping library for Python',
      author='Niklas Baumstark',
      author_email='niklas.baumstark@gmail.com',
      license='MIT',
      url='https://github.com/niklasb/dryscrape',
      packages=['dryscrape', 'dryscrape.driver'],
      install_requires=['webkit_server>=1.0', 'lxml', 'xvfbwrapper'],
      )

hours = 12

while True:
  print "==========================================================================================="
  print "Running Let's Play at: %s" % time.ctime()
  lets_play_run()
  print "Finished Let's Play run at: %s" % time.ctime()
  print "==========================================================================================="

  print "==========================================================================================="
  print "Running UtahSoccer at: %s" % time.ctime()
  utah_soccer_run()
  print "Finished UtahSoccer run at: %s" % time.ctime()
  print "==========================================================================================="

  time.sleep(hours*60*60)
