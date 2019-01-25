"""Async client helper for the Blue Iris class."""
import logging
import hashlib
import json

from aiohttp import ClientSession, ClientError

UNKNOWN_HASH = -1


class BlueIrisClient:
    """Class which facilitates communication between the BlueIris object and the Blue Iris server.

    :param ClientSession session: ClientSession to use for communication with the Blue Iris server.
    :param str endpointurl: Full URL used to communicate with the Blue Iris server. This includes the protocol
        (either http or https) and the '/json' path. If you use a non-standard port (i.e. something other than
        80 for http and 443 for https), it needs to be specified after the host. `http://192.168.1.15:81/json`
    :param bool debug: True to have more verbose logging, defaults to False.
    :param Logger logger: Logger to send log messages to.
    """

    def __init__(self, session: ClientSession, endpointurl: str, debug: bool, logger: logging.Logger):
        """Initialize a client object."""
        self.async_websession = session
        self.url = endpointurl
        self.blueiris_session = UNKNOWN_HASH
        self.response = UNKNOWN_HASH
        self.debug = debug
        self.logger = logger

    async def login(self, username, password):
        """Authenticate to the Blue Iris server.

        :param str username: Username used to authenticate to the Blue Iris server.
        :param str password: Password used to authenitcate to the Blue Iris server.
        :return dict(): Return dictionary of server properties or empty dictionary on failure.
        """
        async with self.async_websession.post(self.url, data=json.dumps({"cmd": "login"})) as r:
            respjson = await r.json()
            if self.debug:
                self.logger.debug("Initial Login response: {}".format(respjson))
            self.blueiris_session = respjson["session"]
            self.generate_response(username, password)
            return await self.cmd("login")

    def generate_response(self, username, password):
        """Generate the response needed to authenticate to the Blue Iris server.

        When communicating with the Blue Iris JSON API, you must provide a valid response when sending commands. This
        method updates the stored response used by this client.

        :warning: This object must have a current username, password and session for this method to work correctly!

        :param str username: Username used to authenticate to the Blue Iris server.
        :param str password: Password used to authenitcate to the Blue Iris server.
        """
        self.response = hashlib.md5(
            "{}:{}:{}".format(username, self.blueiris_session, password).encode('utf-8')).hexdigest()
        if self.debug:
            self.logger.debug("Generating a response hash from session.")
            self.logger.debug("Session: {}, Response: {}".format(self.blueiris_session, self.response))

    async def cmd(self, command, params=None):
        """Send a command to the Blue Iris server.

        :param str command: Command to send to the Blue Iris server.
        :param dict() params:  Parameters for the command.
        :return dict(): Return the 'data' portion of the JSON response. If there was no 'data' in the response, return
            the entire response JSON.
        """
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
                return rjson
        except ClientError as err:
            raise ClientError(
                'Error requesting data from {}: {}'.format(self.url, err))
