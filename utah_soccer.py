from lxml import html
import sys  
from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import *  
import requests,json,httplib,urllib,time

class Render(QWebPage):  
  def __init__(self, url):  
    self.app = QApplication(sys.argv)  
    QWebPage.__init__(self)  
    self.loadFinished.connect(self._loadFinished)  
    self.mainFrame().load(QUrl(url))  
    self.app.exec_()  
  
  def _loadFinished(self, result):  
    self.frame = self.mainFrame()  
    self.app.quit() 

applicationId = "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv"
apiKey = "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b"


#
# Updates teams division on the parse DB that play outdoor at UtahSoccer.org
#
def utahSoccerTeamDivisionUpdate(teamIds, division, connection):
  newDivision = division
  if division == "M" :
    newDivision = "Open Cup"
  if division == "W":
    newDivision = "Women Open Cup"
  for team in teamIds:
    params = urllib.urlencode({"where":json.dumps({
            "teamId": team})})
    connection.request('GET', '/1/classes/AdultOutdoorSoccerTeams?%s' % params,'', {
         "X-Parse-Application-Id": applicationId,
         "X-Parse-REST-API-Key": apiKey,
     })
    results = json.loads(connection.getresponse().read())
    # Object doesn't exist, POST to create new. 

    if results.values() == [[]]:
      return
    # Object exists, PUT to update existing.
    else: 
       call = 'PUT'
       # Better way to obtain objectID for update?  (nested dictionary/array/dictionary is ugly!  Stupid Python...)
       objId = '/%s' % results['results'][0]['objectId']

    connection.request(call, '/1/classes/AdultOutdoorSoccerTeams%s' % objId, json.dumps({
                 "teamId": team,
                 "division": newDivision
               }), {
                 "X-Parse-Application-Id": applicationId,
                 "X-Parse-REST-API-Key": apiKey,
                 "Content-Type": "application/json"
               })
    results = json.loads(connection.getresponse().read())
    print results


#
# To be run before 'fullUtahAdultOutdoorGameListUpdate()' to seed iterable data.
# Scrapes the Utah Soccer Website to obtain a list of all teams currently playing outdoor and stores the team data in the 'AdultOutdoorSoccerTeams' table of the Parse DB.
#
def utahSoccerAdultOutdoorTeamsUpdate():
  page = requests.get('https://utahsoccer.org/public_get_my_team.php')
  tree = html.fromstring(page.text)
  # array of teams
  teamNames = tree.xpath("//select[@name='TID']/option")
  connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=60)
  connection.connect()
  for team in teamNames:
    retries = 0
    while True:
      try:
        if team.attrib['value'] == "0":
          break
        params = urllib.urlencode({"where":json.dumps({
          "teamId": team.attrib['value']})})
        connection.request('GET', '/1/classes/AdultOutdoorSoccerTeams?%s' % params,'', {
               "X-Parse-Application-Id": applicationId,
               "X-Parse-REST-API-Key": apiKey,
             })
        results = json.loads(connection.getresponse().read())
        # Object doesn't exist, POST to create new. 

        if results.values() == [[]]:
           call = 'POST'
           objId = ''
        # Object exists, PUT to update existing.
        else: 
           call = 'PUT'
           # Better way to obtain objectID for update?  (nested dictionary/array/dictionary is ugly!  Stupid Python...)
           objId = '/%s' % results['results'][0]['objectId']

        connection.request(call, '/1/classes/AdultOutdoorSoccerTeams%s' % objId, json.dumps({
                     "teamId": team.attrib['value'],
                     "name": team.text
                   }), {
                     "X-Parse-Application-Id": applicationId,
                     "X-Parse-REST-API-Key": apiKey,
                     "Content-Type": "application/json"
                   })
        results = json.loads(connection.getresponse().read())
        print results
      except Exception, e:
        print str(e)
        retries += 1
        if retries < 5:
          print "Error retry %s..." % retries
          time.sleep(5)
          connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=60)
          connection.connect()
          continue
        else:
          print "There was a failure in teamListUpdate(), could not resolve after 5 attempts, aborting..."
          return
      break
