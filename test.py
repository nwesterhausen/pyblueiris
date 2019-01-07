import logging, sys

import blueiris as BI

from .test_config import USER, PASS, PROTOCOL, HOST

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

MY_LOGGER = logging.getLogger(__name__)

def tests():
    blue = BI.BlueIris(USER, PASS, PROTOCOL, HOST, debug=True, logger=MY_LOGGER)
    blue.selfTest()


if __name__ == "__main__":
    tests()
