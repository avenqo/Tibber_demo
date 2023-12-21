from lib.tibber import Tibber

import os

TIBBER_URL = "https://api.tibber.com/v1-beta/gql"

TIBBER_API_TOKEN = os.getenv("TIBBER_API_TOKEN")  # None
if TIBBER_API_TOKEN is None:
    raise NameError("Environment variable TIBBER_API_TOKEN isn't defined yet!")

clientTibber = Tibber(TIBBER_URL, TIBBER_API_TOKEN)
clientTibber.initSocketUri()
clientTibber.readPower()
