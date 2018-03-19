from setuptools import setup, find_packages

version = '0.0.18'

setup(
    name='oapi',

    version=version,

    description='An SDK for parsing OpenAPI (Swagger) 2.0 - 3.0 specifications.',

    # The project's main homepage.
    url='https://bitbucket.com/davebelais/oapi.git',

    # Author details
    author='David Belais',
    author_email='david@belais.me',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='openapi swagger json rest',

    packages=find_packages(),
    # packages=[], # explicitly set packages
    # py_modules=[], # Single-file module names

    # dependencies
    # See https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'future>=0.16.0',
        'pyyaml>=3.12',
        'iso8601>=0.1.12',
        'serial>=0.0.50',
        'jsonpointer>=1.12'
    ],

    # pip install -e .[dev, test]
    extras_require={
        'dev': [
            'pytest>=2.9.0'
        ],
        'test': [
            'pytest>=2.9.0'
        ],
    },

    package_data={},

    # See http://docs.python.org/3.5/distutils/setupscript.html#installing-additional-files
    data_files=[],

    entry_points={
        'console_scripts': [],
    }
)
