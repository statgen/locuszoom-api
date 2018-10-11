import io
from setuptools import find_packages, setup

with io.open('README.md','rt',encoding='utf8') as f:
  readme = f.read()

with io.open('requirements.txt','rt',encoding='utf8') as f:
  requirements = f.read().split()

setup(
  name = 'locuszoom-api',
  version = '0.1.0',
  url = 'https://github.com/statgen/locuszoom-api',
  license = 'GPLv3',
  maintainer = 'Ryan Welch',
  maintainer_email = 'welchr@umich.edu',
  description = 'Flask server code for the LocusZoom REST API',
  long_description = readme,
  packages = find_packages(),
  include_package_data = True,
  zip_safe = False,
  install_requires = requirements,
  classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Programming Language :: Python :: 3.6 :: Only',
    'Operating System :: POSIX :: Linux',
  ],
)
