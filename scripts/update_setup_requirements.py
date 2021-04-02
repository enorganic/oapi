#!/usr/bin/env python3
"""
This script updates installation requirements in ../setup.py
"""
import os
from subprocess import getstatusoutput

from setuptools_setup_versions import requirements  # type: ignore


def run(command: str) -> str:
    print(command)
    status, output = getstatusoutput(command)
    # Create an error if a non-zero exit status is encountered
    if status:
        raise OSError(output)
    else:
        print(output)
    return output


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Update `setup.py` to require currently installed versions of all packages
    requirements.update_setup(
        default_operator="~=", ignore=("setuptools", "pyyaml")
    )
    run("black setup.py")
