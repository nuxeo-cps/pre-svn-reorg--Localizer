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

# Python
from urlparse import urlparse

# Zope
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

# Localizer
from LocalFiles import LocalDTMLFile
from Utils import languages, get_language_name, lang_negotiator
from Gettext import dummy as N_


class LanguageManager:
    """ """

    security = ClassSecurityInfo()

    manage_options = ({'label': N_('Languages'), 'action': 'manage_languages',
                       'help': ('Localizer', 'LM_languages.stx')},)


    _languages = ()
    _default_language = None


    security.declareProtected('View management screens', 'manage_languages')
    manage_languages = LocalDTMLFile('ui/LM_languages', globals())


    security.declareProtected('Manage languages', 'manage_addLanguage')
    def manage_addLanguage(self, language, REQUEST=None, RESPONSE=None):
        """ """
        self._languages = tuple(self._languages) + (language,)

        if RESPONSE is not None:
            RESPONSE.redirect("%s/manage_languages" % REQUEST['URL1'])


    security.declareProtected('Manage languages', 'manage_delLanguages')
    def manage_delLanguages(self, languages, REQUEST=None, RESPONSE=None):
        """ """

        languages = [ x for x in self._languages if x not in languages ]
        self._languages = tuple(languages)

        if RESPONSE is not None:
            RESPONSE.redirect("%s/manage_languages" % REQUEST['URL1'])


    security.declareProtected('Manage languages', 'manage_changeDefaultLang')
    def manage_changeDefaultLang(self, language, REQUEST=None, RESPONSE=None):
        """ """
        self._default_language = language

        if REQUEST is not None:
            RESPONSE.redirect("%s/manage_languages" % REQUEST['URL1'])


    security.declarePublic('get_languages')
    def get_languages(self):
        """ """
        return self._languages


    # We need other id here, probably
    security.declarePublic('get_languages_tuple')
    def get_languages_tuple(self):
        """ """
        return [ (x, get_language_name(x)) for x in self._languages ]


    security.declarePublic('get_language_name')
    def get_language_name(self, id=None):
        """ """
        if id is None:
            id = self.get_default_language()
        return get_language_name(id)


    security.declarePublic('get_all_languages')
    def get_all_languages(self):
        """ """
        langs = languages.items()
        langs.sort()
        return langs


    # XXX We need other id here
    security.declarePublic('default_language')
    def default_language(self, lang):
        """ """
        # XXX should this be "self.get_default_language()"
        return lang == self._default_language

    security.declarePublic('get_language')


    security.declarePublic('get_available_languages')
    def get_available_languages(self, **kw):
        """
        Returns the langauges available.

        This method could be redefined in subclasses.
        """
        return self._languages


    security.declarePublic('get_default_language')
    def get_default_language(self):
        """
        Return the default language.

        This method could be redefined in subclasses.
        """
        return self._default_language


    security.declarePublic('get_selected_language')
    def get_selected_language(self, **kw):
        """
        Returns the selected language.

        Accepts keyword arguments which will be passed to
        'get_available_languages'.
        """
        available_languages = apply(self.get_available_languages, (), kw)

        return lang_negotiator(available_languages) \
               or self.get_default_language()

    # Unicode support, custom ZMI
    manage_page_header = LocalDTMLFile('ui/manage_page_header', globals())


InitializeClass(LanguageManager)
