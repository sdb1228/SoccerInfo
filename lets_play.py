from lxml import html
import requests,json,httplib,urllib,time, psycopg2, datetime

#
# Adds the team data for a given teamId.
# This method is called from teamListUpdate()
#
def teamUpdate(id, connection, cursor):
  print id
  # connection = httplib.HTTPSConnection('api.parse.com', 443, timeout=120)
  # connection.connect()
  retries = 0
  while True:
    try:
      teamPage = requests.get('http://www.letsplaysoccer.com/facilities/12/teams/%s' % id)
      tree = html.fromstring(teamPage.text)
      divisionHeader = tree.xpath("//*[@id='mainright']/h3")
      divisionHeader = divisionHeader[0].text.rstrip()
      divisionArray = divisionHeader.split(' ')
      if len(divisionArray) < 7:
        division = divisionArray[5]
      else: 
        division = divisionArray[5] + divisionArray[6]

      season = divisionArray[1]

      selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility=6; """.format(str(id))
      cursor.execute(selectQuery)
      team = cursor.fetchone()
      if team is not None:
        print "Updating"
        updateQuery = """UPDATE "teams" SET  "name" = %s, "division" = %s, "facility" = %s WHERE "id" = %s ; """
        updateData = (tree.xpath("//*[@id='mainright']/h1")[0].text.rstrip(), division, 6, team[-1])
        cursor.execute(updateQuery, updateData)
        connection.commit()
      else:
        print "Inserting"
        insertQuery = """INSERT INTO "teams" ("name", "division", "teamid", "facility") VALUES (%s, %s, %s, %s);"""
        insertData = (tree.xpath("//*[@id='mainright']/h1")[0].text.rstrip(), division, str(id), 6)
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
        print "There was a failure in teamListUpdate(), could not resolve after 5 attempts, aborting..."
        return
    break

#
# To be run before 'fullGameListUpdate()' to seed iterable data.
# Scrapes the Let's Play site to obtain a list of all teams in (currently) facility 12 and stores the team data in the 'Teams' table of the Parse DB.
#
def teamListUpdate():
  connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
  cursor = connection.cursor()
  page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams')
  tree = html.fromstring(page.text)
  # array of teams
  teamNames = tree.xpath("//a[contains(@href, '/facilities/12/teams/' )]")
  for team in teamNames:
    teamUpdate(team.attrib['href'].split('/')[-1], connection, cursor)

#
# To be run AFTER 'teamListUpdate()'
# Given a teamId, scrapes the Let's Play site for that teamId and stores a list of all games played by the corresponding team in the 'Games' table of the Parse DB.
#
# teamId : Corresponds to the teamId that the team is referenced in the Let's Play href to view team data.
#
def gamesUpdate(teamId, connection, cursor):
  retries = 0
  while True:
    try:
      print teamId
      page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams/%s' % teamId)
      tree = html.fromstring(page.text)
      # array of games
      # games = tree.xpath("//tr[td]")
      
      if len(tree.xpath("//table[1]")) == 0:
        print "No games for teams yet"
        break
      games = tree.xpath("//table[1]")[0].getchildren()

      # delete the title we don't need it
      del games[0]

      count = 0
      for game in games:
        children = game.getchildren()
        homeTeamScore = None
        awayTeamScore = None

        if len(children) != 7:
          date = children[0].getchildren()[0].text
          field = children[1].text.strip()
          homeTeam = children[2].getchildren()[0]
          awayTeam = children[3].getchildren()[0]
          
          awayTeam = awayTeam.attrib['href'].split('/')[-1]
          homeTeam = homeTeam.attrib['href'].split('/')[-1]

          selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility='{1}'; """.format(str(awayTeam), 6)
          cursor.execute(selectQuery)
          team = cursor.fetchone()
          if team is None:
            print "No Team Updating Now"
            teamUpdate(awayTeam, connection, cursor)

          selectQuery = """SELECT * FROM "teams" WHERE teamid='{0}' AND facility='{1}'; """.format(str(homeTeam), 6)
          cursor.execute(selectQuery)
          team = cursor.fetchone()
          if team is None:
            print "No Team Updating Now"
            teamUpdate(homeTeam, connection, cursor)

          score = "".join(children[4].text.split()).split("-") 
          if score[0]:
            homeTeamScore = int(score[0])
            awayTeamScore = int(score[1])

          neededDate = date[4:]
          month = int(neededDate[:2])
          day = neededDate[3] + neededDate[4]
          day = int(day)
          year = "20" + neededDate[6] + neededDate[7]
          year = int(year)
          gameTime = datetime.datetime.strptime(neededDate[9:], '%I:%M %p')
          saveDate = datetime.datetime(year, month, day, gameTime.hour, gameTime.minute)

          selectQuery = """SELECT id FROM "fields" WHERE name='{0}'; """.format(field)
          cursor.execute(selectQuery)
          DBfield = cursor.fetchone()
          if DBfield is None:
            print "Field doesn't match DB"
            print field
            continue
          DBfield = DBfield[0]
          

          gamesSelectQuery = """SELECT * FROM "games" WHERE awayTeam=%s AND homeTeam=%s AND gamesdatetime=%s AND field = %s;"""
          gamesSelectData = (awayTeam, homeTeam, saveDate, DBfield)
          cursor.execute(gamesSelectQuery, gamesSelectData)
          game = cursor.fetchone()
          if game is not None:
            print "Updating"
            updateQuery = """UPDATE "games" SET  "awayteam"=%s, "hometeam"=%s,"gamesdatetime"=%s, "field"=%s,"hometeamscore"=%s, "awayteamscore"=%s WHERE "id" = %s ; """
            updateData = (awayTeam, homeTeam, saveDate, int(DBfield), homeTeamScore, awayTeamScore, game[6])
            cursor.execute(updateQuery, updateData)
          else:
            print "Inserting"
            insertQuery = """INSERT INTO "games" ("awayteam", "hometeam", "gamesdatetime", "field", "hometeamscore", "awayteamscore") VALUES (%s, %s, %s, %s, %s, %s);"""
            insertData = (awayTeam, homeTeam, saveDate, int(DBfield), homeTeamScore, awayTeamScore)
            cursor.execute(insertQuery, insertData)

          connection.commit()
          count += 1

        else:
          print"\n\n\n\Standings\n"
    except Exception, e:
      print str(e)
      retries += 1
      if retries < 5:
        print "Error retry %s..." % retries
        time.sleep(5)
        continue
      else:
        print "There was a failure in gameUpdate(), could not resolve after 5 attempts, aborting..."
        return
    break

#
# To be run AFTER 'teamListUpdate()'
# Iterates across all teams stores in the 'Teams' table of the Parse DB and updates the 'Games' table according to the team's schedule.
#
def fullGameListUpdate():
  connection = psycopg2.connect(host='54.68.232.199',database='Soccer_Games',user='dburnett',password='doug1')
  cursor = connection.cursor()
  selectQuery = """SELECT * FROM "teams" WHERE facility=6; """
  cursor.execute(selectQuery)
  teams = cursor.fetchall()
  for team in teams:
    gamesUpdate(team[3], connection, cursor)

#
# Single method to combine all update methods for Let's Play facility.
#
def lets_play_run():
  # teamListUpdate()
  fullGameListUpdate()
  #gamesUpdate()
