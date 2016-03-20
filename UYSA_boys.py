from lxml import html
from bs4 import BeautifulSoup
import requests,json,httplib,urllib,sys,dryscrape,time,psycopg2, datetime
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
#
# To be run BEFORE 'UYSABoysGamesUpdate()'
# Scrapes the UYSA site for the teamId, name, and division and puts it into the parse DB
#
#
def UYSABoysTeamUpdate():
	connection = psycopg2.connect(host='localhost',database='Soccer_Games',user='dburnett',password='doug1')
	cursor = connection.cursor()
	url = 'http://uysa.affinitysoccer.com/tour/public/info/accepted_list.asp?sessionguid=&tournamentguid=714A94A4-B78D-421F-9EC7-0FCF25060908'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	soup = BeautifulSoup(session.body())
	bracketSession = dryscrape.Session()
	leauges = soup.findAll("a", href=True, text="Brackets")
	retries = 0
	try:
	    for league in leauges:
			leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + league['href']
			

			bracketSession.visit(leagueUrl)
			soup2 = BeautifulSoup(bracketSession.body())
			division = soup2.findAll("td", {"class": "title"})
			division = division[1].contents[0]
			table = soup2.findAll("table", {"class": "report"})
			rows = table[0].findAll("tr")
			# removing first row since its the title
			del rows[0]
			print leagueUrl
			for row in rows:
				rowContents = row.findChildren()
				teamName = rowContents[1].contents[0]
				teamId = rowContents[3].contents[0]

				selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility = '{1}'; """.format(teamId, 4)
				cursor.execute(selectQuery)
				team = cursor.fetchone()

				if team is not None:
					print "Updating " + teamName
					updateQuery = """UPDATE "teams" SET  "name" = %s, "division" = %s, "facility" = %s WHERE "id" = %s ; """
					updateData = (teamName, division,4, team[-1])
					cursor.execute(updateQuery, updateData)
					connection.commit()
				else:
					print "Inserting " + teamName
					insertQuery = """INSERT INTO "teams" ("name", "division", "teamid", "facility") VALUES (%s, %s, %s, %s);"""
					insertData = (teamName, division, teamId, 4)
					cursor.execute(insertQuery, insertData)

				connection.commit()
	except Exception, e:
		print str(e)
		return


#
# To be run AFTER 'UYSABoysTeamUpdate()'
# Scrapes the UYSA site For all the games related to the teams in the division.
#
#
def UYSABoysGamesUpdate():
	connection = psycopg2.connect(host='localhost',database='Soccer_Games',user='dburnett',password='doug1')
	cursor = connection.cursor()
	url = 'http://uysa.affinitysoccer.com/tour/public/info/accepted_list.asp?sessionguid=&tournamentguid=714A94A4-B78D-421F-9EC7-0FCF25060908'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	schedulesAndLeaguesBody = BeautifulSoup(session.body())
	schedules = schedulesAndLeaguesBody.findAll("a", href=True, text="Schedule & Results")
	retries = 0
	scheduleSession = dryscrape.Session()
	teamsHash = {}

	try:
		for schedule in schedules:
			leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + schedule['href']
			print leagueUrl + "\n\n\n\n\n\n\n"
			scheduleSession.visit(leagueUrl)
			schedulesBody = BeautifulSoup(scheduleSession.body())
			division = schedulesBody.findAll("span", {"class" : "title"})[0].contents[0][17:].rstrip()
			if not allDatesHaveGames(schedulesBody):
				print "More dates then actual game containers"
				continue

			dates = schedulesBody.findAll("center", {"xmlns:msxsl": "urn:schemas-microsoft-com:xslt"})
			gamesContainers = schedulesBody.findAll("table", {"xmlns:msxsl":"urn:schemas-microsoft-com:xslt"})
			# GamesContainers first item is the teams table with all the team names and ids
			teamsTableBody = gamesContainers[0].findAll("table", {"cellspacing" : "2"})
			teamsTableRows = teamsTableBody[0].findAll("tr")
			# Delete first two rows of teams table due to they are unneeded
			del teamsTableRows[0]
			del teamsTableRows[0]
			if not addTeamIfMissing(teamsTableRows, connection, cursor, division):
				print "A team was not added correctly"
				continue

			teamsHash = getTeamHash(teamsTableRows)
			centersCount = 0
			tableCount = 0

			del gamesContainers[0]
			for table in gamesContainers:
				print "Table " + str(tableCount) + " Being Parsed"
				games = parseTable(table, dates[tableCount], teamsHash)
				if games is None:
					print "Games table could not be parsed correctly"
					continue

				err = insertOrUpdateGames(games, cursor, connection)
				tableCount += 1
				
	except Exception, e:
		print str(e)
		return

#
# Will determine if the dates and the games table counts match
#
def allDatesHaveGames(schedulesBody):
	dates = schedulesBody.findAll("center", {"xmlns:msxsl": "urn:schemas-microsoft-com:xslt"})
	gamesContainers = schedulesBody.findAll("table", {"xmlns:msxsl":"urn:schemas-microsoft-com:xslt"})
	if len(dates) == (len(gamesContainers)-1):
		return True
	return False

#
# Will add a team from the teams table if it doesn't already exist in database
#
def addTeamIfMissing(teamsTableRows, connection, cursor, division):
	for tr in teamsTableRows:
		team = parseTeamFromRow(tr)
		if teamMissing(connection, cursor, team.get("teamId")):
			insertTeam(connection, cursor, team.get("teamId"), 4, division, team.get("name"))
			continue

	return True
#
# Wil return true if the team is missing.  False otherwise
#
def teamMissing(connection, cursor, teamId):
	selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility = '{1}'; """.format(teamId, 4)
	cursor.execute(selectQuery)
	team = cursor.fetchone()
	return team is None

