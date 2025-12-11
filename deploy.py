import os
import sys
import subprocess
import platform

def run(cmd, env=None):
    return subprocess.run(cmd, check=True, env=env)

def main():
    proj_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(proj_dir, ".venv")
    py = sys.executable

    if not os.path.exists(venv_dir):
        run([py, "-m", "venv", venv_dir])

    if platform.system() == "Windows":
        vpy = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        vpy = os.path.join(venv_dir, "bin", "python")

    run([vpy, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])
    req = os.path.join(proj_dir, "requirements.txt")
    run([vpy, "-m", "pip", "install", "-r", req])
    run([vpy, os.path.join(proj_dir, "main.py")])

if __name__ == "__main__":
    main()
