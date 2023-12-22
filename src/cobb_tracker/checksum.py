#!/usr/bin/env python
import hashlib
from file_ops import FileList
from pathlib import Path

BUFFER=(1024 ** 2) * 3
fileops = FileList(Path('/home/sam/minutes'))
for entry in fileops.minutes_files():
    print("")
    with open(entry, 'rb') as file:
        m = hashlib.sha256()
        while True:
            chunk = file.read(BUFFER)
            if not chunk:
                break
            m.update(chunk)
        print(m.hexdigest())

