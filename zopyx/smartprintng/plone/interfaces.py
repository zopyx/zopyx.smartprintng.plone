from zope.interface import Interface

class IPPContent(Interface):
    """ Marker interface for Plone content to be considered as
        content for Produce & Publish.
    """

class IArchiveFolder(Interface):
    """ Marker interface for folder with archived content that will
        be ignored inside @@asHTML
    """
