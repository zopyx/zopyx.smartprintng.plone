################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################


"""'
ZCML directives for zopyx.smartprintng.plone
"""

import os

from zope.interface import Interface
from zope.schema import TextLine 

import resources

class IResourcesDirectory(Interface):
    """ Used for specifying SmartPrintNG resources """

    name = TextLine(
        title=u"name",
        description=u'Resource name',
        default=u"",
        required=True)

    directory = TextLine(
        title=u"Directory name",
        description=u'Directory path containing template, styles and other resources',
        default=u"",
        required=True)


def resourcesDirectory(_context, name, directory):

    # path of ZCML file
    zcml_filename = _context.info.file
    directory = os.path.join(os.path.dirname(zcml_filename), directory)
    resources.registerResource(name, directory)

