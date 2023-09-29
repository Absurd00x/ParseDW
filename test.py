from telethon import TelegramClient
from credentials import api_id, api_hash
import shelve
import hashlib
import telethon.errors
import re

client = TelegramClient("my_session", api_id, api_hash)
dw_id = 1234060895

async def main():
  tmp = []
  async for msg in client.iter_messages(dw_id, 1):
    photos = None
    try:
      photos = await msg.download_media("buff/")
    except telethon.errors.rpcerrorlist.TimeoutError:
      print("Failed to download pictures with the following text:")
      print(msg.text)
    if photos is None:
      continue
    if type(photos) is str:
      photos = [photos]
    hashes = []
    for path in photos:
      with open(path, "rb") as f:
        hashed = hashlib.sha256(f.read()).hexdigest()
        hashes.append(hashed)
    tmp.append((hashes, msg.text))
  with shelve.open("test") as f:
    f["data"] = tmp


with client:
  client.loop.run_until_complete(main())

with shelve.open("test") as f:
  print(f["data"])
