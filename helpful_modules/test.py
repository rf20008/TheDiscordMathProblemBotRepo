import subprocess
print("test stuff is working :D")
subprocess.run(("/usr/bin/say " + "HELLO " * 10).split())
subprocess.run(f"/usr/bin/say {__name__}")