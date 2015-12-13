from bs4 import BeautifulSoup
import requests,json,httplib,sys,dryscrape,urllib,time, datetime, psycopg2

applicationId = "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv"
apiKey = "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b"

#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Soccer City site to obtain a list of all youth teams playing currently at Soccer City.
#
def youthTeamListUpdate():
	connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
  	cursor = connection.cursor()
	count = 0
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
	del divisions[-1]
	print len(divisions)
	for division in divisions:
			try:
				url= division['href']
				print "URL " + url
				if url == "http://www.facebook.com/soccercityutah":
					print "RETURNING"
					break

				stringDivision = ""
				if division.span is None:
					stringDivision = division.contents[0]
				else:
					stringDivision = division.span.contents[0]

				if stringDivision :
					pass
				print stringDivision + " %s" % count
				print "\n\n"
				if stringDivision == "Click Here!":
					continue

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
						teamId = splitUrl[4]

						selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility=5;""".format(str(teamId))
						cursor.execute(selectQuery)
						team = cursor.fetchone()

						if team is not None:
							print "Updating"
							updateQuery = """UPDATE "teams" SET  "name" = %s, "division" = %s, facility = %s WHERE "id" = %s ; """
							updateData = (teamName, stringDivision,5 ,team[-1])
							cursor.execute(updateQuery, updateData)
							connection.commit()
						else:
							print "Inserting"
							insertQuery = """INSERT INTO "teams" ("name", "division", "teamid", facility) VALUES (%s, %s, %s, %s);"""
							insertData = (teamName, stringDivision, teamId, 5)
							cursor.execute(insertQuery, insertData)

						connection.commit()

			except Exception, e:
				print str(e)
				continue
#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Soccer City site to obtain a list of all teams in (currently) facility 12 and stores the team data in the 'Teams' table of the Parse DB.
#
def teamListUpdate():
	connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
  	cursor = connection.cursor()
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
		if url == "http://www.facebook.com/soccercityutah":
			return
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
				teamId = splitUrl[4]

				selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility=5; """.format(str(teamId))
				cursor.execute(selectQuery)
				team = cursor.fetchone()

				if team is not None:
					print "Updating"
					updateQuery = """UPDATE "teams" SET  "name" = %s, "division" = %s, facility = %s WHERE "id" = %s ; """
					updateData = (teamName, stringDivision, 5,team[-2])
					print "RECORD " + teamName + " " + str(team[-2])
					cursor.execute(updateQuery, updateData)
				else:
					print "Inserting"
					insertQuery = """INSERT INTO "teams" ("name", "division", "teamid", facility) VALUES (%s, %s, %s, %s);"""
					insertData = (teamName, stringDivision, teamId, 5)
					print "RECORD " + teamName + " " + str(teamId)
					cursor.execute(insertQuery, insertData)

				connection.commit()

	    except Exception, e:
              print str(e)
              retries += 1
              if retries < 5:
                print "Error retry %s..." % retries
                time.sleep(5)
                continue
              else:
                print "There was a failure in teamListUpdate() for SoccerCity, could not resolve after 5 attempts, aborting..."
                break
            break

# 
# Updates the teams games from the soccer city website given their teamId and their teamName and puts them into parse table called SoccerCityGames
# 
# 
def gamesUpdate(teamId, teamName, session, cursor, connection):
	session = session
	retries = 1
	while True:
		try:
			print "\ngamesUpdate, teamId: " + teamId
			print "gamesUpdate, name: " + teamName
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
			errorMessage = soup.findAll("div", {"id": "ErrorMessage"})
			if not errorMessage:
				print "No Error"
			else:
				print errorMessage
				return
				
			gamesTable = soup.findAll("table", {"id": "ctl00_C_Schedule1_GridView1"})
			games = gamesTable[0].findAll("tr")
			del games[0]
			for game in games:
				gameData = game.findChildren()
				date = gameData[0].findChildren()[0].contents[0]
				homeTeam = gameData[2].findChildren()[0]['href'].split('/')[4]
				score = gameData[5].findChildren()[0].contents[0].split('v')
				homeTeamScore = None
				awayTeamScore = None
				if len(score) == 1:
					scores = score[0].split('-')
					homeTeamScore = scores[0].strip()
					awayTeamScore = scores[1].strip()
					if "Forfeit" in homeTeamScore: homeTeamScore = 0
					if "Forfeit" in awayTeamScore: awayTeamScore = 0

				awayTeam = gameData[7].findChildren()[0]['href'].split('/')[4]
				game_time = gameData[10].findChildren()[0].contents[0]
				location = gameData[12].findChildren()[0].contents[0]

				if game_time.strip() == "Complete" or game_time.strip() == "Result Pending":
					game_time = getGameTime(gameData[10].findChildren()[0]['href'], session)

				dateSplit = date.split("-")
				dateSplit2 = dateSplit[1].split(" ")
				day = dateSplit2[1]
				if len(dateSplit2[1]) == 1:
					day = "0" + dateSplit2[1]

				date = dateSplit[0] + " " + months.get(dateSplit2[0]) + "-" + day + "-15"+ " " + game_time

				neededDate = date[4:]
				month = int(neededDate[:2])
				day = neededDate[3] + neededDate[4]
				day = int(day)
				year = "20" + neededDate[6] + neededDate[7]
				year = int(year)
				gameTime = datetime.datetime.strptime(neededDate[9:], '%I:%M %p')
				saveDate = datetime.datetime(year, month, day, gameTime.hour, gameTime.minute)


				selectQuery = """SELECT id FROM "fields" WHERE name='{0}'; """.format(location)
				cursor.execute(selectQuery)
				DBfield = cursor.fetchone()
				if DBfield is None:
					print "Field doesn't match DB"
					print location
					continue
				DBfield = DBfield[0]

				gamesSelectQuery = """SELECT * FROM "games" WHERE awayTeam=%s AND homeTeam=%s AND gamesdatetime=%s AND field = %s;"""
				gamesSelectData = (awayTeam, homeTeam, saveDate, DBfield)
				cursor.execute(gamesSelectQuery, gamesSelectData)
				game = cursor.fetchone()
				if game is not None:
					print "Updating"
					updateQuery = """UPDATE "games" SET  "awayteam"=%s, "hometeam"=%s,"gamesdatetime"=%s, "field"=%s,"hometeamscore"=%s, "awayteamscore"=%s WHERE "id" = %s ; """
					updateData = (awayTeam, homeTeam, saveDate, DBfield, homeTeamScore, awayTeamScore, game[6])
					cursor.execute(updateQuery, updateData)
				else:
					print "Inserting"
					insertQuery = """INSERT INTO "games" ("awayteam", "hometeam", "gamesdatetime", "field", "hometeamscore", "awayteamscore") VALUES (%s, %s, %s, %s, %s, %s);"""
					insertData = (awayTeam, homeTeam, saveDate, DBfield, homeTeamScore, awayTeamScore)
					cursor.execute(insertQuery, insertData)

				connection.commit()

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

def fullGameListUpdate():
	connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
	cursor = connection.cursor()
	selectQuery = """SELECT * FROM "teams" WHERE facility=5; """
	cursor.execute(selectQuery)
	teams = cursor.fetchall()
	session = dryscrape.Session()
        session.set_attribute('auto_load_images', False)
        session.set_timeout(20)
	for team in teams:
	  retries = 0
	  while True:
	    try:
		  gamesUpdate(team[3], team[1], session, cursor, connection)

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

def lets_play_run():
	dryscrape.start_xvfb()
	youthTeamListUpdate()
	teamListUpdate()
	fullGameListUpdate()

