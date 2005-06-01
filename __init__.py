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
        # XXX
        # Some people has reported that sometimes a KeyError exception is
        # raised in the previous line, I haven't been able to reproduce it.
        # This try/except clause seems to work. I'd prefer to understand
        # what is happening.
        LOG('Localizer', PROBLEM,
            "The thread number %s don't has a request object associated." % id)

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
# For Zope 2.5.1 (unsupported), patch appropriately.
# For Zope 2.6b1+
#   - if LOCALIZER_USE_ZOPE_UNICODE, use standard Zope Unicode handling,
#   - otherwise use Localizer's version of StringIO for ZPT and TAL.
#

from TAL.TALInterpreter import TALInterpreter
patch_251 = not hasattr(TALInterpreter, 'StringIO')

if patch_251:
    try:
        # Patched 2.5.1 should have ustr in __builtins__
        ustr
    except NameError:
        LOG('Localizer', ERROR, (
            "A Unicode-aware version of Zope is needed by Localizer.\n"
            "Please consult the documentation for a patched version\n"
            "of Zope 2.5.1, or use Zope 2.6b1 or later."))
        raise

    # 3.1 - Fix two instances where ustr must be used

    from Products.PageTemplates.TALES import Context, Default

    def evaluateText(self, expr, _None=None):
        text = self.evaluate(expr)
        if text is Default or text is _None:
            return text
        return ustr(text) # Use "ustr" instead of "str"
    Context.evaluateText = evaluateText

    def do_insertStructure_tal(self, (expr, repldict, block)):
        structure = self.engine.evaluateStructure(expr)
        if structure is None:
            return
        if structure is self.Default:
            self.interpret(block)
            return
        text = ustr(structure)  # Use "ustr" instead of "str"
        if not (repldict or self.strictinsert):
            # Take a shortcut, no error checking
            self.stream_write(text)
            return
        if self.html:
            self.insertHTMLStructure(text, repldict)
        else:
            self.insertXMLStructure(text, repldict)
    TALInterpreter.do_insertStructure_tal = do_insertStructure_tal
    TALInterpreter.bytecode_handlers_tal["insertStructure"] = do_insertStructure_tal

# 3.2 - Fix uses of StringIO with a Unicode-aware StringIO

from StringIO import StringIO as originalStringIO
from types import UnicodeType
class LocalizerStringIO(originalStringIO):
    def write(self, s):
        if isinstance(s, UnicodeType):
            try:
                response = get_request().RESPONSE
                s = response._encode_unicode(s)
            except AttributeError:
                # not an HTTPResponse
                pass
        originalStringIO.write(self, s)



from Products.PageTemplates.PageTemplate import PageTemplate


if not patch_251:
    import os
    if os.environ.get('LOCALIZER_USE_ZOPE_UNICODE'):
        LOG('Localizer', DEBUG, 'No Unicode patching')
        # Use the standard Zope way of dealing with Unicode
    else:
        LOG('Localizer', DEBUG, 'Unicode patching for Zope 2.6b1+')
        # Patch the StringIO method of TALInterpreter and PageTemplate
        def patchedStringIO(self):
            return LocalizerStringIO()
        TALInterpreter.StringIO = patchedStringIO
        PageTemplate.StringIO = patchedStringIO

else:
    LOG('Localizer', DEBUG, 'Unicode patching for Zope 2.5.1')
    # Patch uses of StringIO in Zope 2.5.1
    def no_tag(self, start, program):
        state = self.saveState()
        self.stream = stream = LocalizerStringIO()
        self._stream_write = stream.write
        self.interpret(start)
        self.restoreOutputState(state)
        self.interpret(program)
    TALInterpreter.no_tag = no_tag

    def do_onError_tal(self, (block, handler)):
        state = self.saveState()
        self.stream = stream = LocalizerStringIO()
        self._stream_write = stream.write
        try:
            self.interpret(block)
        except self.TALESError, err:
            self.restoreState(state)
            engine = self.engine
            engine.beginScope()
            err.lineno, err.offset = self.position
            engine.setLocal('error', err)
            try:
                self.interpret(handler)
            finally:
                err.takeTraceback()
                engine.endScope()
        else:
            self.restoreOutputState(state)
            self.stream_write(stream.getvalue())
    TALInterpreter.do_onError_tal = do_onError_tal

    from Products.PageTemplates.PageTemplate import PTRuntimeError
    from Products.PageTemplates.PageTemplate import Z_DEBUG_MODE
    from Products.PageTemplates.PageTemplate import getEngine
    import pprint
    def pt_render(self, source=0, extra_context={}):
        """Render this Page Template"""
        if self._v_errors:
            raise PTRuntimeError, 'Page Template %s has errors.' % self.id
        output = LocalizerStringIO()
        c = self.pt_getContext()
        c.update(extra_context)
        if Z_DEBUG_MODE:
            __traceback_info__ = pprint.pformat(c)

        TALInterpreter(self._v_program, self._v_macros,
                       getEngine().getContext(c),
                       output,
                       tal=not source, strictinsert=0)()
        return output.getvalue()
    PageTemplate.pt_render = pt_render

del patch_251

#################################################################
# Standard intialization code
#################################################################

from ImageFile import ImageFile
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
