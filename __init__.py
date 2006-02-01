# -*- coding: iso-8859-15 -*-

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


"""Localizer"""
__version__ = "$Revision$"


from zLOG import LOG, ERROR, INFO, PROBLEM, DEBUG




#################################################################
# Patches start here!!!
#################################################################


# PATCH 1
#
# Makes REQUEST available from the Globals module.
#
# It's needed because context is not available in the __of__ method,
# so we can't get REQUEST with acquisition. And we need REQUEST for
# local properties (see LocalPropertyManager.pu).
#
# This patch is at the beginning to be sure code that requires it
# doesn't breaks.
#
# This pach is inspired in a similar patch by Tim McLaughlin, see
# "http://dev.zope.org/Wikis/DevSite/Proposals/GlobalGetRequest".
# Thanks Tim!!
#

from thread import get_ident
from ZPublisher import Publish, mapply

def get_request():
    """Get a request object"""
    return Publish._requests.get(get_ident(), None)

def new_publish(request, module_name, after_list, debug=0):
    id = get_ident()
    Publish._requests[id] = request
    x = Publish.old_publish(request, module_name, after_list, debug)
    try:
        del Publish._requests[id]
    except KeyError:
        # When a ConflictError happened, the recursive call to publish
        # implies that _requests has already been cleared
        pass

    return x


import Globals
patch = 0
if not hasattr(Globals, 'get_request'):
    # Apply patch
    Publish._requests = {}
    Publish.old_publish = Publish.publish
    Publish.publish = new_publish

    Globals.get_request = get_request

    # First import (it's not a refresh operation).
    # We need to apply the patches.
    patch = 1


# PATCH 2
#
# Adds the variables AcceptLanguage and AcceptCharset to the REQUEST.
# They provide a higher level interface than HTTP_ACCEPT_LANGUAGE and
# HTTP_ACCEPT_CHARSET.
#


# Apply the patch
from Accept import AcceptCharset, AcceptLanguage
from ZPublisher.HTTPRequest import HTTPRequest
def new_processInputs(self):
    HTTPRequest.old_processInputs(self)

    request = self

    # Set the AcceptCharset variable
    accept = request['HTTP_ACCEPT_CHARSET']
    self.other['AcceptCharset'] = AcceptCharset(request['HTTP_ACCEPT_CHARSET'])

    # Set the AcceptLanguage variable
    # Initialize witht the browser configuration
    accept_language = request['HTTP_ACCEPT_LANGUAGE']
    # Patches for user agents that don't support correctly the protocol
    user_agent = request['HTTP_USER_AGENT']
    if user_agent.startswith('Mozilla/4') and user_agent.find('MSIE') == -1:
        # Netscape 4.x
        q = 1.0
        langs = []
        for lang in [ x.strip() for x in accept_language.split(',') ]:
            langs.append('%s;q=%f' % (lang, q))
            q = q/2
        accept_language = ','.join(langs)

    accept_language = AcceptLanguage(accept_language)

    self.other['AcceptLanguage'] = accept_language
    # XXX For backwards compatibility
    self.other['USER_PREF_LANGUAGES'] = accept_language


if patch:
    HTTPRequest.old_processInputs = HTTPRequest.processInputs
    HTTPRequest.processInputs = new_processInputs


# PATCH 3
#
# Enables support of Unicode in ZPT.
#   - if LOCALIZER_USE_ZOPE_UNICODE, use standard Zope Unicode handling,
#   - otherwise use Localizer's version of StringIO for ZPT and TAL.
#

# Fix uses of StringIO with a Unicode-aware StringIO

from TAL.TALInterpreter import FasterStringIO
class LocalizerStringIO(FasterStringIO):
    def write(self, s):
        if isinstance(s, unicode):
            try:
                response = get_request().RESPONSE
                s = response._encode_unicode(s)
            except AttributeError:
                # not an HTTPResponse
                pass
        FasterStringIO.write(self, s)

from Products.PageTemplates.PageTemplate import PageTemplate
from TAL.TALInterpreter import TALInterpreter
import os

if os.environ.get('LOCALIZER_USE_ZOPE_UNICODE'):
    LOG('Localizer', DEBUG, 'No Unicode patching')
    # Use the standard Zope way of dealing with Unicode
else:
    LOG('Localizer', DEBUG, 'Unicode patching')
    # Patch the StringIO method of TALInterpreter and PageTemplate
    def patchedStringIO(self):
        return LocalizerStringIO()
    TALInterpreter.StringIO = patchedStringIO
    PageTemplate.StringIO = patchedStringIO

#################################################################
# Standard intialization code
#################################################################

from App.ImageFile import ImageFile
from DocumentTemplate.DT_String import String
import ZClasses

import Localizer, LocalContent, MessageCatalog, LocalFolder
from LocalFiles import LocalDTMLFile, LocalPageTemplateFile
from LocalPropertyManager import LocalPropertyManager, LocalProperty
from GettextTag import GettextTag


misc_ = {'arrow_left': ImageFile('img/arrow_left.gif', globals()),
         'arrow_right': ImageFile('img/arrow_right.gif', globals()),
         'eye_opened': ImageFile('img/eye_opened.gif', globals()),
         'eye_closed': ImageFile('img/eye_closed.gif', globals())}



def initialize(context):
    # Register the Localizer
    context.registerClass(Localizer.Localizer,
                          constructors = (Localizer.manage_addLocalizerForm,
                                          Localizer.manage_addLocalizer),
                          icon = 'img/localizer.gif')

    # Register LocalContent
    context.registerClass(
        LocalContent.LocalContent,
        constructors = (LocalContent.manage_addLocalContentForm,
                        LocalContent.manage_addLocalContent),
        icon='img/local_content.gif')

    # Register MessageCatalog
    context.registerClass(
        MessageCatalog.MessageCatalog,
        constructors = (MessageCatalog.manage_addMessageCatalogForm,
                        MessageCatalog.manage_addMessageCatalog),
        icon='img/message_catalog.gif')

    # Register LocalFolder
    context.registerClass(
        LocalFolder.LocalFolder,
        constructors = (LocalFolder.manage_addLocalFolderForm,
                        LocalFolder.manage_addLocalFolder),
        icon='img/local_folder.gif')

    # Register LocalPropertyManager as base class for ZClasses
    ZClasses.createZClassForBase(LocalPropertyManager, globals(),
                                 'LocalPropertyManager',
                                 'LocalPropertyManager')


    context.registerHelp()

    # Register the dtml-gettext tag
    String.commands['gettext'] = GettextTag
