# Blue Iris Python Library

An async python library for the Blue Iris JSON API.

# Usage

Creating a BlueIris object requires you provide an async web session for it.

```python
import pyblueiris

from aiohttp import ClientSession
```

```python
async with ClientSession(raise_for_status=True) as sess:
    blue = BI.BlueIris(sess, USER, PASS, PROTOCOL, HOST)
```

Optionally you can provide a `logging.Logger` for it to use, and you can enable debug messages with the `debug=True` flag:

```python
async with ClientSession(raise_for_status=True) as sess:
    blue = BI.BlueIris(sess, USER, PASS, PROTOCOL, HOST, logger=_LOGGER, debug=True)
```

From there you can simply call a command you want it to execute. There is a command `update_all_information()` which will call all data-gathering commands to fill out information about the server.

```python
await blue.update_all_information()
```

All of the information the BlueIris object knows about the server is stored in the attributes property (dictionary).

```python
print(blue.attributes)
```