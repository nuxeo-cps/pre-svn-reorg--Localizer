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
This module provides the MessageCatalog base class, which
provides message catalogs for the web.
"""
__version__ = "$Revision$"


# Python
import base64, re, time
from types import StringType, UnicodeType
from urllib import quote

# Zope
from Globals import  MessageDialog, PersistentMapping, InitializeClass, \
     get_request
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

# Localizer
from LocalFiles import LocalDTMLFile
from zgettext import parse_po_file
from Utils import charsets, get_language_name, lang_negotiator
from LanguageManager import LanguageManager
import Gettext


_ = Gettext.translation(globals())
N_ = Gettext.dummy



manage_addMessageCatalogForm = LocalDTMLFile('ui/MC_add', globals())
def manage_addMessageCatalog(self, id, title, languages, REQUEST=None):
    """ """
    self._setObject(id, MessageCatalog(id, title, languages))

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


# Empty header information for PO files, the default
empty_po_header = {'last_translator_name': '',
                   'last_translator_email': '',
                   'language_team': '',
                   'charset': ''}

_marker = []


class MessageCatalog(LanguageManager, ObjectManager, SimpleItem):
    """
    Stores messages and their translations...
    """

    meta_type = 'MessageCatalog'

    security = ClassSecurityInfo()


    def __init__(self, id, title, languages):
        self.id = id

        self.title = title

        # Language Manager data
        self._languages = tuple(languages)
        self._default_language = languages[0]

        # Here the message translations are stored
        self._messages = PersistentMapping()

        # Data for the PO files headers
        self._po_headers = PersistentMapping()
        for lang in self._languages:
            self._po_headers[lang] = empty_po_header


    #######################################################################
    # Public API
    #######################################################################
    security.declarePublic('message_encode')
    def message_encode(self, message):
        """
        Encodes a message to an ASCII string.
        To be used in the user interface, to avoid problems with the
        encodings, HTML entities, etc..
        """
        if type(message) is UnicodeType:
            msg = 'u' + message.encode('utf8')
        else:
            msg = 'n' + message

        return base64.encodestring(msg)


    security.declarePublic('message_decode')
    def message_decode(self, message):
        """
        Decodes a message from an ASCII string.
        To be used in the user interface, to avoid problems with the
        encodings, HTML entities, etc..
        """
        message = base64.decodestring(message)
        type = message[0]
        message = message[1:]
        if type == 'u':
            return unicode(message, 'utf8')
        return message


    security.declarePublic('message_exists')
    def message_exists(self, message):
        """ """
        return self._messages.has_key(message)


    security.declareProtected('Manage messages', 'message_edit')
    def message_edit(self, message, language, translation):
        """ """
        self._messages[message][language] = translation


    security.declareProtected('Manage_messages', 'message_del')
    def message_del(self, message):
        """ """
        del self._messages[message]


    security.declarePublic('gettext')
    def gettext(self, message, lang=None, add=1, default=_marker):
        """Returns the message translation from the database if available.

        If add=1, add any unknown message to the database.
        If a default is provided, use it instead of the message id
        as a translation for unknown messages.
        """

        if type(message) not in (StringType, UnicodeType):
            raise TypeError, 'only strings can be translated.'

        message = message.strip()

        if default is _marker:
            default = message

        # Add it if it's not in the dictionary
        if add and not self._messages.has_key(message) and message:
            self._messages[message] = PersistentMapping()

        # Get the string
        if self._messages.has_key(message):
            m = self._messages[message]

            if lang is None:
                # Builds the list of available languages
                # should the empty translations be filtered?
                available_languages = list(self._languages)

                # Get the language!
                lang = lang_negotiator(available_languages)

                # Is it None? use the default
                if lang is None:
                    lang = self._default_language

            if lang is not None:
                return m.get(lang) or default

        return default


    __call__ = gettext



    #######################################################################
    # Management screens
    #######################################################################
    def manage_options(self):
        """ """
        options = (
            {'label': N_('Messages'), 'action': 'manage_messages',
             'help': ('Localizer', 'MC_messages.stx')},
            {'label': N_('Properties'), 'action': 'manage_propertiesForm'},
            {'label': N_('Import/Export'), 'action': 'manage_importExport',
             'help': ('Localizer', 'MC_importExport.stx')}) \
            + LanguageManager.manage_options \
            + SimpleItem.manage_options

        r = []
        for option in options:
            option = option.copy()
            option['label'] = _(option['label'])
            r.append(option)

        return r


    security.declarePublic('get_language_name')
    def get_language_name(self, id):
        """ """
        return get_language_name(id)


    #######################################################################
    # Management screens -- Messages
    #######################################################################
    security.declareProtected('Manage messages', 'manage_messages')
    manage_messages = LocalDTMLFile('ui/MC_messages', globals())


    security.declareProtected('Manage messages', 'get_translations')
    def get_translations(self, message):
        """ """
        return self._messages[message]


    security.declarePublic('get_url')
    def get_url(self, url, batch_start, batch_size, regex, lang, empty, **kw):
        """ """
        params = []
        for key, value in kw.items():
            params.append('%s=%s' % (key, quote(value)))

        params.extend(['batch_start:int=%d' % batch_start,
                       'batch_size:int=%d' % batch_size,
                       'regex=%s' % quote(regex),
                       'empty=%s' % (empty and 'on' or '')])

        if lang:
            params.append('lang=%s' % lang)

        return url + '?' + '&amp;'.join(params)

    def to_unicode(self, x):
        """
        In Zope the ISO-885p-1 encoding has an special status, normal strings
        are considered to be in this encoding by default.
        """
        if type(x) is StringType:
            x = unicode(x, 'iso-8859-1')
        return x


    def filter_sort(self, x, y):
        x = self.to_unicode(x)
        y = self.to_unicode(y)
        return cmp(x, y)


    security.declarePublic('filter')
    def filter(self, message, lang, empty, regex, batch_start, batch_size=15):
        """
        For the management interface, allows to filter the messages to show.
        """
        # Filter the messages
        regex = regex.strip()

        try:
            regex = re.compile(regex)
        except:
            regex = re.compile('')

        messages = []
        for m, t in self._messages.items():
            if regex.search(m) and (not empty or not t.get(lang, '').strip()):
                messages.append(m)
        messages.sort(self.filter_sort)

        # How many messages
        n = len(messages)

        # Calculate the start
        while batch_start >= n:
            batch_start = batch_start - batch_size

        if batch_start < 0:
            batch_start = 0

        # Select the batch to show
        batch_end = batch_start + batch_size
        messages = messages[batch_start:batch_end]

        # Get the message
        message_encoded = None
        if message is None:
            if messages:
                message = messages[0]
                message_encoded = self.message_encode(message)
        else:
            message_encoded = message
            message = self.message_decode(message)

        # Calculate the current message
        aux = []
        for x in messages:
            current = type(x) is type(message) \
                      and self.to_unicode(x) == self.to_unicode(message)
            aux.append({'message': x, 'current': current})

        return {'messages': aux,
                'n_messages': n,
                'batch_start': batch_start,
                'message': message,
                'message_encoded': message_encoded}


    security.declareProtected('Manage messages', 'manage_editMessage')
    def manage_editMessage(self, message, language, translation,
                           REQUEST, RESPONSE):
        """Modifies a message."""
        message_encoded = message
        message = self.message_decode(message_encoded)
        self.message_edit(message, language, translation)

        url = self.get_url(REQUEST.URL1 + '/manage_messages',
                           REQUEST['batch_start'], REQUEST['batch_size'],
                           REQUEST['regex'], REQUEST.get('lang', ''),
                           REQUEST.get('empty', 0),
                           msg=message_encoded,
                           manage_tabs_message=_('Saved changes.'))
        RESPONSE.redirect(url)


    security.declareProtected('Manage messages', 'manage_delMessage')
    def manage_delMessage(self, message, REQUEST, RESPONSE):
        """ """
        message = self.message_decode(message)
        self.message_del(message)

        url = self.get_url(REQUEST.URL1 + '/manage_messages',
                           REQUEST['batch_start'], REQUEST['batch_size'],
                           REQUEST['regex'], REQUEST.get('lang', ''),
                           REQUEST.get('empty', 0),
                           manage_tabs_message=_('Saved changes.'))
        RESPONSE.redirect(url)



    #######################################################################
    # Management screens -- Properties
    # Management screens -- Import/Export
    # FTP access
    #######################################################################
    security.declareProtected('View management screens',
                              'manage_propertiesForm')
    manage_propertiesForm = LocalDTMLFile('ui/MC_properties', globals())


    security.declareProtected('View management screens', 'manage_properties')
    def manage_properties(self, title, REQUEST=None, RESPONSE=None):
        """Change the Message Catalog properties."""
        self.title = title

        if RESPONSE is not None:
            RESPONSE.redirect('manage_propertiesForm')


    # Properties management screen
    security.declareProtected('View management screens', 'get_po_header')
    def get_po_header(self, lang):
        """ """
        # For backwards compatibility
        if not hasattr(self.aq_base, '_po_headers'):
            self._po_headers = PersistentMapping()

        return self._po_headers.get(lang, empty_po_header)


    security.declareProtected('View management screens', 'update_po_header')
    def update_po_header(self, lang,
                         last_translator_name=None,
                         last_translator_email=None,
                         language_team=None,
                         charset=None,
                         REQUEST=None, RESPONSE=None):
        """ """
        header = self.get_po_header(lang)

        if last_translator_name is None:
            last_translator_name = header['last_translator_name']

        if last_translator_email is None:
            last_translator_email = header['last_translator_email']

        if language_team is None:
            language_team = header['language_team']

        if charset is None:
            charset = header['charset']

        header = {'last_translator_name': last_translator_name,
                  'last_translator_email': last_translator_email,
                  'language_team': language_team,
                  'charset': charset}

        self._po_headers[lang] = header

        if RESPONSE is not None:
            RESPONSE.redirect('manage_propertiesForm')



    security.declareProtected('View management screens', 'manage_importExport')
    manage_importExport = LocalDTMLFile('ui/MC_importExport', globals())


    security.declarePublic('get_charsets')
    def get_charsets(self):
        """ """
        return charsets[:]


    security.declarePublic('manage_export')
    def manage_export(self, x, REQUEST=None, RESPONSE=None):
        """
        Exports the content of the message catalog either to a template
        file (locale.pot) or to an language specific PO file (<x>.po).
        """
        # Get the PO header info
        header = self.get_po_header(x)
        last_translator_name = header['last_translator_name']
        last_translator_email = header['last_translator_email']
        language_team = header['language_team']
        charset = header['charset']

        # PO file header, empty message.
        po_revision_date = time.strftime('%Y-%m-%d %H:%m+%Z',
                                         time.gmtime(time.time()))
        pot_creation_date = po_revision_date
        last_translator = '%s <%s>' % (last_translator_name,
                                       last_translator_email)

        if x == 'locale.pot':
            language_team = 'LANGUAGE <LL@li.org>'
        else:
            language_team = '%s <%s>' % (x, language_team)

        r = ['msgid ""',
             'msgstr "Project-Id-Version: %s\\n"' % self.title,
             '"POT-Creation-Date: %s\\n"' % pot_creation_date,
             '"PO-Revision-Date: %s\\n"' % po_revision_date,
             '"Last-Translator: %s\\n"' % last_translator,
             '"Language-Team: %s\\n"' % language_team,
             '"MIME-Version: 1.0\\n"',
             '"Content-Type: text/plain; charset=%s\\n"' % charset,
             '"Content-Transfer-Encoding: 8bit\\n"',
             '', '']


        # Get the messages, and perhaps its translations.
        d = {}
        if x == 'locale.pot':
            filename = x
            for k in self._messages.keys():
                d[k] = ""
        else:
            filename = '%s.po' % x
            for k, v in self._messages.items():
                try:
                    d[k] = v[x]
                except KeyError:
                    d[k] = ""

        # Generate the file
        def escape(x):
            quote_esc = re.compile(r'"')
            x = quote_esc.sub('\\"', x)

            trans = [('\n', '\\n'), ('\r', '\\r'), ('\t', '\\t')]
            for a, b in trans:
                x = x.replace(a, b)

            return x

        # Generate sorted msgids to simplify diffs
        dkeys = d.keys()
        dkeys.sort()
        for k in dkeys:
            r.append('msgid "%s"' % escape(k))
            v = d[k]
            r.append('msgstr "%s"' % escape(v))
            r.append('')

        if RESPONSE is not None:
            RESPONSE.setHeader('Content-type','application/data')
            RESPONSE.setHeader('Content-Disposition',
                               'inline;filename=%s' % filename)

        r2 = []
        for x in r:
            if type(x) is UnicodeType:
                r2.append(x.encode(charset))
            else:
                r2.append(x)

        return '\n'.join(r2)


    security.declareProtected('Manage messages', 'manage_import')
    def manage_import(self, lang, file, REQUEST=None, RESPONSE=None):
        """ """
        messages = self._messages

        if type(file) is StringType:
            content = file.split('\n')
        else:
            content = file.readlines()

        encoding, d = parse_po_file(content)

        # Load the data
        for k, v in d.items():
            k = ''.join(k)
            if k.strip():
                if not messages.has_key(k):
                    messages[k] = PersistentMapping()
                messages[k][lang] = ''.join(v[1])

        # Set the encoding (the full header should be loaded XXX)
        self.update_po_header(lang, charset=encoding)

        if REQUEST is not None:
            RESPONSE.redirect('manage_messages')


    def objectItems(self, spec=None):
        """ """
        for lang in self._languages:
            if not hasattr(self.aq_base, lang):
                self._setObject(lang, POFile(lang))

        r = MessageCatalog.inheritedAttribute('objectItems')(self, spec)
        return r


    #######################################################################
    # Backwards compatibility (XXX)
    #######################################################################

    hasmsg = message_exists
    hasLS = message_exists  # CMFLocalizer uses it




class POFile(SimpleItem):
    """ """

    security = ClassSecurityInfo()


    def __init__(self, id):
        self.id = id


    security.declareProtected('FTP access', 'manage_FTPget')
    def manage_FTPget(self):
        """ """
        return self.manage_export(self.id)


    security.declareProtected('Manage messages', 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """ """
        body = REQUEST['BODY']
        self.manage_import(self.id, body)
        RESPONSE.setStatus(204)
        return RESPONSE



InitializeClass(MessageCatalog)
InitializeClass(POFile)
