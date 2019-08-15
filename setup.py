from setuptools import setup, find_packages

setup(
    name='oapi',
    version="0.0.48",
    description=(
        'An SDK for parsing OpenAPI (Swagger) 2.0 - 3.0 specifications'
    ),
    url='https://bitbucket.com/davebelais/oapi.git',
    author='David Belais',
    author_email='david@belais.me',
    license='MIT',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='openapi swagger json rest',
    packages=find_packages(),
    install_requires=[
        "future>=0.17.1",
        "pyyaml>=5.1.1",
        "iso8601>=0.1.12",
        "sob>=0.1.32",
        "jsonpointer>=2.0"
    ],
    extras_require={
        "dev": [
            "pytest>=5.0.1"
        ],
        "test": [
            "pytest>=5.0.1"
        ]
    }
)