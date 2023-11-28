import os
import threading
import time
from sys import executable

def start():
    os.system(f"cd {executable}; python3.12 main.py")


t = threading.Thread(target=start)
time.sleep(5)
os._exit(0)
