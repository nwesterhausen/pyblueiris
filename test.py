import logging, sys, asyncio

import pyblueiris as BI

from test_config import USER, PASS, PROTOCOL, HOST
from aiohttp import ClientSession

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

MY_LOGGER = logging.getLogger(__name__)


async def tests():
    async with ClientSession(raise_for_status=True) as sess:
        blue = BI.BlueIris(sess, USER, PASS, PROTOCOL, HOST, debug=True, logger=MY_LOGGER)
        #await blue.setup_session()
        await blue.update_all_information()

        print(blue.attributes)

        # print("Sending disable to INT01")
        # await blue.enable_camera("INT01", False)
        # print("Sending enable to INT01")
        # await blue.enable_camera("INT01", True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tests())
