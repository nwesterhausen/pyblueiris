---
description: Overview of getting pyblueiris connected to your Blue Iris server.
---

# Getting Started

## Installation

Installation is as easy as:

```
$ pip install pyblueiris
```

## Usage

Creating a BlueIris object requires you provide an async web session for it.
You also need to provide the protocol (`http` or `https`), the host IP or FQDN, and a username and password.

```python
import pyblueiris
from aiohttp import ClientSession

PROTOCOL = 'http'
HOST = 192.168.1.5
USER = 'pyserv'
PASS = 'secret-password'

def main():  
  async with ClientSession(raise_for_status=True) as sess:
    blue = pyblueiris.BlueIris(sess, USER, PASS, PROTOCOL, HOST)
 
if __name__ == '__main__':
  main()
```

From there you can use the helper functions to make API calls against your Blue Iris server.
