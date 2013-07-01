from setuptools import setup, find_packages
import sys, os

version = '0.1.1'

install_requires = [
    "django-templateinspector",
    "djangohelpers",
    ]

import sys
if sys.version_info[:2] < (2, 7):
    install_requires.append("simplejson")

setup(name='django-apihangar',
      version=version,
      description="through-the-web creation of templated sql->json APIs for querying data",
      long_description="",
      classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
      ],
      keywords='',
      author='Ethan Jucovy',
      author_email='ethan@boldprogressives.org',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      entry_points="""
      """,
      )