#
# To be run AFTER 'utahSoccerAdultOutdoorGamesUpdate()'
# Scrapes the Utah Soccer site for that teamId and stores a list of all games played by the corresponding team in the 'AdultOutdoorSoccerGames' table of the Parse DB.
#
#
def utahSoccerAdultPlayedOutdoorGamesUpdate():
  url = 'https://utahsoccer.org/public_manage_games_completed_process.php?s=2014&l=&t=%20(All)'
  #This does the magic.Loads everything
  r = Render(url)  
  #result is a QString.
  result = r.frame.toHtml()
  #QString should be converted to string before processed by lxml
  formatted_result = str(result.toAscii())
  # skip the first two records
  tree = html.fromstring(formatted_result)
  games = tree.xpath('//tbody/tr')
  connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=60)
  connection.connect()
  for game in games:
    while True:
      try:
        children = game.getchildren()
        if len(children) < 16:
          break

        gameNumber = children[4].text
        division = children[7].text
        homeTeam = children[9].text
        homeTeamScore = children[11].text
        awayTeam = children[12].text
        awayTeamScore = children[14].text
        field = children[15].text
        if homeTeam == "-1" or awayTeam == "-1" or homeTeam == "0" or awayTeam == "0" or not gameNumber:
          break

        params = urllib.urlencode({"where":json.dumps({
          "gameNumber": gameNumber})})
        connection.request('GET', '/1/classes/AdultOutdoorSoccerGames?%s' % params,'', {
               "X-Parse-Application-Id": applicationId,
               "X-Parse-REST-API-Key": apiKey,
             })
        results = json.loads(connection.getresponse().read())

        # Object doesn't exist, POST to create new.
        if results.values() == [[]]:
           call = 'POST'
           objId = ''
        # Match exists, PUT to update existing match.
        else:
           call = 'PUT'
           objId = '/%s' % results['results'][0]['objectId']

        connection.request(call, '/1/classes/AdultOutdoorSoccerGames%s' % objId, json.dumps({
                     "division": division,
                     "homeTeamScore": homeTeamScore,
                     "awayTeamScore": awayTeamScore,
                     "homeTeam": homeTeam,
                     "awayTeam": awayTeam,
                     "field": field,
                     "gameNumber": gameNumber
                   }), {
                     "X-Parse-Application-Id": applicationId,
                     "X-Parse-REST-API-Key": apiKey,
                     "Content-Type": "application/json"
                   })
        results = json.loads(connection.getresponse().read())
        print results
        break
      except Exception, e:
        print str(e)
        break

#
# To be run AFTER 'utahSoccerAdultOutdoorUpdate()'
# Scrapes the Utah Soccer site for that teamId and stores a list of all games played by the corresponding team in the 'AdultOutdoorSoccerGames' table of the Parse DB.
#
#
def utahSoccerAdultOutdoorGamesUpdate():
  url = 'http://www.utahsoccer.org/public_manage_schedules_process.php?s=2015&l=&t=%20(All)'
  #This does the magic.Loads everything
  r = Render(url)  
  #result is a QString.
  result = r.frame.toHtml()
  #QString should be converted to string before processed by lxml
  formatted_result = str(result.toAscii())
  # skip the first two records
  skipCount = 0
  tree = html.fromstring(formatted_result)
  games = tree.xpath('//tbody/tr')
  connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=60)
  connection.connect()
  for game in games:
    while True:
      try:
        children = game.getchildren()
        if len(children) < 17:
          break

        homeTeam = children[12].text
        awayTeam = children[14].text
        if homeTeam == "-1" or awayTeam == "-1" or homeTeam == "0" or awayTeam == "0":
          break

        realisticDate = children[4].text[-5:] + "-" + children[4].text[2] + children[4].text[3]
        gameNumber = children[2].text
        date = children[3].text[:3] + " " + realisticDate + " " + children[5].text
        division = children[8].text
        homeTeam = children[12].text
        awayTeam = children[14].text
        field = children[16].text


        teams = [homeTeam, awayTeam]
        utahSoccerTeamDivisionUpdate(teams, division, connection)

        params = urllib.urlencode({"where":json.dumps({
          "gameNumber": gameNumber})})
        connection.request('GET', '/1/classes/AdultOutdoorSoccerGames?%s' % params,'', {
               "X-Parse-Application-Id": applicationId,
               "X-Parse-REST-API-Key": apiKey,
             })
        results = json.loads(connection.getresponse().read())

        # Object doesn't exist, POST to create new.
        if results.values() == [[]]:
           call = 'POST'
           objId = ''
        # Match exists, PUT to update existing match.
        else:
           call = 'PUT'
           objId = '/%s' % results['results'][0]['objectId']

        connection.request(call, '/1/classes/AdultOutdoorSoccerGames%s' % objId, json.dumps({
                     "date": date,
                     "gameNumber": gameNumber,
                     "field": field,
                     "homeTeam": homeTeam,
                     "awayTeam": awayTeam,
                     "division": division
                   }), {
                     "X-Parse-Application-Id": applicationId,
                     "X-Parse-REST-API-Key": apiKey,
                     "Content-Type": "application/json"
                   })
        results = json.loads(connection.getresponse().read())
        print results
        break
      except Exception, e:
        print str(e)
        break

hours=10

while True:
  print "Running at: %s" % time.ctime()
  teamListUpdate()
  #gamesUpdate()
  fullGameListUpdate()
  print "Finished run at: %s" % time.ctime()
  time.sleep(hours*60*60)
