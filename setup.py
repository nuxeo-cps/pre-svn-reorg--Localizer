# -*- coding: iso-8859-15 -*-

from distutils.core import setup

setup(name='Localizer',
      version='0.9',
      description='Internatinalization facilities for Zope',
      author='Juan David Ibáñez Palomar',
      author_email='j-david@noos.fr',
      url='http://www.j-david.net/localizer',
      packages=[''],
      scripts=['zgettext.py'],
      data_files=[('ui', ['ui/changeLanguageForm.dtml',
                          'ui/LocalFolder_add.dtml'])])
