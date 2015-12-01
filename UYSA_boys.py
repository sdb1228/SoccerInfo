from lxml import html
from bs4 import BeautifulSoup
import requests,json,httplib,urllib,sys,dryscrape,time,psycopg2, datetime

#
# To be run BEFORE 'UYSABoysGamesUpdate()'
# Scrapes the UYSA site for the teamId, name, and division and puts it into the parse DB
#
#
def UYSABoysTeamUpdate():
	connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
	cursor = connection.cursor()
	url = 'http://uysa.affinitysoccer.com/tour/public/info/accepted_list.asp?sessionguid=&Tournamentguid={DF7BDAE9-AED4-4836-9B48-1BBE491CA60A}'
	session = dryscrape.Session(base_url = url)
	session.visit(url)
	soup = BeautifulSoup(session.body())
	leauges = soup.findAll("a", href=True, text="Brackets")
	retries = 0
        while True:
          try:
	    for league in leauges:
			leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + league['href']
			bracketSession = dryscrape.Session(base_url = leagueUrl)
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
	connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
	cursor = connection.cursor()
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
	soup = BeautifulSoup(session.body())
	schedules = soup.findAll("a", href=True, text="Schedule & Results")
	retries = 0
	consoleHelp = 0

	while True:
	  try:
	    for schedule in schedules:
			leagueUrl = "http://uysa.affinitysoccer.com/tour/public/info/" + schedule['href']
			consoleHelp += 1
			print leagueUrl + " " + str(consoleHelp) + "\n\n\n\n\n\n\n"
			bracketSession = dryscrape.Session(base_url = leagueUrl)
			bracketSession.visit(leagueUrl)
			soup2 = BeautifulSoup(bracketSession.body())
			centers = soup2.findAll("center", {"xmlns:msxsl": "urn:schemas-microsoft-com:xslt"})
			tables = soup2.findAll("table", {"xmlns:msxsl":"urn:schemas-microsoft-com:xslt"})
			teamDicionary = {}
			tbodys = tables[0].findAll("table", {"cellspacing" : "2"})
			trs = tbodys[0].findAll("tr")
			centersCount = 0
			del trs[0]
			del trs[0]
			for tr in trs:
				teamId = tr.findChildren()[5]['href'].split("teamcode")[-1]
				teamId = teamId.replace("=", "")
				teamId = teamId[:16]
				name = tr.findChildren()[5].contents[1]
				name = name[3:]
				group = tr.findChildren()[6].contents[0]
				teamDicionary[group] = teamId

			del tables[0]

			tableCount = 0
			for table in tables:
				tableCount += 1
				print "Table " + str(tableCount) + " Being Parsed"
				trs = table.findAll("tr")
				# delete header of table
				del trs[0]
				for tr in trs:
					field = tr.findChildren()[1].contents[0]
					field = field.lstrip()
					field = field.rstrip()
					date = centers[centersCount]
					date = date.findChildren()[0].contents[0][10:]
					arrayDate = date.split(',')
					game_time = tr.findChildren()[2].findChildren()[0].contents[0]
					date = arrayDate[0][:3] + " " + months.get(arrayDate[1].split(' ')[2]) + "-" + arrayDate[1].split(' ')[3] + "-" + arrayDate[2][3:] + game_time[:-1]
					# We should do some smarter parsing here that if the game is TBD Maybe still store the date and on the phone do more magic
					# Until then this will have to do
					if field == "TBD":
						continue

					neededDate = date[4:]
					month = int(neededDate[:2])
					day = neededDate[3] + neededDate[4]
					day = int(day)
					year = "20" + neededDate[6] + neededDate[7]
					year = int(year)
					gameTime = datetime.datetime.strptime(neededDate[9:], '%I:%M %p')
					saveDate = datetime.datetime(year, month, day, gameTime.hour, gameTime.minute)


					awayVHome = tr.findChildren()[5].findChildren()[0].contents[0].split(" ")
					homeTeam = teamDicionary.get(awayVHome[0])
					awayTeam = teamDicionary.get(awayVHome[2])
					if not homeTeam or not awayTeam:
						print awayVHome[0]
						print awayVHome[2]
						print "ERROR NO TEAMS"
						return

					homeTeamScore = None
					awayTeamScore = None
					
					extraCell = False
					specialCell = False
					
					if len(tr.findChildren()[8].findChildren()) == 1:
						extraCell = True
						if len(tr.findChildren()[8].findChildren()[0].contents) == 0:
							specialCell = True
							extraCell = False
							homeTeamScore = "0"
							awayTeamScore = "1"
						else:
							homeTeamScore = tr.findChildren()[8].findChildren()[0].contents[0]
					else:
						if len(tr.findChildren()[8].contents) == 0:
							specialCell = True
							extraCell = False
							homeTeamScore = "0"
							awayTeamScore = "1"
						else:
							homeTeamScore = tr.findChildren()[8].contents[0]


					if specialCell:
						homeTeamScore = "0"
						awayTeamScore = "1"
						
					elif extraCell:
						homeTeamScoreDisq = homeTeamScore.strip() == "D" or homeTeamScore.strip() == "F"
						if homeTeamScoreDisq:
							homeTeamScore = "1"
							awayTeamScore = "0"

						elif len(tr.findChildren()[12].findChildren()) == 1:
							awayTeamScore = tr.findChildren()[12].findChildren()[0].contents[0]
						else:
							awayTeamScore = tr.findChildren()[12].contents[0]
					else:
						if len(tr.findChildren()[11].findChildren()) == 1:
							awayTeamScore = tr.findChildren()[11].findChildren()[0].contents[0]
						else:
							awayTeamScore = tr.findChildren()[11].contents[0]
					
					homeTeamScore = homeTeamScore.strip()
					awayTeamScore = awayTeamScore.strip()
					awayTeamScoreDisq = awayTeamScore == "D" or awayTeamScore == "F"
					if awayTeamScoreDisq:
						homeTeamScore = 1
						awayTeamScore = 0

					if homeTeamScore == "CS" or awayTeamScore == "CS":
						homeTeamScore = None
						awayTeamScore = None
					if not homeTeamScore:
						homeTeamScore = None
					else:
						homeTeamScore = int(homeTeamScore)	
					if not awayTeamScore:
						awayTeamScore = None
					else:
						awayTeamScore = int(awayTeamScore)




					selectQuery = """SELECT id FROM "fields" WHERE name LIKE '{0}%'; """.format(field)
					cursor.execute(selectQuery)
					DBfield = cursor.fetchone()
					if DBfield is None:
						print "Field doesn't match DB"
						print field
						insertQuery = """INSERT INTO "fields" ("name") VALUES ('{0}');""".format(field)
						cursor.execute(insertQuery)
						print "Inserted missing field"
						field = field.rstrip()
						field = field.lstrip()
						print field
						selectQuery = """SELECT id FROM "fields" WHERE name LIKE '{0}%'; """.format(str(field))
						cursor.execute(selectQuery)
						DBfield = cursor.fetchone()
					
					DBfield = DBfield[0]

					gamesSelectQuery = """SELECT * FROM "games" WHERE awayTeam=%s AND homeTeam=%s AND gamesdatetime=%s AND field = %s"""
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

				centersCount += 1
	  except Exception, e:
            print str(e)
            retries += 1
            if retries < 5:
              print "Error retry %s..." % retries
              time.sleep(5)
              continue
            else:
              print "There was a failure in UYSABoysGamesUpdate(), coult not resolve after 5 attempts, aborting..."
              return
          break

#
# Single method to combine all update methods for UYSA facility.
#
# def UYSABoys_run():
UYSABoysTeamUpdate()
# UYSABoysGamesUpdate()
