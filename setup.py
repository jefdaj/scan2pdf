from setuptools import setup

setup(
  author       = 'Jeffrey David Johnson',
  author_email = 'jefdaj@gmail.com',
  description  = 'A script to automate scanning documents',
  entry_points = {'console_scripts': ['scan2pdf=scan2pdf:main']},
  license      = 'GPL3', # TODO check dependencies
  name         = 'scan2pdf',
  packages     = ['scan2pdf'],
  version      = '0.2',
)
