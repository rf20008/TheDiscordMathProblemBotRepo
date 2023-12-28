import os
import threading
import time
from sys import executable
import subprocess


def start():
    print(f"{executable} -m main.py")
    subprocess.run([executable, "-m", "main.py"])
    #os.system(f"cd {executable}; python3.12 -m main.py")


t = threading.Thread(target=start)
time.sleep(6)
os._exit(0)