#
# Returns a hash of all the teams
#
def getTeamHash(teamsTableRows):
	teamsHash = {}
	for tr in teamsTableRows:
		tableLabel = tr.findChildren()[6].contents[0]
		teamsHash[tableLabel] = parseTeamFromRow(tr)

	return teamsHash

#
# Prints the teams row
#
def parseTeamFromRow(teamRow):
	team = {}
	teamId = teamRow.findChildren()[5]['href'].split("teamcode")[-1]
	teamId = teamId.replace("=", "")
	teamId = teamId[:16]
	name = teamRow.findChildren()[5].contents[1]
	name = name[3:]
	tableLabel = teamRow.findChildren()[6].contents[0]
	print "Table Lable: " + tableLabel + " TeamId: " + teamId + " TeamName: " + name
	team["teamId"] = teamId
	team["name"] = name
	return team
#
# Will parse the game table and return back all games
#
def parseTable(gamesTable, date, teamsHash):
	games = []
	rows = gamesTable.findAll("tr")
	del rows[0]
	for gameRow in rows:
		field = parseField(gameRow.findChildren()[1].contents[0])
		if field is None:
			print "Field could not be parsed correctly"
			continue
		saveDate = parseDate(date, gameRow.findChildren()[2].findChildren()[0].contents[0])
		if saveDate is None:
			print "Date could not be parsed correctly"
			continue
		teams = parseTeams(gameRow, teamsHash)
		if teams is None:
			print "Could not parse the teams correctly"
			continue
		scores = parseScores(gameRow)
		if scores is None:
			print "Scores could not be parsed correctly"
			continue

		games.append({"homeTeam": teams.get("homeTeam"), 
				"awayTeam": teams.get("awayTeam"), 
				"homeTeamScore": scores.get("homeTeamScore"), 
				"awayTeamScore": scores.get("awayTeamScore"), 
				"dateTime": saveDate, 
				"field": field})
	return games
		

#
# Makes the field look pretty
#
def parseField(field):
	field = field.lstrip()
	field = field.rstrip()
	if field == "TBD":
		return None
	return field


#
# Will update the game if we have it otherwise insert it
#
def insertOrUpdateGames(games, cursor, connection):
	for game in games:
		if gameExists(game, cursor, connection):
			continue
		else:
			insertGame(game, cursor, connection)


#
# Will update game if it exists and return true otherwise return false
#
def gameExists(game, cursor, connection):
	field = getFieldId(game.get("field"), cursor, connection)
	gamesSelectQuery = """SELECT * FROM "games" WHERE awayTeam=%s AND homeTeam=%s AND gamesdatetime=%s AND field = %s"""
	gamesSelectData = (game.get("awayTeam").get("teamId"), game.get("homeTeam").get("teamId"), game.get("dateTime"), field)
	cursor.execute(gamesSelectQuery, gamesSelectData)
	databaseGame = cursor.fetchone()
	if databaseGame is not None:
		print "Updating"
		updateQuery = """UPDATE "games" SET  "awayteam"=%s, "hometeam"=%s,"gamesdatetime"=%s, "field"=%s,"hometeamscore"=%s, "awayteamscore"=%s WHERE "id" = %s ; """
		updateData = (game.get("awayTeam").get("teamId"), game.get("homeTeam").get("teamId"), game.get("dateTime"), field, game.get("homeTeamScore"), game.get("awayTeamScore"), databaseGame[6])
		cursor.execute(updateQuery, updateData)
		connection.commit()
		return True
	return False

	
