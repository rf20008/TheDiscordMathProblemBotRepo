import multiprocessing
import os
import subprocess
from sys import executable
from time import sleep

print("We are: " + str(os.path.abspath(os.getcwd())))
current_file_path = os.path.abspath(__file__)
main_script_path = os.path.abspath(
    os.path.join(os.path.dirname(current_file_path), "..", "main.py")
)
test_script_path = os.path.abspath(
    os.path.join(os.path.dirname(current_file_path), "test.py")
)
print("Current file path: " + str(current_file_path))
print("Main script path: " + str(main_script_path))
q = subprocess.Popen(
    test_script_path.split(),
    executable=executable,
    shell=False,
)

print("Q's PID is " + str(q.pid))
q.wait()
print(q.stdout)


def start():
    print(f"Hello from my subprocess! My PID is {os.getpid()}")
    print(f"{main_script_path}")

    p = subprocess.Popen(
        f"{main_script_path}".split(),
        executable=executable,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    )
    print("NEW PID: " + str(p.pid))
    # os.system(f"cd {executable}; python3.12 -m main.py")
    p.wait()


if __name__ == "__main__":
    print(f"Parent PID: {os.getpid()}")
    sp = multiprocessing.Process(target=start)
    sp.start()
    try:
        sp.join(timeout=1.0)
    finally:
        sp.kill()
        os._exit(0)  # type: ignore
