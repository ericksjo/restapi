#!/usr/bin/env python
import os
from ConfigParser import SafeConfigParser

keystore_locations = [
    "%s/.credentials/credentials.ini" % os.environ.get("HOME","."),
    "/etc/credentials/credentials.ini",
]

valid_keystore_locations = [loc for loc in keystore_locations if os.path.isfile(loc)]

credentials = SafeConfigParser()
if len(valid_keystore_locations) > 0:
    # The first valid keystore location is the highest priority
    credentials.read(valid_keystore_locations[0])
else:
    print "Couldn't locate any credentials"
