from setuptools import setup, find_packages

setup(
    name='oapi',
    version="0.0.58",
    description=(
        'An SDK for parsing OpenAPI (Swagger) 2.0 - 3.0 specifications'
    ),
    url='https://bitbucket.com/davebelais/oapi.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    python_requires='>=3.7',
    keywords='openapi swagger json rest',
    packages=find_packages(),
    install_requires=[
        "future>=0.18.2",
        "pyyaml>=5.1.1",
        "iso8601>=0.1.12",
        "sob>=0.1.45",
        "jsonpointer>=2.0"
    ],
    extras_require={
        "dev": [
            "pytest>=5.1.1"
        ],
        "test": [
            "pytest>=5.1.1"
        ]
    }
)