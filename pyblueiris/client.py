import logging
import hashlib
import json

from aiohttp import ClientSession, ClientError


UNKNOWN_HASH = -1

class BlueIrisClient:

    def __init__(self, session: ClientSession, endpointurl, debug: bool, logger: logging.Logger):
        self.async_websession = session
        self.url = endpointurl
        self.blueiris_session = UNKNOWN_HASH
        self.response = UNKNOWN_HASH
        self.debug = debug
        self.logger = logger

    async def login(self, username, password):
        """
        Send hashed username/password to validate session
        Returns system name and dictionary of profiles OR nothing
        """
        async with self.async_websession.post(self.url, data=json.dumps({"cmd": "login"})) as r:
            respjson = await r.json()
            if self.debug:
                self.logger.debug("Initial Login response: {}".format(respjson))
            self.blueiris_session = respjson["session"]
            self.generate_response(username, password)
            return await self.cmd("login")

    def generate_response(self, username, password):
        """Update self.username, self.password and self.blueiris_session before calling this."""
        self.response = hashlib.md5(
            "{}:{}:{}".format(username, self.blueiris_session, password).encode('utf-8')).hexdigest()
        if self.debug:
            self.logger.debug("Generating a response hash from session.")
            self.logger.debug("Session: {}, Response: {}".format(self.blueiris_session,self.response))

    async def cmd(self, command, params=None):
        if params is None:
            params = dict()
        args = {"session": self.blueiris_session, "response": self.response, "cmd": command}
        args.update(params)

        if self.debug:
            self.logger.info("Sending async command: {} {}".format(command, params))
            self.logger.debug("Full command JSON data: {}".format(args))

        try:
            async with self.async_websession.post(self.url, data=json.dumps(args)) as resp:
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
