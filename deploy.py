import shutil
import os
from subprocess import run

run('tox')

run('python3.6 setup.py sdist bdist_wheel upload', shell=True)

for p in ('./dist', './build', './serial.egg-info', './.tox', './.cache'):
    if os.path.exists(p):
        shutil.rmtree(p)
