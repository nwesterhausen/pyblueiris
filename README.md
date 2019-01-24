# README

## Blue Iris Python Library

An async python library for the Blue Iris JSON API.

## Overview
For more in-depth documentation, visit [the documentation](https://pyblueiris.gitbook.io/docs).

Creating a BlueIris object requires you provide an async web session for it.

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

From there you can simply call a command you want it to execute. There is a command `update_all_information()` which will call all data-gathering commands to fill out information about the server.

```python
def main():  
  async with ClientSession(raise_for_status=True) as sess:
    blue = pyblueiris.BlueIris(sess, USER, PASS, PROTOCOL, HOST)
    await blue.update_all_information()
```

All of the information the BlueIris object knows about the server is stored in the attributes property \(dictionary\).

```python
print(blue.attributes)
```

