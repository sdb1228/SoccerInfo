from bs4 import BeautifulSoup
import requests,json,httplib,sys,dryscrape,urllib,time, datetime, threading

applicationId = "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv"
apiKey = "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b"

#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Soccer City site to obtain a list of all youth teams playing currently at Soccer City.
#
def youthTeamListUpdate():
	count = 0
	connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
	connection.connect()
	divisions = []
	while len(divisions) == 0:
		url= 'http://www.soccercityutah.com/#!youthschedules/c14mx'
		session = dryscrape.Session(base_url = url)
		session.set_timeout(30)
		session.visit(url)
		soup = BeautifulSoup(session.body())
		divisions = soup.findAll("a", {"target": "_blank"})
	del divisions[15]
	del divisions[-1]
	del divisions[-1]
	for division in divisions:
	  retries = 0
          while True:
            try:
		url= division['href']
		print "URL " + url
		stringDivision = ""
		if division.span is None:
			stringDivision = division.contents[0]
		else:
			stringDivision = division.span.contents[0]

		print stringDivision + " %s" % count
		print "\n\n"
		session = dryscrape.Session(base_url = url)
		session.set_timeout(30)
		session.visit(url)
		soup = BeautifulSoup(session.body())
		teams = soup.findAll("a")
		count += 1
		if soup.find("a", {"href": "#stats"}) is not None:
			del teams[0]


		for x in xrange(1,18):
			del teams[0]

		betterstrat = ""
		stringDivision = stringDivision.replace(u'\xa0', ' ')
		betterstrat = soup.findAll("table",{"id": "ctl00_C_Standings_GridView1"})

		teams2 = betterstrat[0].findAll("tr")
		del teams2[0]

		for thing in teams2:
				teamName = thing.findChildren()[0].findChildren()[0].contents[0]
				teamURL = thing.findChildren()[0].findChildren()[0]['href']
				splitUrl = teamURL.split('/')

				if stringDivision.split(' ')[1] == "30":
					teamId = splitUrl[1]
				else:
					teamId = splitUrl[4]

				params = urllib.urlencode({"where":json.dumps({
				"teamId": teamId})})
				connection.request('GET', '/1/classes/SoccerCityTeams?%s' % params,'', {
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

				connection.request(call, '/1/classes/SoccerCityTeams%s' % objId, json.dumps({
				           "teamId": teamId,
				           "name": teamName,
				           "division": stringDivision
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
                print "There was a failure in teamListUpdate() for SoccerCity, could not resolve after 5 attempts, aborting..."
                break
            break
#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Soccer City site to obtain a list of all teams in (currently) facility 12 and stores the team data in the 'Teams' table of the Parse DB.
#
def teamListUpdate():
	connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
	connection.connect()
	divisions = []
	while len(divisions) == 0:
		url= 'http://www.soccercityutah.com/#!schedules/c1c2m'
		session = dryscrape.Session(base_url = url)
		session.set_timeout(30)
		session.visit(url)
		soup = BeautifulSoup(session.body())
		divisions = soup.findAll("a", {"target": "_blank"})
	del divisions[-1]
	del divisions[-1]
	del divisions[9]
	for division in divisions:
	  retries = 0
          while True:
            try:
		url= division['href']
		print "URL " + url
		stringDivision = ""
		if division.span is None:
			stringDivision = division.contents[0]
		else:
			stringDivision = division.span.contents[0]

		print stringDivision
		print "\n\n"
		session = dryscrape.Session(base_url = url)
		session.set_timeout(30)
		session.visit(url)
		soup = BeautifulSoup(session.body())
		teams = soup.findAll("a")
		if soup.find("a", {"href": "#stats"}) is not None:
			del teams[0]


		for x in xrange(1,18):
			del teams[0]

		betterstrat = ""
		stringDivision = stringDivision.replace(u'\xa0', ' ')
		betterstrat = soup.findAll("table",{"id": "ctl00_C_Standings_GridView1"})

		teams2 = betterstrat[0].findAll("tr")
		del teams2[0]

		for thing in teams2:
				teamName = thing.findChildren()[0].findChildren()[0].contents[0]
				teamURL = thing.findChildren()[0].findChildren()[0]['href']
				splitUrl = teamURL.split('/')

				if stringDivision.split(' ')[1] == "30":
					teamId = splitUrl[1]
				else:
					teamId = splitUrl[4]

				params = urllib.urlencode({"where":json.dumps({
				"teamId": teamId})})
				connection.request('GET', '/1/classes/SoccerCityTeams?%s' % params,'', {
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

				connection.request(call, '/1/classes/SoccerCityTeams%s' % objId, json.dumps({
				           "teamId": teamId,
				           "name": teamName,
				           "division": stringDivision
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
                print "There was a failure in teamListUpdate() for SoccerCity, could not resolve after 5 attempts, aborting..."
                break
            break

# 
# Updates the teams games from the soccer city website given their teamId and their teamName and puts them into parse table called SoccerCityGames
# 
# 
def gamesUpdate(teamId, teamName, session):
	session = session
	retries = 1
	while True:
		try:
			print "\ngamesUpdate, teamId: " + teamId
			print "gamesUpdate, name: " + teamName
			connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
			connection.connect()
			months = {
		        'Jan': '01',
		        'Feb': '02',
		        'Mar': '03',
		        'Apr': '04',
		        'May': '05',
		        'Jun': '06',
		        'Jul': '07',
		        'Aug': '08',
		        'Sep': '09',
		        'Oct': '10',
		        'Nov': '11',
		        'Dec': '12'
			}
			teamNameWithoutSpace = teamName.replace(u' ', '%20') 
			url="http://soccer-city-utah.ezleagues.ezfacility.com/teams/" + teamId + "/" + teamNameWithoutSpace + ".aspx?framed=1"
			print url
			session.visit(url)
			print "after url"
			soup = BeautifulSoup(session.body())
			gamesTable = soup.findAll("table", {"id": "ctl00_C_Schedule1_GridView1"})
			games = gamesTable[0].findAll("tr")
			del games[0]
			for game in games:
				gameData = game.findChildren()
				date = gameData[0].findChildren()[0].contents[0]
				homeTeam = gameData[2].findChildren()[0]['href'].split('/')[4]
				score = gameData[5].findChildren()[0].contents[0].split('v')
				homeTeamScore = ''
				awayTeamScore = ''
				if len(score) == 1:
					scores = score[0].split('-')
					homeTeamScore = scores[0].strip()
					awayTeamScore = scores[1].strip()

				awayTeam = gameData[7].findChildren()[0]['href'].split('/')[4]
				game_time = gameData[10].findChildren()[0].contents[0]
				location = gameData[12].findChildren()[0].contents[0]

				if game_time.strip() == "Complete":
					game_time = getGameTime(gameData[10].findChildren()[0]['href'], session)

				dateSplit = date.split("-")
				dateSplit2 = dateSplit[1].split(" ")
				day = dateSplit2[1]
				if len(dateSplit2[1]) == 1:
					day = "0" + dateSplit2[1]

				date = dateSplit[0] + " " + months.get(dateSplit2[0]) + "-" + day + "-15"+ " " + game_time
				params = urllib.urlencode({"where":json.dumps({
					"date": date,
					"field": location,
					"homeTeam": homeTeam,
					"awayTeam": awayTeam})
				})
				connection.request('GET', '/1/classes/SoccerCityGames?%s' % params,'', {
					"X-Parse-Application-Id": applicationId,
					"X-Parse-REST-API-Key": apiKey,
				})
				results = json.loads(connection.getresponse().read())
				objId = ''
				if results.values() == [[]]:
					call = 'POST'
				else:
					call = 'PUT'
					objId = '/%s' % results['results'][0]['objectId']

				connection.request(call, '/1/classes/SoccerCityGames%s' % objId, json.dumps({
					"homeTeamScore": homeTeamScore,
					"awayTeamScore": awayTeamScore,
					"homeTeam": homeTeam,
					"date":     date,
					"awayTeam": awayTeam,
					"field": location
					}), {
					"X-Parse-Application-Id": applicationId,
					"X-Parse-REST-API-Key": apiKey,
					"Content-Type": "application/json"
				})
				results = json.loads(connection.getresponse().read())
				if objId != '':
					teamGameLink(objId, homeTeam, awayTeam, connection)

		except Exception, e:
			print str(e)
			retries += 1
			if retries < 6:
				time.sleep(retries*retries*retries)
				print "Error retry %s..." % retries
				continue
			else:
				print "There was a failure in gameUpdate(), could not resolve after 5 attempts, aborting..."
				return
		break

def teamGameLink(gameId, homeTeam, awayTeam, connection):
    retries = 0
    while True:
      try:
	print "teamGameLink, gameId: " + gameId
	params = urllib.urlencode({"where":json.dumps({
		"teamId": homeTeam
	})})
	connection.request('GET', '/1/classes/SoccerCityTeams?%s' % params,'', {
		"X-Parse-Application-Id": applicationId,
		"X-Parse-REST-API-Key": apiKey,
	})
	results = json.loads(connection.getresponse().read())
	# Object doesn't exist, Continue for now.  Better handeling later
	if results.values() == [[]]:
		return
	else:
		homeTeamObjId = results['results'][0]['objectId']

	params = urllib.urlencode({"where":json.dumps({
		"teamId": awayTeam
	})})
	connection.request('GET', '/1/classes/SoccerCityTeams?%s' % params,'', {
		"X-Parse-Application-Id": applicationId,
		"X-Parse-REST-API-Key": apiKey,
	})

	results = json.loads(connection.getresponse().read())
	# Object doesn't exist, Continue for now.  Better handeling later
	if results.values() == [[]]:
		return
	else:
		awayTeamObjId = results['results'][0]['objectId']


	connection.request('PUT', '/1/classes/SoccerCityGames%s' % gameId, json.dumps({
        "awayTeamPointer": {
         "__op": "AddRelation",
         "objects": [
           {
             "__type": "Pointer",
             "className": "SoccerCityTeams",
             "objectId": awayTeamObjId
           }
         ]
       },
       "homeTeamPointer": {
         "__op": "AddRelation",
         "objects": [
           {
             "__type": "Pointer",
             "className": "SoccerCityTeams",
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
          print "There was a failure in teamGameLink() in SoccerCity, could not resolve after 5 attempts, aborting..."
          return
      break

def fullGameListUpdate():
	params = urllib.urlencode({"limit":1000})
	connection = httplib.HTTPSConnection('api.parse.com', 443)
	connection.connect()
	connection.request('GET', '/1/classes/SoccerCityTeams?%s' % params, '', {
	     "X-Parse-Application-Id": applicationId,
	     "X-Parse-REST-API-Key": apiKey,
	})
	results = json.loads(connection.getresponse().read())
	teams = results['results']
	session = dryscrape.Session()
        session.set_attribute('auto_load_images', False)
        session.set_timeout(20)
	for team in teams:
	  retries = 0
	  while True:
	    try:
		  gamesUpdate(team['teamId'], team['name'], session)

	    except Exception, e:
              print str(e)
              retries += 1
              if retries < 5:
                print "Error retry %s..." % retries
                time.sleep(5)
                continue
              else:
                print "There was a failure in fullGameListUpdate() in SoccerCity, could not resolve after 5 attempts, aborting..."
                break
            break

def getGameTime(url, session):
	retries = 0
	while True:
		try:
			#session = dryscrape.Session()
        		#session.set_attribute('auto_load_images', False)
        		#session.set_timeout(20)
			print "second url = " + url
                        session.visit(url)
                        soup2 = BeautifulSoup(session.body())
                        return soup2.find("span", {"id": "ctl00_C_lblGameTime"}).contents[0]
		except Exception, e:
			retries += 1
			if retries < 5:
				print "error retry %s..." % retries
				time.sleep(5)
				continue
			else:
				print "aborting...."
				break
			break


# teamListUpdate()
# fullGameListUpdate()
