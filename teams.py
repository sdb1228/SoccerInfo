from lxml import html
import requests
import json,httplib
page = requests.get('http://www.letsplaysoccer.com/facilities/12/teams')
tree = html.fromstring(page.text)
# array of teams
teamNames = tree.xpath("//a[contains(@href, '/facilities/12/teams/' )]/text()")
# probably should move our key and id out to a variable at the top.  Later....
connection = httplib.HTTPSConnection('api.parse.com', 443)
connection.connect()
for team in teamNames:
	connection.request('POST', '/1/classes/Teams', json.dumps({
	       "name": team,
	     }), {
	       "X-Parse-Application-Id": "UnWG5wrHS2fIl7xpzxHqStks4ei4sc6p0plxUOGv",
	       "X-Parse-REST-API-Key": "g7Cj2NeORxfnKRXCHVv3ZcxxjRNpPU1RVuUxX19b",
	       "Content-Type": "application/json"
	     })
	results = json.loads(connection.getresponse().read())
	print results