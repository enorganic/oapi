import shutil
import os
from subprocess import run

run('python3.6 setup.py sdist bdist_wheel upload', shell=True)

shutil.rmtree('./dist')
shutil.rmtree('./build')
shutil.rmtree('./oapi.egg-info')
if os.path.exists('./.cache'):
    shutil.rmtree('./.cache')