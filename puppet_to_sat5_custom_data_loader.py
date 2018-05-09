#!/usr/bin/python

#########################################################################
# Author: Steven S. Boger (sboger@costco.com)
# Created: Dec 22  2015
#
# Version: 1.0 - initial version
# Version: 1.1 - verbose define added
# Version: 1.2 - multiple hostname checking
# Version: 1.3 - added puppet fact to satellite server custom name conversion 
# Version: 1.4 - if/elif/else cleanup to make it easier to add new facts
#                at a later date.
#
# Usage: Run once a night via cron. Make sure to set verbose to 0
#
#########################################################################

import urllib2
import json
import sys
import xmlrpclib

# defines
VERBOSE = 1;
SATELLITE_URL = "https://rhn.costco.com/rpc/api"
SATELLITE_LOGIN = "LOGIN"
SATELLITE_PASSWORD = "PASSWORD"
PUPPET_SERVER_URL = "http://localhost:8080/v2/facts/"

# setup xmlrpc client for sat server
client = xmlrpclib.Server(SATELLITE_URL, verbose=VERBOSE)
sessionkey = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

# open url to puppet server API
resp = urllib2.urlopen(PUPPET_SERVER_URL).read()

# load puppet server facts
data = json.loads(resp.decode('utf8'))

# loop through each fact from puppet server looking for specific facts
for line in data:

    # get this lines FACT info
    myhost = line['certname']
    myfact = line['name']
    myvalue = line['value']

    # Not a pretty way to pull the facts we want, but easy to add
    # additional facts later. At the same time, define a custom value
    # name that Sat server likes. Skip line if it's a fact we don't need.
    if myfact == "location":
        mycustom = myfact
    elif myfact == "server_environment":
        mycustom = 'environment'
    elif myfact == "net_zone":
        mycustom = "netzone"
    elif myfact == "server_puppet_profile":
        mycustom = "role"
    elif myfact == "costco_os1":
        mycustom = "os1"
    else:
        continue

    # translate the hostname from puppet into a sysid that satellite knows
    # skip for safety if multiple hostnames are returned
    search = client.system.search.nameAndDescription(sessionkey, myhost)
    if len(search) > 1:
        if (VERBOSE): print 'Multiple hostnames returned for {0}. Skipping for safety' .format (myhost)
        continue

    # pull sysid from search to use to set sat custom info
    if (search):
        sysname = search[0].get('name')
        syshostname =  search[0].get('hostname')
        sysid = search[0].get("id")

        if (VERBOSE): print 'Setting {0}:{1} for hostname: {2}' .format (mycustom, myvalue, sysname)

        # set the custom info in sat server
        client.system.setCustomValues(sessionkey, sysid, {mycustom: myvalue})

# all done. cleanly close connection to sat server.
client.auth.logout(sessionkey)

