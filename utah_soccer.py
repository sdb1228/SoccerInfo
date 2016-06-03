from lxml import html
from bs4 import BeautifulSoup
import requests,json,httplib,urllib,sys,dryscrape,time, psycopg2
from slack import draft_slack_message

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
    print 'Team: %s' % team
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
  connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
  connection.connect()
  for team in teamNames:
    print 'Team: %s' % team.attrib['value']
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
          connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
          connection.connect()
          continue
        else:
          print "There was a failure in teamListUpdate(), could not resolve after 5 attempts, aborting..."
          draft_slack_message("Utah Soccer", "failed", str(e))
          return
      break



def fields():
  connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
  cursor = connection.cursor()
  url = 'https://utahsoccer.org/fields-2/'
  session = dryscrape.Session(base_url = url)
  session.visit(url)
  soup = BeautifulSoup(session.body())
  fields = soup.findAll("div", {"class": "su-note-inner"})
  for field in fields:
   need = field.contents
   globalFieldName = ""
   for nee in need:
    if not isinstance(nee, basestring):
      if not nee:
        continue
      noo = nee.contents
      if not noo:
        continue
      fieldName = noo[0].lstrip()
      fieldName = fieldName.rstrip()
      if fieldName == "Map":
        continue
      globalFieldName = fieldName
    else:
      address = nee.rstrip()
      address = address.lstrip()
      address = address.split(",")
      if not address[0]:
        continue


      city = address[1]
      city = city.rstrip()
      city = city.lstrip()
      address = address[0]
      address = address.rstrip()
      address = address.lstrip()
      globalFieldName = globalFieldName.rstrip()
      globalFieldName = globalFieldName.lstrip()
      print address + " " + city+ " " + " " + globalFieldName

      selectQuery = """SELECT * FROM "fields" WHERE name='{0}'; """.format(globalFieldName)
      cursor.execute(selectQuery)
      field = cursor.fetchone()

      if field is not None:
        print "Updating " + globalFieldName
        updateQuery = """UPDATE "fields" SET  "name" = %s, "address" = %s, "city" = %s, "state" = %s WHERE "id" = %s ; """
        updateData = (globalFieldName, address, city, "UT", field[5])
        cursor.execute(updateQuery, updateData)
        connection.commit()
      else:
        print "Inserting " + globalFieldName
        insertQuery = """INSERT INTO "fields" ("name", "address", "city", "state") VALUES (%s, %s, %s, %s);"""
        insertData = (globalFieldName, address, city, "UT")
        cursor.execute(insertQuery, insertData)

      connection.commit()
      globalFieldName = ""
      continue


#
# To be run AFTER 'utahSoccerAdultOutdoorGamesUpdate()'
# Scrapes the Utah Soccer site for that teamId and stores a list of all games played by the corresponding team in the 'AdultOutdoorSoccerGames' table of the Parse DB.
#
#
def utahSoccerAdultPlayedOutdoorGamesUpdate():
  url = 'https://utahsoccer.org/public_manage_games_completed_process.php?s=2014&l=&t=%20(All)'
  session = dryscrape.Session(base_url = url)
  session.visit(url)
  response = session.body()
  tree = html.fromstring(response)
  games = tree.xpath('//tbody/tr')
  connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
  connection.connect()
  for game in games:
    while True:
      try:
        children = game.getchildren()
        if len(children) < 16:
          break

        gameNumber = children[4].text
        print 'GameNumber: %s' % gameNumber
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
        draft_slack_message("Utah Soccer", "failed", str(e))
        print str(e)
        break

#
# To be run AFTER 'utahSoccerAdultOutdoorUpdate()'
# Scrapes the Utah Soccer site for that teamId and stores a list of all games played by the corresponding team in the 'AdultOutdoorSoccerGames' table of the Parse DB.
#
#
def utahSoccerAdultOutdoorGamesUpdate():
  retries = 0
  while True:
    try:
      url = 'http://www.utahsoccer.org/public_manage_schedules_process.php?s=2015&l=&t=%20(All)'
      skipCount = 0
      session = dryscrape.Session(base_url = url)
      session.visit(url)
      response = session.body()
      tree = html.fromstring(response)
      games = tree.xpath('//tbody/tr')
      connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
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
            else:
              realisticDate = children[4].text[-5:] + "-" + children[4].text[2] + children[4].text[3]
              gameNumber = children[2].text
              print 'GameNumber: %s' % gameNumber
              date = children[3].text[:3] + " " + realisticDate + " " + children[5].text
              division = children[8].text
              homeTeam = children[12].text
              awayTeam = children[14].text
              field = children[16].text



              # Add link back to the team table for easy query later
              params = urllib.urlencode({"where":json.dumps({
                    "teamId": homeTeam
              })})
              connection.request('GET', '/1/classes/AdultOutdoorSoccerTeams?%s' % params,'', {
                     "X-Parse-Application-Id": applicationId,
                     "X-Parse-REST-API-Key": apiKey,
                   })
              results = json.loads(connection.getresponse().read())
              # Object doesn't exist, Continue for now.  Better handeling later
              if results.values() == [[]]:
                continue
              else:
                homeTeamObjId = results['results'][0]['objectId']

              # Add Team information for AwayTeam if it doesn't exist in the table.
              params = urllib.urlencode({"where":json.dumps({
                    "teamId": awayTeam
              })})
              connection.request('GET', '/1/classes/AdultOutdoorSoccerTeams?%s' % params,'', {
                     "X-Parse-Application-Id": applicationId,
                     "X-Parse-REST-API-Key": apiKey,
              })

              results = json.loads(connection.getresponse().read())
              # Object doesn't exist, Continue for now.  Better handeling later
              if results.values() == [[]]:
                continue
              else:
                awayTeamObjId = results['results'][0]['objectId']

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
              connection.request('PUT', '/1/classes/AdultOutdoorSoccerGames%s' % objId, json.dumps({
                            "awayTeamPointer": {
                             "__op": "AddRelation",
                             "objects": [
                               {
                                 "__type": "Pointer",
                                 "className": "AdultOutdoorSoccerTeams",
                                 "objectId": awayTeamObjId
                               }
                             ]
                           },
                           "homeTeamPointer": {
                             "__op": "AddRelation",
                             "objects": [
                               {
                                 "__type": "Pointer",
                                 "className": "AdultOutdoorSoccerTeams",
                                 "objectId": homeTeamObjId
                               }
                             ]
                           }
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
    except Exception, e:
      print str(e)
      retries += 1
      if retries < 5:
        print "Error retry %s..." % retries
        time.sleep(5)
        connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
        connection.connect()
        continue
      else:
        draft_slack_message("Utah Soccer", "failed", str(e))
        print "There was a failure in gameUpdate(), could not resolve after 5 attempts, aborting..."
        return
    break

#
# Single method to combine all update methods for Utah Soccer facility.
# fields()
def utah_soccer_run():
  utahSoccerAdultOutdoorTeamsUpdate()
  utahSoccerAdultPlayedOutdoorGamesUpdate()
  utahSoccerAdultOutdoorGamesUpdate()
  draft_slack_message("Utah Soccer", "success")
