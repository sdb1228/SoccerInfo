from lxml import html
import requests,json,httplib,urllib
def teamListUpdate():
  page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams')
  tree = html.fromstring(page.text)
  # array of teams
  teamNames = tree.xpath("//a[contains(@href, '/facilities/12/teams/' )]")
  # probably should move our key and id out to a variable at the top.  Later....
  connection = httplib.HTTPSConnection('api.parse.com', 443)
  connection.connect()
  for team in teamNames:
    params = urllib.urlencode({"where":json.dumps({
      "teamId": team.attrib['href'].split('/')[-1]})})
    connection.request('GET', '/1/classes/Teams?%s' % params,'', {
           "X-Parse-Application-Id": "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv",
           "X-Parse-REST-API-Key": "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b",
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

    connection.request(call, '/1/classes/Teams%s' % objId, json.dumps({
                 "teamId": team.attrib['href'].split('/')[-1],
                 "name": team.text,
               }), {
                 "X-Parse-Application-Id": "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv",
                 "X-Parse-REST-API-Key": "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b",
                 "Content-Type": "application/json"
               })
    results = json.loads(connection.getresponse().read())
    print results

def teamsUpdate():
  page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams/220973')
  tree = html.fromstring(page.text)
  # array of teams
  games = tree.xpath("//tr[td]")
  for game in games:
    children = game.getchildren()
    if len(children) != 7:
      date = children[0].getchildren()[0].text
      field = children[1].text
      homeTeam = children[2].getchildren()[0]
      awayTeam = children[3].getchildren()[0]
      if not awayTeam.getchildren() and not homeTeam.getchildren():
        awayTeam = awayTeam.text
        homeTeam = homeTeam.text
      elif not awayTeam.getchildren():
        homeTeam = homeTeam.getchildren()[0].text
        awayTeam = awayTeam.text
      else:
        awayTeam = awayTeam.getchildren()[0].text
        homeTeam = homeTeam.text

      score = "".join(children[4].text.split()).split("-") 
      if score[0]:
        homeTeamScore = score[0]
        awayTeamScore = score[1]
      else:
        homeTeamScore = ""
        awayTeamScore = ""

      connection = httplib.HTTPSConnection('api.parse.com', 443)
      connection.connect()
      connection.request('POST', '/1/classes/Games', json.dumps({
                   "date": date,
                   "field": field,
                   "homeTeam": homeTeam,
                   "awayTeam": awayTeam,
                   "homeTeamScore": homeTeamScore,
                   "awayTeamScore": awayTeamScore
                 }), {
                   "X-Parse-Application-Id": "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv",
                   "X-Parse-REST-API-Key": "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b",
                   "Content-Type": "application/json"
                 })
      results = json.loads(connection.getresponse().read())
      print results
    else:
      print"\n\n\n\Standings\n"
