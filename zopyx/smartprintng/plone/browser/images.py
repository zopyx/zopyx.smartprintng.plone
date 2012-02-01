################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################

"""
Image resolver
"""


from urllib2 import unquote, Request, urlopen, HTTPError
from urlparse import urlparse 
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interfaces import IATImage
from Products.Archetypes.Field import Image
from plone.app.imaging.scale import ImageScale
from zopyx.smartprintng.plone.logger import LOG

def resolveImage(context, src):
    """ Try to resolve an image based on its src which 
        can be a relative URL, an absolute URL or an URL
        using UIDs. Image scales can be annotated through
        image_<scale> or using the newer plone.app.imaging
        mechanism. Much fun :-P
    """

    ref_catalog = getToolByName(context, 'reference_catalog')
    parse_result = urlparse(unquote(src))
    path = str(parse_result.path)
    img_obj = None

    if path.startswith('resolveuid'):
        # can be resolveuid/<uid>/@@images/image/preview
        path_parts = path.split('/')
        img_obj = ref_catalog.lookupObject(path_parts[1])
    else:

        candidates = [path, path[1:]] # with and without leading '/' 
        # check for a possible URL redirection
        if src.startswith('http'):
            req = Request(src)

            try:
                result = urlopen(req)
            except HTTPError:
               	result = None 

            if result and result.url != src: 
                # a redirection happened
                parse_result2 = urlparse(unquote(result.url))
                path2 = str(parse_result2.path)
                candidates.extend([path2, path2[1:]])

        for p in candidates:
            img_obj = context.restrictedTraverse(p, None)
            print p
            print img_obj

            if img_obj:
                if img_obj.portal_type in ('Image',):
                    # check if current image is a scale (having a parent image)
                    if IATImage.providedBy(img_obj.aq_parent):
                        img_obj = img_obj.aq_parent
                    break
                elif isinstance(img_obj, ImageScale):
                    img_obj = img_obj.aq_parent
                    break
                elif isinstance(img_obj.aq_parent, Image):
                    break

            else:
                img_obj = None
    return img_obj


def existsExternalImageUrl(url):
    """ Check if the external URL exists (by issuing a 
        HTTP request.
    """

    class HeadRequest(Request):
        def get_method(self):
            return "HEAD"

    if not url.startswith('http'):
        return False

    try:
        urlopen(HeadRequest(url))
        return True
    except Exception, e: 
        LOG.warn('External(?) image reference not found (%s)' % e)
        return False

