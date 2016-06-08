from lxml import html
import requests,json,httplib,urllib,time, psycopg2, datetime, os
from slack import draft_slack_message

is_test = os.environ.get('TEST') == "1"
if is_test:
  db_host = 'postgres'
else:
  db_host = 'localhost'

#
# Adds the team data for a given teamId.
# This method is called from teamListUpdate()
#
def teamUpdate(id, connection, cursor):
  print id
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

      selectQuery = """SELECT id FROM "teams" WHERE teamid='{0}' AND facility=6; """.format(str(id))
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
        continue
      else:
        draft_slack_message("Let's Play", "failed", str(e))
        print "There was a failure in teamListUpdate(), could not resolve after 5 attempts, aborting..."
        return
    break

#
# To be run before 'fullGameListUpdate()' to seed iterable data.
#
def teamListUpdate():
  connection = psycopg2.connect(host=db_host,database='Soccer_Games',user='dburnett',password='doug1')
  cursor = connection.cursor()

  page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams')
  tree = html.fromstring(page.text)
  # array of teams
  teamNames = tree.xpath("//a[contains(@href, '/facilities/12/teams/' )]")
  for team in teamNames:
    teamUpdate(team.attrib['href'].split('/')[-1], connection, cursor)

#
# To be run AFTER 'teamListUpdate()'
#
# teamId : Corresponds to the teamId that the team is referenced in the Let's Play href to view team data.
#
def gamesUpdate(teamId, connection, cursor):
  retries = 0
  updating = False
  rescheduled_ran = False
  while True:
    try:
      print teamId
      page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams/%s' % teamId)
      tree = html.fromstring(page.text)
      # array of games
      # this is the old version.  Keep here just incase
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

          if not rescheduled_ran:
            reschedule_calculator(games, teamId, cursor, connection)
            rescheduled_ran = True

          gamesSelectQuery = """SELECT id FROM "games" WHERE awayTeam=%s AND homeTeam=%s AND gamesdatetime=%s AND field = %s;"""
          gamesSelectData = (awayTeam, homeTeam, saveDate, DBfield)
          cursor.execute(gamesSelectQuery, gamesSelectData)
          game = cursor.fetchone()
          if game is not None:
            print "Updating"
            updateQuery = """UPDATE "games" SET  "awayteam"=%s, "hometeam"=%s,"gamesdatetime"=%s, "field"=%s,"hometeamscore"=%s, "awayteamscore"=%s WHERE "id" = %s ; """
            updateData = (awayTeam, homeTeam, saveDate, int(DBfield), homeTeamScore, awayTeamScore, game[0])
            cursor.execute(updateQuery, updateData)
            updating = True

          else:
            if updating:
              print "Team " + teamId + " Has a reschedule"
              selectQuery = """INSERT INTO "rescheduled_teams"  ("teamid") VALUES ('{0}'); """.format(teamId)
              cursor.execute(selectQuery)
              reschedule_calculator(games, teamId, cursor, connection)
              rescheduled_ran = False
              updating = False

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
        draft_slack_message("Let's Play", "failed", str(e))
        print "There was a failure in gameUpdate(), could not resolve after 5 attempts, aborting..."
        return
    break


# Calculates which games are reschedules and delete the ones that aren't correct
def reschedule_calculator(games, teamId, cursor, connection):
  ourGamesQuery = """SELECT f1.name AS field, f1.address AS address, games.hometeam AS hometeam, games.awayteam AS awayteam, games.gamesdatetime, games.hometeamscore, games.awayteamscore, games.id 
  FROM games
  INNER JOIN fields f1 ON f1.id=games.field
  WHERE games.awayteam='""" + teamId + """' OR games.hometeam='""" + teamId + """' ORDER BY games.gamesdatetime LIMIT 10;"""
  cursor.execute(ourGamesQuery)
  ourGames = cursor.fetchall()
  gameCopy = list(ourGames)
  deletingIndexs = []
  for idx, game in enumerate(ourGames):
    for theirGame in games:
        children = theirGame.getchildren()
        date = children[0].getchildren()[0].text
        field = children[1].text.strip()
        homeTeam = children[2].getchildren()[0]
        awayTeam = children[3].getchildren()[0]

        awayTeam = awayTeam.attrib['href'].split('/')[-1]
        homeTeam = homeTeam.attrib['href'].split('/')[-1]
        neededDate = date[4:]
        month = int(neededDate[:2])
        day = neededDate[3] + neededDate[4]
        day = int(day)
        year = "20" + neededDate[6] + neededDate[7]
        year = int(year)
        gameTime = datetime.datetime.strptime(neededDate[9:], '%I:%M %p')
        saveDate = datetime.datetime(year, month, day, gameTime.hour, gameTime.minute)
        if saveDate == game[4] and field == game[0] and homeTeam == game[2] and awayTeam[3]:
          gameCopy.remove(game)
          break


  print len(gameCopy)
  if gameCopy:
    for deleteGame in gameCopy:
      deleteQuery = """ DELETE FROM games WHERE id='{0}';""".format(deleteGame[-1])
      cursor.execute(deleteQuery)


#
# To be run AFTER 'teamListUpdate()'
#
def fullGameListUpdate():
  connection = psycopg2.connect(host=db_host,database='Soccer_Games',user='dburnett',password='doug1')
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
  teamListUpdate()
  fullGameListUpdate()
  draft_slack_message("Let's Play", "success")
