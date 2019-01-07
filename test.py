import logging, sys, asyncio

import blueiris as BI

from test_config import USER, PASS, PROTOCOL, HOST

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

MY_LOGGER = logging.getLogger(__name__)


async def tests():
    blue = BI.BlueIris(USER, PASS, PROTOCOL, HOST, debug=True, logger=MY_LOGGER)
    await blue.command("status")
    # blue.selfTest()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tests())
