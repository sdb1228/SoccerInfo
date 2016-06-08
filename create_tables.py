import psycopg2, os
host = os.environ.get('POSTGRES_PORT_5432_TCP_ADDR')
connection = psycopg2.connect(host='postgres',database='Soccer_Games',user='dburnett',password='doug1')
cursor = connection.cursor()

facility = """CREATE TABLE IF NOT EXISTS facility(name TEXT, address TEXT, city TEXT, state TEXT, zip INT, id SERIAL, PRIMARY KEY(id));"""
favorites = """CREATE TABLE IF NOT EXISTS favorites(installationid TEXT, id BIGSERIAL, teamid TEXT, PRIMARY KEY(id));"""
fields = """CREATE TABLE IF NOT EXISTS fields(address TEXT DEFAULT '', name TEXT, city TEXT, state CHARACTER varying(2), zip INT, id SERIAL, PRIMARY KEY(id));"""
games = """CREATE TABLE IF NOT EXISTS games(awayteamscore INT, hometeamscore INT, updatedate TIMESTAMP without time zone, awayteam TEXT, hometeam TEXT, createddate TIMESTAMP without time zone, id SERIAL, gamesdatetime TIMESTAMP without time zone, field INT, deleted_at TIMESTAMP without time zone, tournament TEXT DEFAULT NULL);"""
installation = """CREATE TABLE IF NOT EXISTS installation(installationid TEXT, id BIGSERIAL, devicetoken TEXT);"""
likes = """CREATE TABLE IF NOT EXISTS likes(id BIGSERIAL, installationid TEXT, videoid BIGINT);"""
teams = """CREATE TABLE IF NOT EXISTS teams(division TEXT, name TEXT, updateddate TIMESTAMP without time zone, teamid TEXT, createddate TIMESTAMP without time zone, id SERIAL, facility INT, deleted_at TIMESTAMP without time zone, PRIMARY KEY(id));"""
videos = """CREATE TABLE IF NOT EXISTS videos(id BIGSERIAL, likes INT DEFAULT 0, url TEXT, email TEXT, installation_id TEXT, PRIMARY KEY(id));"""
resched = """CREATE TABLE IF NOT EXISTS rescheduled_teams(teamid TEXT, id SERIAL);"""

field_insert1 = """INSERT INTO fields(name) VALUES('Gardner Village Left');"""
field_insert2 = """INSERT INTO fields(name) VALUES('Gardner Village Right');"""
field_insert3 = """INSERT INTO fields(name) VALUES('Salt Lake');"""

cursor.execute(facility)
cursor.execute(favorites)
cursor.execute(fields)
cursor.execute(games)
cursor.execute(installation)
cursor.execute(likes)
cursor.execute(teams)
cursor.execute(videos)
cursor.execute(resched)
cursor.execute(field_insert1)
cursor.execute(field_insert2)
cursor.execute(field_insert3)

connection.commit()
