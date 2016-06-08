import psycopg2, os
host = os.environ.get('POSTGRES_PORT_5432_TCP_ADDR')
connection = psycopg2.connect(host='postgres',database='Soccer_Games',user='dburnett',password='doug1')
cursor = connection.cursor()

facility = """CREATE TABLE IF NOT EXISTS facility(id SERIAL, name TEXT, address TEXT, city TEXT, state TEXT, zip INT, PRIMARY KEY(id));"""
favorites = """CREATE TABLE IF NOT EXISTS favorites(id BIGSERIAL, installationid TEXT, teamid TEXT, PRIMARY KEY(id));"""
fields = """CREATE TABLE IF NOT EXISTS fields(id SERIAL, address TEXT DEFAULT '', name TEXT, city TEXT, state CHARACTER varying(2), zip INT, PRIMARY KEY(id));"""
#fields = """CREATE TABLE IF NOT EXISTS fields(id SERIAL, address TEXT DEFAULT NOT NULL, name TEXT, city TEXT, state CHARACTER varying(2), zip INT, PRIMARY KEY(id));"""
games = """CREATE TABLE IF NOT EXISTS games(id SERIAL, awayteamscore INT, hometeamscore INT, updatedate TIMESTAMP without time zone, awayteam TEXT, hometeam TEXT, createddate TIMESTAMP without time zone, field INT, deleted_at TIMESTAMP without time zone, tournament TEXT DEFAULT NULL);"""
installation = """CREATE TABLE IF NOT EXISTS installation(id BIGSERIAL, installationid TEXT, devicetoken TEXT);"""
likes = """CREATE TABLE IF NOT EXISTS likes(id BIGSERIAL, installationid TEXT, videoid BIGINT);"""
teams = """CREATE TABLE IF NOT EXISTS teams(id SERIAL, division TEXT, name TEXT, updateddate TIMESTAMP without time zone, teamid TEXT, createddate TIMESTAMP without time zone, facility INT, deleted_at TIMESTAMP without time zone, PRIMARY KEY(id));"""
videos = """CREATE TABLE IF NOT EXISTS videos(id BIGSERIAL, likes INT DEFAULT 0, url TEXT, email TEXT, installation_id TEXT, PRIMARY KEY(id));"""

cursor.execute(facility)
cursor.execute(favorites)
cursor.execute(fields)
cursor.execute(games)
cursor.execute(installation)
cursor.execute(likes)
cursor.execute(teams)
cursor.execute(videos)

connection.commit()
