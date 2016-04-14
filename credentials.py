#!/usr/bin/env python
import os
from ConfigParser import SafeConfigParser

keystore_locations = [
    "%s/.credentials/credentials.ini" % os.environ.get("HOME","."),
    "/etc/credentials/credentials.ini",
]

filename = None
for location in keystore_locations:
    if os.path.isfile(location):
        filename = location
        break
credentials = SafeConfigParser()
if filename:
    credentials.read(filename)
else:
    print "Couldn't locate any credentials"
