import logging
import hashlib
import json

from aiohttp import ClientSession, ClientError


UNKNOWN_HASH = -1

_LOGGER = logging.getLogger(__name__)


class BlueIrisClient:

    def __init__(self, session: ClientSession, user, password, protocol, host, port="", debug=False, logger=_LOGGER):
        self.async_websession = session
        """Define an abstract blue iris server."""
        if port != "":
            host = "{}:{}".format(host, port)
        self.url = "{}://{}/json".format(protocol, host)
        self.user = user
        self.password = password
        self.blueiris_session = UNKNOWN_HASH
        self.response = UNKNOWN_HASH
        self.debug = debug
        self.logger = logger

    async def login(self):
        """
        Send hashed username/password to validate session
        Returns system name and dictionary of profiles OR nothing
        """
        async with self.async_websession.post(self.url, data=json.dumps({"cmd": "login"})) as r:
            respjson = await r.json()
            if self.debug:
                self.logger.debug("Initial Login response: {}".format(respjson))
            self.blueiris_session = respjson["session"]
            self.generate_response()
            return await self.cmd("login")

    def generate_response(self):
        """Update self.username, self.password and self.blueiris_session before calling this."""
        if self.debug:
            self.logger.debug("Generating a response hash with session: {}".format(self.blueiris_session))
        self.response = hashlib.md5(
            "{}:{}:{}".format(self.user, self.blueiris_session, self.password).encode('utf-8')).hexdigest()

    async def cmd(self, command, params=None):
        if params is None:
            params = dict()
        args = {"session": self.blueiris_session, "response": self.response, "cmd": command}
        args.update(params)

        if self.debug:
            self.logger.info("Sending async command: {} {}".format(command, params))
            self.logger.debug("Full command JSON data: {}".format(args))

        try:
            async with self.async_websession.post(self.url, data=args) as resp:
                rjson = await resp.json()
                if self.debug:
                    self.logger.debug("Full json response: {}".format(rjson))
                return rjson["data"]
        except ClientError as err:
            raise ClientError(
                'Error requesting data from {}: {}'.format(self.url, err))
        except KeyError:
            """It's possible that there was no data to be returned. In that case respond 'None'"""
            self.logger.error("No 'data' response from cmd:{}".format(command))
            if self.debug:
                self.logger.error("POST JSON: {}".format(args))
                self.logger.error("RESPONSE: {}".format(rjson))
