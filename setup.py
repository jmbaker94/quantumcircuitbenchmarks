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
    url = f'https://github.com/jmbaker94/{name}',
    download_url = f'https://github.com/jmbaker94/{name}/archive/{version}.tar.gz',
    keywords = ['quantum computing', 'benchmark'],
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires = [
        'cirq==0.8',
        'networkx',
    ],
)

