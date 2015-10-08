from lxml import html
import requests,json,httplib,urllib,sys,dryscrape,time

applicationId = "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv"
apiKey = "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b"


#Updates the linker to the games table for UYSA
def updateLinker(objId, awayTeamObjId, homeTeamObjId, connection):
	              connection.request('PUT', '/1/classes/UYSABoysGames%s' % objId, json.dumps({
                            "awayTeamPointer": {
                             "__op": "AddRelation",
                             "objects": [
                               {
                                 "__type": "Pointer",
                                 "className": "UYSABoysTeams",
                                 "objectId": awayTeamObjId
                               }
                             ]
                           },
                           "homeTeamPointer": {
                             "__op": "AddRelation",
                             "objects": [
                               {
                                 "__type": "Pointer",
                                 "className": "UYSABoysTeams",
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
#
# To be run BEFORE 'UYSABoysGamesUpdate()'
# Scrapes the UYSA site for the teamId, name, and division and puts it into the parse DB
#
#
def UYSABoysTeamUpdate():
	url = 'http://uysa.affinitysoccer.com/tour/public/info/accepted_list.asp?sessionguid=&Tournamentguid={DF7BDAE9-AED4-4836-9B48-1BBE491CA60A}'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	response = session.body()
	tree = html.fromstring(response)
	games = tree.xpath('//tbody/tr')
	connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
	connection.connect()
	retries = 0
        while True:
          try:
	    for game in games:
		  children = game.getchildren()
		  if len(children) < 8:
			  continue
		  else:
			  leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + children[1].getchildren()[0].getchildren()[0].attrib['href']
			  bracketSession = dryscrape.Session(base_url = leagueUrl)
			  bracketSession.visit(leagueUrl)
			  response = bracketSession.body()
			  tree = html.fromstring(response)
			  division = tree.xpath('//*[@id="tabs-1"]/div/table/tbody/tr[2]/td/table/tbody/tr[1]/td/a/div/table[1]/tbody/tr/td[1]')
			  teams = tree.xpath('//tbody/tr')
			  firstElement = 0
			  for team in teams:
				  if firstElement == 0:
					  firstElement = 1;
					  continue
				  else:
					  teamChildren = team.getchildren()
					  if len(teamChildren) != 5:
						  continue

					  else:
						  teamName = team.getchildren()[1].text
						  teamId = team.getchildren()[3].text
						  params = urllib.urlencode({"where":json.dumps({
							  "teamId": teamId})})
						  connection.request('GET', '/1/classes/UYSABoysTeams?%s' % params,'', {
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

						  connection.request(call, '/1/classes/UYSABoysTeams%s' % objId, json.dumps({
						               "teamId": teamId,
						               "name": teamName,
						               "division": division[0].text
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
	      print "There was a failure in UYSABoysTeamUpdate(), coult not resolve after 5 attempts, aborting..."
	      return
	  break


#
# To be run AFTER 'UYSABoysTeamUpdate()'
# Scrapes the UYSA site For all the games related to the teams in the division.
#
#
def UYSABoysGamesUpdate():
	months = {
            'January': '01',
            'February': '02',
            'March': '03',
            'April': '04',
            'May': '05',
            'June': '06',
            'July': '07',
            'August': '08',
            'September': '09',
            'October': '10',
            'November': '11',
            'December': '12',
	}
	url = 'http://uysa.affinitysoccer.com/tour/public/info/accepted_list.asp?sessionguid=&Tournamentguid={DF7BDAE9-AED4-4836-9B48-1BBE491CA60A}'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	response = session.body()
	tree = html.fromstring(response)
	games = tree.xpath('//tbody/tr')
	connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
	connection.connect()
        retries = 0
	while True:
	  try:
	    for game in games:
	  	  children = game.getchildren()
		  if len(children) < 8:
			  continue
		  else:
			print children[2].getchildren()[0].getchildren()[0].attrib['href']
			leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + children[2].getchildren()[0].getchildren()[0].attrib['href']
			bracketSession = dryscrape.Session(base_url = leagueUrl)
			bracketSession.visit(leagueUrl)
			response = bracketSession.body()
			tree = html.fromstring(response)
			teams = tree.xpath('//*[@id="tabs-1"]/div/table[4]/tbody/tr/td/table[1]/tbody/tr[2]/td/table/tbody/tr')
			firstElement = 0
			teamDicionary = {}
			for team in teams:
				if firstElement < 2:
					firstElement+=1
					continue


				teamDicionary[team.getchildren()[1].getchildren()[0].getchildren()[0].attrib['href'].split('&')[4][9:]] =  team.getchildren()[1].getchildren()[0].getchildren()[0].attrib['href'].split('&')[5][9:]

			tbodys = tree.xpath('//tbody')
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			del tbodys[0]
			centers = tree.xpath('//center')
			centersCount = -1
			for table in tbodys:
				if len(table.getchildren()) < 2:
					continue

				centersCount +=1
				noneElementRemoval = 0
				for bracket in table.getchildren():
					if noneElementRemoval < 1:
						noneElementRemoval = 1
						continue

					date = centers[centersCount]
					date = date.getchildren()[0].text[10:]
					arrayDate = date.split(',')
					game_time = bracket.getchildren()[2].getchildren()[0].text
					date = arrayDate[0][:3] + " " + months.get(arrayDate[1].split(' ')[2]) + "-" + arrayDate[1].split(' ')[3] + "-" + arrayDate[2][3:] + game_time[:-1]
					field = bracket.getchildren()[1].text
					homeTeam = teamDicionary.get(bracket.getchildren()[5].text)
					homeTeamScore = bracket.getchildren()[6].text
					awayTeam = teamDicionary.get(bracket.getchildren()[8].text)
					awayTeamScore = bracket.getchildren()[9].text
					if awayTeamScore is None or awayTeamScore.isspace():
						awayTeamScore = ""
					if awayTeamScore is None or homeTeamScore.isspace():
						homeTeamScore = ""

					params = urllib.urlencode({"where":json.dumps({
					    "teamId": homeTeam
					})})
					connection.request('GET', '/1/classes/UYSABoysTeams?%s' % params,'', {
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
					connection.request('GET', '/1/classes/UYSABoysTeams?%s' % params,'', {
					     "X-Parse-Application-Id": applicationId,
					     "X-Parse-REST-API-Key": apiKey,
					})

					results = json.loads(connection.getresponse().read())
					# Object doesn't exist, Continue for now.  Better handeling later
					if results.values() == [[]]:
					 continue
					else:
					 awayTeamObjId = results['results'][0]['objectId']



					params = urllib.urlencode({"where":json.dumps({
			            "date": date,
			            "field": field,
			            "homeTeam": homeTeam,
			            "awayTeam": awayTeam})})

			        connection.request('GET', '/1/classes/UYSABoysGames?%s' % params,'', {
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

			        connection.request(call, '/1/classes/UYSABoysGames%s' % objId, json.dumps({
			                    "date": date,
			                    "field": field,
			                    "homeTeam": homeTeam,
			                    "awayTeam": awayTeam,
			                    "homeTeamScore": homeTeamScore,
			                    "awayTeamScore": awayTeamScore
			                    }), {
			                    	"X-Parse-Application-Id": applicationId,
			                       	"X-Parse-REST-API-Key": apiKey,
			                       	"Content-Type": "application/json"
			                    })
			        results = json.loads(connection.getresponse().read())
			        print results
	                	updateLinker(objId, awayTeamObjId, homeTeamObjId,connection)
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
              print "There was a failure in UYSABoysGamesUpdate(), coult not resolve after 5 attempts, aborting..."
              return
          break

#
# Single method to combine all update methods for UYSA facility.
#
def UYSABoys_run():
  UYSABoysTeamUpdate()
  UYSABoysGamesUpdate()
