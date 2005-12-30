# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
"""Localizer XML Adapter.

Initializes the tool and imports the message catalogs.
"""

import os
import sys
import errno
from Acquisition import aq_parent, aq_inner
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers

from zope.component import adapts
from zope.interface import implements
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.Localizer.interfaces import ILocalizerTool
from Products.Localizer.interfaces import IMessageCatalog


TOOL = 'Localizer'
NAME = 'localizer'

def importLocalizer(context):
    """Import Localizer and message catalogs from XML files.
    """
    site = context.getSite()
    tool = getToolByName(site, TOOL)
    importObjects(tool, '', context)


class LocalizerToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers):
    """XML importer for a Localizer tool.
    """

    adapts(ILocalizerTool, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME
    name = NAME

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeObjects()

        # Initialize the languages from the portal settings.
        localizer = self.context
        site = aq_parent(aq_inner(localizer))
        languages = site.getProperty('available_languages', ())
        if not languages:
            languages = ('en',)
        # Not really used
        if 'en' in languages:
            default_language = 'en'
        else:
            default_language = languages[0]
        localizer._languages = tuple(languages)
        localizer._default_language = default_language

        self._initObjects(node)

        self._logger.info("Localizer tool imported.")


class MessageCatalogXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    """XML importer for a Localizer Message Catalog.
    """

    adapts(IMessageCatalog, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeTranslations()
        self._initTranslations(node)
        self._logger.info("%s message catalog imported." %
                          self.context.getId())

    def _purgeTranslations(self):
        pass

    def _initTranslations(self, node):
        catalog = self.context
        localizer = aq_parent(aq_inner(catalog))

        # Set languages same as parent
        catalog._languages = localizer._languages
        catalog._default_language = localizer._default_language

        for child in node.childNodes:
            if child.nodeName != 'translations':
                continue

            product = str(child.getAttribute('product'))
            if child.hasAttribute('file'):
                filename = str(child.getAttribute('file'))
                if not '%s' in filename:
                    raise ValueError("No '%%s' in filename %r" % filename)
            else:
                filename = '%s.po'

            for language in catalog._languages:
                file = self._getPOFile(product, filename, language)
                if file is None:
                    continue
                if not language in catalog.get_languages():
                    catalog.manage_addLanguage(language)
                catalog.manage_import(language, file)

    def _getPOFile(self, product, filename, language):
        filename = filename % language
        product_module = sys.modules.get('Products.%s' % product)
        if product_module is None:
            raise ValueError("No product %r" % product)
        for dirname in ('i18n',):
            # XXX this is not egg-safe
            product_path = os.path.dirname(product_module.__file__)
            path = os.path.join(product_path, dirname, filename)
            try:
                return open(path)
            except IOError, e:
                if e.errno != errno.ENOENT: raise
        return None
