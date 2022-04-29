################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################

from ..compatible import InitializeClass
from Products.Five.browser import BrowserView

class HTMLView(BrowserView):
    """ This view renders a HMTL fragment for the configured content type """

    def collect(self, html):

        html.append('<div class="type-topic">')
        for brain in self.context.queryCatalog():
            obj = brain.getObject()
            if view := obj.restrictedTraverse('@@asHTML', None):
                html.append('<div class="topic-item">')
                html.append(view())
            else:
                html.append('<div class="topic-item">')
                html.append('<span class="aggregation-error">new view for %s (%s) found</span>' %
                            (obj.absolute_url(1), obj.portal_type))
            html.append('</div>')
        html.append('</div>')

    def __call__(self, *args, **kw):
        """ Collector for topic content """
        html = []
        self.collect(html)
        return ''.join(html)

InitializeClass(HTMLView)

