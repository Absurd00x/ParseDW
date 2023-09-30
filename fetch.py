from time import sleep
from random import random
from telethon import TelegramClient
from credentials import api_id, api_hash
import telethon.errors
import hashlib
import shelve
import datetime
import os
import re


if not os.path.isdir("buff"):
  os.mkdir("buff")

if not os.path.isdir("backup"):
  os.mkdir("backup")

client = TelegramClient("my_session", api_id, api_hash)
dw_id = 1234060895

async def extract_hashes(message):
  if not message.photo:
    return None
  photos = None
  try:
    photos = await message.download_media("buff/")
  except telethon.errors.rpcerrorlist.TimeoutError:
    print("Failed to download pictures with the following text:")
    print(message.text)
    return None
  if photos is None:
    return None
  if type(photos) is str:
    photos = [photos]
  res = []
  for path in photos:
    with open(path, "rb") as f:
      hashed = hashlib.sha256(f.read()).hexdigest()
      res.append(hashed)
    os.remove(path)
  return res


pattern = re.compile("\D[1-3][0-9]\D?")
async def extract_age(message):
  if not message.text:
    return None
  s = pattern.findall(message.text)
  age = None
  for num in s:
    num = num[1:3]
    if f"Мне {num}" in message.text \
        or f"мне {num}" in message.text \
        or f"{num})" in message.text:
      age = int(num)
      break
  if age is None:
    for num in s:
      num = num[1:3]
      if f", {num}," in message.text:
        return int(num)
  return age


async def main(mine=False, sieve=False, unique=False, extract=False, backup=False):
  last = 0
  async for message in client.iter_messages(dw_id):
    if message.photo:
      last = message.id
      break
  print("Got last message")
  if mine:
    sieve = True
    unique = True
    # get messages
    print("Mining messages")
    responses = ("👎", "1 👍", "Нет", "👍Полезно", "Продолжить просмотр анкет", "Не люблю игры", "Не очень",
                 "Продолжить смотреть анкеты", "Возможно позже", "Анкеты в Telegram", "Не интересно",
                 "Сам найду(", "Поделюсь с другом", "Смотреть анкеты", "💳 Нет, буду платить дальше", "1 🚀")
    ind = 0
    finish_response = "1. Смотреть анкеты.\n2. Моя анкета.\n3. Я больше не хочу никого искать.\n***\n4. Пригласи друзей - получи больше лайков 😎."
    flag = False
    while ind < len(responses):
      try:
        await client.send_message(dw_id, responses[ind])
        sleep(1 + random())
        res = (await client.get_messages(dw_id))[0]
        if res.text == "Нет такого варианта ответа":
          ind += 1
        elif res.text == "Пока все, больше нет анкет для тебя, попробуй позже":
          ind = len(responses)
        elif res.text == finish_response:
          ind = len(responses)
        else:
          ind = 0
      except KeyboardInterrupt:
        exit(0)
      except StopIteration:
        break
      except Exception as e:
        print("Something went wrong when mining messages")
        print(e)
        if not flag:
          flag = True
        else:
          break
  if sieve:
    # remove responses
    print("Filtering responses")
    msgs = []
    region = re.compile("[Мм]осковская [Оо]бласть")
    city = re.compile("[Мм]осква")
    async for message in client.iter_messages(dw_id):
      if message.text is None:
        msgs.append(message)
        continue
      avoid = region.findall(message.text)
      match = city.findall(message.text)
      if not message.photo \
          or message.text.startswith("Кому-то понравилась твоя анкета") \
          or message.text.startswith(".,") \
          or len(avoid) > 0 \
          or len(match) == 0:
        msgs.append(message)
      if message.id < last:
        break

    print("Fetched responses")
    for msg in msgs:
      await msg.delete()
    print("Deleted responses")

  if unique:
    # remove duplicates
    print("Filtering duplicates")
    with shelve.open("hashtable") as f:
      if "data" in f:
        images = f["data"]
        present = True
        print(f"Found {len(images)} hash entries")
      else:
        images = set()
        present = False
        print("Didn't find any hash entries")
    buff = []
    async for message in client.iter_messages(dw_id):
      if message.id == last and present:
        break
      hashes = await extract_hashes(message)
      if hashes is None:
        buff.append(message)
      else:
        duplicate = False
        for hashed in hashes:
          if hashed in images:
            duplicate = True
        for hashed in hashes:
          images.add(hashed)
        if duplicate:
          buff.append(message)
    print(f"Total duplicates: {len(buff)}")
    print("Removing...")
    for msg in buff:
      await msg.delete()
    with shelve.open("hashtable") as f:
      f["data"] = images

  cnt_new = 0
  cnt_total = 0
  if extract:
    # extract ages from messages
    print("Extracting ages from messages")
    cnts = dict()
    buff = []
    async for message in client.iter_messages(dw_id):
      age = await extract_age(message)
      if age is None:
        buff.append(message)
      else:
        if age not in cnts:
          cnts[age] = 0
        cnts[age] += 1
    for msg in buff:
      await msg.delete()
    keys = list(cnts.keys())
    keys.sort()
    with open("res.txt", "w") as f:
      for key in keys:
        f.write(f"{key} {cnts[key]}\n")
  cnt_total = 0
  cnt_new = 0
  async for message in client.iter_messages(dw_id):
    cnt_total += 1
    if message.id >= last:
      cnt_new += 1
  print(f"New entries: {cnt_new}")
  print(f"Total entries: {cnt_total}")
  if backup:
    print("Creating backup")
    tmp = []
    async for msg in client.iter_messages(dw_id):
      if msg.id == last:
        break
      hashes = await extract_hashes(msg)
      age = await extract_age(msg)
      if hashes is None or age is None:
        continue
      else:
        tmp.append((hashes, age))
    with shelve.open("backup/messages") as f:
      timestamp = str(datetime.datetime.now()).replace(' ', '_')
      f[f"data_{timestamp}"] = tmp
  print("Done")


mask = input("Enter mask:\nmine sieve unique extract backup\n")
if len(mask) != 5:
  print("Mask length must be equal to 5. Terminating.")
  exit(0)
ok = True
for symb in mask:
  if symb != '0' and symb != '1':
    ok = False
if not ok:
  print("Mask should consist of ones and zeros. Terminating.")
  exit(0)

args = list(map(lambda x: x == '1', mask))

with client:
  client.loop.run_until_complete(main(*args))