def insertGame(game, cursor, connection):
	field = getFieldId(game.get("field"), cursor, connection)
	print "Inserting"
	insertQuery = """INSERT INTO "games" ("awayteam", "hometeam", "gamesdatetime", "field", "hometeamscore", "awayteamscore") VALUES (%s, %s, %s, %s, %s, %s);"""
	insertData = (game.get("awayTeam").get("teamId"), game.get("homeTeam").get("teamId"), game.get("dateTime"), field, game.get("homeTeamScore"), game.get("awayTeamScore"))
	cursor.execute(insertQuery, insertData)
	connection.commit()
#
# Will get field Id if we have it, otherwise add it if we don't
#
def getFieldId(field, cursor, connection):
	selectQuery = """SELECT id FROM "fields" WHERE name LIKE '{0}%'; """.format(field)
	cursor.execute(selectQuery)
	DBfield = cursor.fetchone()
	if DBfield is None:
		print "Field doesn't match DB"
		print field
		insertQuery = """INSERT INTO "fields" ("name") VALUES ('{0}');""".format(field)
		cursor.execute(insertQuery)
		connection.commit()
		print "Inserted missing field"
		field = field.rstrip()
		field = field.lstrip()
		print field
		selectQuery = """SELECT id FROM "fields" WHERE name LIKE '{0}%'; """.format(str(field))
		cursor.execute(selectQuery)
		DBfield = cursor.fetchone()

	return DBfield[0]

#
# Will parse and validate the scores on the game row
#
def parseScores(gameRow):
	homeTeamScore = gameRow.findChildren()[8].contents[0]
	awayTeamScore = gameRow.findChildren()[-1].contents[0]
	homeTeamScore = "".join(homeTeamScore.split())
	awayTeamScore = "".join(awayTeamScore.split())
	if len(homeTeamScore) == 0 or len(awayTeamScore) == 0:
		homeTeamScore = None
		awayTeamScore = None
	else:
		awayTeamScore = int(awayTeamScore)
		homeTeamScore = int(homeTeamScore)

	return {"homeTeamScore": homeTeamScore, "awayTeamScore": awayTeamScore}

#
# Will parse the teams and put them into a hash
#
def parseTeams(gameRow, teamsHash):
	homeTeam = teamsHash.get(gameRow.findChildren()[5].findChildren()[0].contents[0].split(" ")[0])
	awayTeam = teamsHash.get(gameRow.findChildren()[5].findChildren()[0].contents[0].split(" ")[2])
	if not homeTeam or not awayTeam:
		print gameRow.findChildren()[5].findChildren()[0].contents[0].split(" ")
		print "ERROR NO TEAMS"
		return None
	return {"homeTeam": homeTeam, "awayTeam": awayTeam}
	
#
# Makes the date look pretty
#
def parseDate(date, time):
	date = date.findChildren()[0].contents[0][10:]
	arrayDate = date.split(',')
	date = arrayDate[0][:3] + " " + months.get(arrayDate[1].split(' ')[2]) + "-" + arrayDate[1].split(' ')[3] + "-" + arrayDate[2][3:] + time[:-1]

	neededDate = date[4:]
	month = int(neededDate[:2])
	day = neededDate[3] + neededDate[4]
	day = int(day)
	year = "20" + neededDate[6] + neededDate[7]
	year = int(year)
	cleanDate = neededDate[9:]
	cleanDate = cleanDate.lstrip()
	cleanDate = cleanDate.rstrip()
	cleanDate = cleanDate.replace("&bbsp", "")
	cleanDate = cleanDate.replace("&sbsp", "")
	cleanDate = cleanDate.replace("sbsp;", "")
	cleanDate = cleanDate.replace("bbsp;", "")
	gameTime = datetime.datetime.strptime(cleanDate, '%I:%M %p')
	saveDate = datetime.datetime(year, month, day, gameTime.hour, gameTime.minute)
	return saveDate
#
# Insert team into database
#
def insertTeam(connection, cursor, teamId, facility, division, name):
	print "Inserting " + name
	insertQuery = """INSERT INTO "teams" ("name", "division", "teamid", "facility") VALUES (%s, %s, %s, %s);"""
	insertData = (name, division, teamId, facility)
	cursor.execute(insertQuery, insertData)

# 
# Single method to combine all update methods for UYSA facility.
#
def UYSABoys_run():
	dryscrape.start_xvfb()
	UYSABoysTeamUpdate()
	UYSABoysGamesUpdate()
