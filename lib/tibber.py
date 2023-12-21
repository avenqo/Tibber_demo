import requests
import time
import calendar

from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport
from dateutil.parser import parse


class Tibber:
    """Read out power values provided by Tibber."""

    def __init__(self, urlTibber, key):
        self.key = key
        self.urlTibber = urlTibber
        self.subscription_query = """
            subscription {{
                liveMeasurement(homeId:"{HOME_ID}"){{
                    timestamp
                    power
                    accumulatedConsumption
                    accumulatedCost
                    voltagePhase1
                    voltagePhase2
                    voltagePhase3
                    currentL1
                    currentL2
                    currentL3
                    lastMeterConsumption
                }}
            }}
        """
        self.headers = {"Authorization": "Bearer " + key}

    def _run_query(self, query, headers):
        """A simple function to use requests.post to make the API call. Note the json= section."""

        request = requests.post(
            url=self.urlTibber, json={"query": query}, headers=headers
        )
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception(
                "Query failed to run by returning code of {}. {}".format(
                    request.status_code, query
                )
            )

    def _ifStringZero(self, val):
        val = str(val).strip()
        if val.replace(".", "", 1).isdigit():
            res = float(val)
        else:
            res = None
        return res

    def initSocketUri(self):
        print("Tibber->initSocketUri()")

        # Get HomeID & WebSocket URI
        query = "{ viewer { homes { address { address1 } id } } }"
        resp = self._run_query(query, self.headers)
        self.tibberhomeid = resp["data"]["viewer"]["homes"][0]["id"]
        # currently not used
        self.address = resp["data"]["viewer"]["homes"][0]["address"]["address1"]

        # Get subscription URI
        resp = self._run_query("{viewer{websocketSubscriptionUrl}}", self.headers)
        self.ws_uri = resp["data"]["viewer"]["websocketSubscriptionUrl"]
        print(
            "Using homeid ["
            + self.tibberhomeid
            + "], adr ["
            + self.address
            + "], ws_uri ["
            + self.ws_uri
            + "]"
        )

    def fetch_data(self):
        print("Tibber->fetch_data()")

        transport = WebsocketsTransport(
            url=self.ws_uri, headers=self.headers, keep_alive_timeout=120
        )
        ws_client = Client(transport=transport, fetch_schema_from_transport=True)
        subscription = gql(self.subscription_query.format(HOME_ID=self.tibberhomeid))
        try:
            for result in ws_client.subscribe(subscription):
                print("Tibber->fetch_data(): result(" + str(result) + ")")
                self.console_handler(result)

        except Exception as ex:
            module = ex.__class__.__module__
            print(module + ex.__class__.__name__)
            exargs = str(ex.args)
            if exargs.find("Too many open connections") != -1:
                print("Too many open connections. Sleeping 10 minutes...")
                print(
                    "If you continue to see this error you can fix it by recreating the tibber token"
                )
                time.sleep(600)
        finally:
            ws_client.transport.close()
            print("Finally: Client closed.")

    def console_handler(self, data):
        print("Tibber->console_handler()")

        if "liveMeasurement" in data:
            measurement = data["liveMeasurement"]
            timestamp = measurement["timestamp"]
            timeObj = parse(timestamp)
            hourMultiplier = timeObj.hour + 1
            daysInMonth = calendar.monthrange(timeObj.year, timeObj.month)[1]
            power = measurement["power"]
            # min_power = measurement['minPower']
            # max_power = measurement['maxPower']
            # avg_power = measurement['averagePower']
            accumulated = measurement["accumulatedConsumption"]
            accumulated_cost = measurement["accumulatedCost"]
            # currency = measurement['currency']
            voltagePhase1 = measurement["voltagePhase1"]
            voltagePhase2 = measurement["voltagePhase2"]
            voltagePhase3 = measurement["voltagePhase3"]
            currentL1 = measurement["currentL1"]
            currentL2 = measurement["currentL2"]
            currentL3 = measurement["currentL3"]
            lastMeterConsumption = measurement["lastMeterConsumption"]
            # print(accumulated)
            output = [
                {
                    "measurement": "pulse",
                    "time": timestamp,
                    "tags": {"address": self.address},
                    "fields": {
                        "power": self._ifStringZero(power),
                        "consumption": self._ifStringZero(accumulated),
                        "cost": self._ifStringZero(accumulated_cost),
                        "voltagePhase1": self._ifStringZero(voltagePhase1),
                        "voltagePhase2": self._ifStringZero(voltagePhase2),
                        "voltagePhase3": self._ifStringZero(voltagePhase3),
                        "currentL1": self._ifStringZero(currentL1),
                        "currentL2": self._ifStringZero(currentL2),
                        "currentL3": self._ifStringZero(currentL3),
                        "lastMeterConsumption": self._ifStringZero(
                            lastMeterConsumption
                        ),
                        "hourmultiplier": hourMultiplier,
                        "daysInMonth": daysInMonth,
                    },
                }
            ]

            print("---- Output, Date ----")
            print(output)
            print(data)

    def readPower(self):
        print("Tibber->readPower() - sleep for 5 secs.")
        time.sleep(5)
        print("Run GQL query.")
        self.fetch_data()
