#!/usr/bin/python

import sys
from time import sleep
import shutil
import subprocess
import collections
import tempfile
import html
import json
from apiclient.discovery import build as gBuild
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import GoogleCredentials
import httplib2
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import file
from oauth2client import tools



basedir = "/home/httpd/ectnews/data"
filename = "%s/ga_rt_data.json" % basedir

profiles = {
	"TechNewsWorld" : {'id':'18832012', 'order':1 },
	"E-Commerce Times" : {'id':'21395753','order':2 },
	"LinuxInsider" : {'id':'21432507','order':3 },
	"CRM Buyer" : {'id':'21399353','order':4 },
	"ECT News" : {'id':'21432604','order':5 },
}

config_file = "/home/daniel/.aws/enn_realtime_settings.json"
redirect_uri  = "urn:ietf:wg:oauth:2.0:oob"
expires_at=0
token = ''
token_time = ''

#flow = OAuth2WebServerFlow({'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri, 'scope': 'https://www.googleapis.com/auth/analytics.readonly'});
#credentials = flow.step2_exchange(refresh_token)


def getSettings():
	try:
		c = open(config_file, 'r')
	except(IOError):
		print("Unable to read {}".format(config_file))
		sys.exit()
	else:
		try:
			config = json.load(c)
			c.close()
		except ValueError as e :
			print("Unable to parse json from config file: {}".format(e))
			sys.exit()
	return config

def getCredentials():
	credentials = GoogleCredentials(config['access_token'],config['client_id'],config['client_secret'],config['refresh_token'],expires_at,"https://accounts.google.com/o/oauth2/token",'test/1.0')
	http = httplib2.Http()
	#credentials.refresh(http)
	#print(credentials.expires_in)
	return credentials.authorize(http)
	
def getAnalytics(http):
	analytics = gBuild('analytics','v3',http=http)
	return analytics
	
def getStats(site):
	stat = data.realtime().get(
		ids			= "ga:" + site['id'],
		dimensions	= 'rt:pagePath,rt:country,rt:campaign',
		metrics		= "rt:activeUsers"
		).execute()
	
	countries = collections.defaultdict(int)
	referrers = {}
	pages = {}
	all_pages = []
	all_countries = []
	all_referrers = []
	for row in stat['rows']:
		#print(row)
		active_users = row[3] or 0
		path = html.escape(row[0])
		
		pages[path] = pages.get(path,0) + int(active_users)
		#countries[row[1]] = countries.setdefault(row[1], 0) + int(active_users)
		countries[row[1]] += int(active_users)
		referrers[row[2]] = referrers.setdefault(row[2], 0) + int(active_users)
	all_pages =  list(map(lambda x: {x[0]:x[1]}, sorted(pages.items(), key=lambda item: item[1], reverse=True)))
	for x in sorted(countries.items(), key=lambda item: item[1], reverse=True):
		all_countries.append({x[0]: x[1]})
	for x in sorted(referrers.items(), key=lambda item: item[1], reverse=True):
		all_referrers.append({x[0]: x[1]})
	ret = {
			'site': site,
			'activeUsers': active_users,
			'pages': all_pages,
			'countries': all_countries,
			'referers': all_referrers
	}
	return(ret)


def main():
	while True:
		try:
			all_data=[]
			tmp = tempfile.NamedTemporaryFile(delete=False)
			#print('tmp:', tmp, 'name:', tmp.name)
			for site in sorted(profiles.items(), key=lambda item: item[1]['order']):
				print('site:', site)
				all_data.append(getStats(profiles[site[0]]))
			tmp.write(str(json.dumps(all_data, indent=4)).encode('utf-8'))
		except IOError as e:
			print('IOError', e)
		finally:
			tmp.close
			shutil.move(tmp.name, filename)
		subprocess.call(["cat", filename])
		sleep(5)
		#break
config = getSettings()
credentials = getCredentials()
analytics = getAnalytics(credentials)
accounts = analytics.management().accounts().list().execute()
data = analytics.data()
#print(accounts)
main()


#print(profiles)