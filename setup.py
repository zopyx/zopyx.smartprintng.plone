from setuptools import setup, find_packages
import os

version = '2.1.18'

setup(name='zopyx.smartprintng.plone',
      version=version,
      description="Produce & Publisher server integration with Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "source", "HISTORY.rst")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Plone",
        "Framework :: Plone :: 4.0",
        "Framework :: Plone :: 4.1",
        "Framework :: Plone :: 4.2",
        "Framework :: Zope2",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='PDF Plone Python EBook EPUB',
      author='Andreas Jung',
      author_email='info@zopyx.com',
      url='http://pypi.python.org/pypi/zopyx.smartprintng.plone',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['zopyx', 'zopyx.smartprintng'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'BeautifulSoup',
          'zopyx.smartprintng.client',
          'zopyx.convert2',
          'lxml',
          'uuid',
          'Pillow',
          'archetypes.schemaextender',
          'unittest2'
          # -*- Extra requirements: -*-
      ],
      tests_require=['zope.testing'],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
