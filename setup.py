from setuptools import setup, find_packages
import logging
logger = logging.getLogger(__name__)

name = 'quantumcircuitbenchmarks'
package_name = name
version = '0.1.0'

try:
    with open('README.md', 'r') as f:
        long_desc = f.read()
except:
    logger.warning('Could not open README.md.  '
                   'long_description will be set to None.')
    long_desc = None

setup(
    name = package_name,
    packages = find_packages(),
    version = version,
    description = '<Package description here>',
    long_description = long_desc,
    long_description_content_type = 'text/markdown',
    author = 'Jonathan M. Baker',
    url = 'https://github.com/jmbaker94/{}'.format(name),
    download_url = 'https://github.com/jmbaker94/{}/archive/{}.tar.gz'.format(name, version),
    keywords = ['quantum computing', 'benchmark'],
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires = [
        'networkx',
    ],
)

