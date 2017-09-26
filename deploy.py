import shutil
from subprocess import run

run('python3.6 setup.py sdist bdist_wheel', shell=True)
run('twine upload dist/*', shell=True)

shutil.rmtree('./dist')
shutil.rmtree('./build')
shutil.rmtree('./oapi.egg-info')
shutil.rmtree('./.cache')
