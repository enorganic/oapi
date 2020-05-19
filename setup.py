from setuptools import setup

setup(
    name='oapi',
    version="0.1.2",
    description=(
        'An SDK for parsing OpenAPI (Swagger) 2.0 - 3.0 specifications'
    ),
    url='https://bitbucket.com/davebelais/oapi.git',
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
        "pyyaml>=3",
        "iso8601~=0.1",
        "sob>=0.5.7,<1",
        "jsonpointer~=2.0"
    ],
    extras_require={
        "dev": [
            "pytest~=5.4",
            "tox~=3.14",
            "flake8~=3.7"
        ],
        "test": [
            "pytest~=5.4",
            "tox~=3.14",
            "flake8~=3.7"
        ]
    }
)
