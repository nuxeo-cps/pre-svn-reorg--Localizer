# -*- coding: iso-8859-15 -*-

# Localizer, Zope product that provides internationalization services
# Copyright (C) 2000-2002  Juan David Ibáñez Palomar <j-david@noos.fr>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


"""
Localizer..
"""


from Globals import package_home, get_request


# Package home
ph = package_home(globals())

# Initializes a dictionary containing the iso 639 language codes/names
languages = {}
for line in open(ph + '/languages.txt').readlines():
    line = line.strip()
    if line and line[0] != '#':
        code, name = line.split(' ', 1)
        languages[code] = name

def get_language_name(language_code):
    return languages.get(language_code, '???')


# Initializes a list with the charsets
charsets = [ x.strip() for x in open(ph + '/charsets.txt').readlines() ]



# Language negotiation
def lang_negotiator(available_languages):
    """
    Recives two ordered lists, the list of user prefered languages
    and the list of available languages. Returns the first user pref.
    language that is available, if none is available returns None.
    """

    request = get_request()
    if request is None:
        # Happens sometimes during unit tests
        return None

    lang = request.AcceptLanguage.select_language(available_languages)


    # XXX Here we should set the Vary header, but, which value should it have??
##    response = request.RESPONSE
##    response.setHeader('Vary', 'accept-language')
##    response.setHeader('Vary', '*')

    return lang


# Defines strings that must be internationalized
def N_(message): pass
N_('Contents')     # Tabs of the management screens
N_('View')
N_('Properties')
N_('Security')
N_('Undo')
N_('Ownership')
N_('Find')
N_('Catalan')      # Languages
N_('German')
N_('Spanish')
N_('Basque')
N_('French')
N_('Hungarian')
N_('Japanese')
