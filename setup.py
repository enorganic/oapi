import sys
from typing import Any, Set

import setuptools  # type: ignore

_INSTALL_REQUIRES: str = "install_requires"


def setup(**kwargs: Any) -> None:
    """
    This `setup` script intercepts arguments to be passed to
    `setuptools.setup` in order to dynamically alter setup requirements
    while retaining a function call which can be easily parsed and altered
    by `setuptools-setup-versions`.
    """
    # Require the package "dataclasses" for python 3.6, but not later
    # python versions (since it's part of the standard library after 3.6)
    if sys.version_info[:2] == (3, 6):
        if _INSTALL_REQUIRES not in kwargs:
            kwargs[_INSTALL_REQUIRES] = []
        kwargs[_INSTALL_REQUIRES].append("dataclasses")
    # Add an "all" extra which includes all extra requirements
    if "extras_require" in kwargs and "all" not in kwargs["extras_require"]:
        all_extras_require: Set[str] = set()
        kwargs["extras_require"]["all"] = []
        for extra_name, requirements in kwargs["extras_require"].items():
            if extra_name != "all":
                for requirement in requirements:
                    if requirement not in all_extras_require:
                        all_extras_require.add(requirement)
                        kwargs["extras_require"]["all"].append(requirement)
    # Pass the modified keyword arguments to `setuptools.setup`
    setuptools.setup(**kwargs)

setup(
    name='oapi',
    version="1.0.0",
    description=(
        'An SDK for parsing OpenAPI (Swagger) 2.0 - 3.0 specifications'
    ),
    url='https://github.com/davebelais/oapi.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='~=3.6',
    keywords='openapi swagger json rest',
    packages=[
        'oapi',
        'oapi.oas'
    ],
    setup_requires=[
        "setuptools"
    ],
    install_requires=[
        "pyyaml>=3.10",
        "iso8601~=0.1",
        "sob~=1.0",
        "jsonpointer~=2.0"
    ],
    extras_require={
        "dev": [
            "pytest~=5.4",
            "tox~=3.20",
            "flake8~=3.8",
            "daves-dev-tools~=0.0",
            "readme-md-docstrings~=0.1"
        ],
        "test": [
            "pytest~=5.4",
            "tox~=3.20",
            "flake8~=3.8"
        ]
    }
)
