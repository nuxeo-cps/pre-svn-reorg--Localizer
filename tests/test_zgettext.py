# Localizer, Zope product that provides internationalization services
# Copyright (C) 2001, 2002 J. David Ibáñez <j-david@noos.fr>

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
Test suite for the zgettext.py script.
"""

__version__ = "$Revision$"


# Add the Localizer product directory to the path
import os, sys
sys.path.append(os.path.join(sys.path[0], '../'))

import zgettext


import unittest
from unittest import TestCase, TestSuite, TextTestRunner


class ParsePOFileTestCase(TestCase):
    def test_case1(self):
        """Test for newlines."""
        content = [r'msgid "Add"',
                   r'msgstr "Añadir\n"']

        encoding, x = zgettext.parse_po_file(content)
        assert x == {('Add',): ([], ['Añadir\n'])}

    def test_case2(self):
        """Test for multiple lines"""
        content = ['msgid "Hello world"',
                   'msgstr ""',
                   '"Hola "',
                   '"mundo"']

        encoding, x = zgettext.parse_po_file(content)
        assert x == {('Hello world',): ([], ['', 'Hola ', 'mundo'])}

    def test_case3(self):
        """Test for double quotes."""
        content = ['msgid "test"',
                   r'msgstr "Esto es una \"prueba\""']

        encoding, x = zgettext.parse_po_file(content)
        assert x == {('test',): ([], ['Esto es una "prueba"'])}



class GettextTagTestCase(TestCase):
    def test_caseSimple(self):
        """Test the 'dtml-gettext' tag without any option."""
        text = "<dtml-gettext>\n" \
               "  message\n" \
               "</dtml-gettext>"

        assert zgettext.parse_dtml(text) == ['message']

    def test_caseVerbatim(self):
        """Test the 'dtml-gettext' tag when using the 'verbatim' option."""
        text = "<dtml-gettext verbatim>\n" \
               "  message\n" \
               "</dtml-gettext>"

        assert zgettext.parse_dtml(text) == ['\n  message\n']



if __name__ == '__main__':
    unittest.main()
