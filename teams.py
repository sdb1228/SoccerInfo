from lxml import html
import requests,json,httplib,urllib
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
