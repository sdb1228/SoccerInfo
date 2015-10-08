from bs4 import BeautifulSoup
import requests,json,httplib,sys,dryscrape,urllib,time, datetime

applicationId = "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv"
apiKey = "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b"
#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Let's Play site to obtain a list of all teams in (currently) facility 12 and stores the team data in the 'Teams' table of the Parse DB.
#
def teamListUpdate():
	connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
	connection.connect()
	url= 'http://www.soccercityutah.com/#!schedules/c1c2m'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	soup = BeautifulSoup(session.body())
	divisions = soup.findAll("a", {"target": "_blank"})
	del divisions[-1]
	del divisions[-1]
	del divisions[9]
	for division in divisions:
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
		session.visit(url)
		soup = BeautifulSoup(session.body())
		teams = soup.findAll("a")
		if soup.find("a", {"href": "#stats"}) is not None:
			del teams[0]

		for x in xrange(1,18):
			del teams[0]

		stringDivision = stringDivision.replace(u'\xa0', ' ')
		if stringDivision.split(' ')[1] == "30":
			for x in xrange(1,17):
				del teams[0]

		for team in teams:
			if team.has_attr('name'):
				if team['name'] == "schedule":
					break
			else:
				teamName = team.contents[0]
				teamURL = team['href']
				print teamURL
				splitUrl = teamURL.split('/')
				teamId = ""
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


# 
# Updates the teams games from the soccer city website given their teamId and their teamName and puts them into parse table called SoccerCityGames
# 
# 
def gamesUpdate(teamId, teamName):
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
	url="http://soccer-city-utah.ezleagues.ezfacility.com/teams/" + teamId + "/" + teamName + ".aspx?framed=1"
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	soup = BeautifulSoup(session.body())
	gamesTable = soup.findAll("table", {"id": "ctl00_C_Schedule1_GridView1"})
	games = gamesTable[0].findAll("tr")
	del games[0]
	for game in games:
		gameData = game.findChildren()
		date = gameData[0].findChildren()[0].contents[0]
		homeTeam = gameData[2].findChildren()[0].contents[0]
		score = gameData[5].findChildren()[0].contents[0].split('v')
		homeTeamScore = ''
		awayTeamScore = ''
		if len(score) == 1:
			scores = score[0].split('-')
			homeTeamScore = scores[0].strip()
			awayTeamScore = scores[1].strip()

		awayTeam = gameData[7].findChildren()[0].contents[0]
		time = gameData[10].findChildren()[0].contents[0]
		location = gameData[12].findChildren()[0].contents[0]

		if time.strip() == "Complete":
			session2 = dryscrape.Session(base_url = gameData[10].findChildren()[0]['href'])
			session2.visit(gameData[10].findChildren()[0]['href'])
			soup2 = BeautifulSoup(session2.body())
			time = soup2.find("span", {"id": "ctl00_C_lblGameTime"}).contents[0]

		dateSplit = date.split("-")
		dateSplit2 = dateSplit[1].split(" ")
		day = dateSplit2[1]
		if len(dateSplit2[1]) == 1:
			day = "0" + dateSplit2[1]

		date = dateSplit[0] + " " + months.get(dateSplit2[0]) + "-" + day + "-15"+ " " + time

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

		if results.values() == [[]]:
			call = 'POST'
			objId = ''
		# Match exists, PUT to update existing match.
		else:
			call = 'PUT'
			objId = '/%s' % results['results'][0]['objectId']

		connection.request(call, '/1/classes/SoccerCityGames%s' % objId, json.dumps({
			"homeTeamScore": homeTeamScore,
			"awayTeamScore": awayTeamScore,
			"homeTeam": homeTeam,
			"awayTeam": awayTeam,
			"field": location
			}), {
			"X-Parse-Application-Id": applicationId,
			"X-Parse-REST-API-Key": apiKey,
			"Content-Type": "application/json"
		})
		results = json.loads(connection.getresponse().read())
		print results


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
	for team in teams:
		gamesUpdate(team['teamId'], team['name'])



