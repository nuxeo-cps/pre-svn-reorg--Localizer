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
LocalContent
"""

__version__ = "$Revision$"


# Zope
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager    
from Products.ZCatalog.CatalogPathAwareness import CatalogAware


# Localizer
from LocalFiles import LocalDTMLFile
from LocalPropertyManager import LocalPropertyManager, LocalProperty
import Gettext


_ = Gettext.translation(globals())
N_ = Gettext.dummy



manage_addLocalContentForm = LocalDTMLFile('ui/LocalContent_add', globals())
def manage_addLocalContent(self, id, languages, REQUEST=None):
    """ """
    self._setObject(id, LocalContent(id, tuple(languages)))

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


class LocalContent(CatalogAware, LocalPropertyManager, PropertyManager,
                   SimpleItem):
    """ """

    meta_type = 'LocalContent'

    # Properties metadata
    _local_properties_metadata = ({'id': 'title', 'type': 'string'},
                                  {'id': 'body', 'type': 'text'})

    _properties = ()

    title = LocalProperty('title')   # Override title from SimpleItem
    body = LocalProperty('body')


    def manage_options(self):
        """ """
        options = LocalContent.inheritedAttribute('manage_options')(self) \
                  + PropertyManager.manage_options \
                  + SimpleItem.manage_options

        r = []
        for option in options:
            option = option.copy()
            option['label'] = _(option['label'])
            r.append(option)

        return r


    def __init__(self, id, languages):
        self.id = id
        self._languages = languages


    index_html = None     # Prevent accidental acquisition


    def __call__(self, client=None, REQUEST=None, RESPONSE=None, **kw):
        if REQUEST is None:
            REQUEST = self.REQUEST

        # Get the template to use
        template_id = 'default_template'
        if hasattr(self.aq_base, 'default_template'):
            template_id = self.default_template

        # Render the object
        template = getattr(self.aq_parent, template_id)
        template = template.__of__(self)
        return apply(template, ((client, self), REQUEST), kw)


    # Override some methods to be sure that LocalContent objects are
    # reindexed when changed.
    def _setLocalPropValue(self, id, lang, value):
        LocalContent.inheritedAttribute('_setLocalPropValue')(self, id, lang,
                                                              value)

        self.reindex_object()

    def _delLocalProperty(self, id):
        LocalContent.inheritedAttribute('_delLocalProperty')(self, id)

        self.reindex_object()
