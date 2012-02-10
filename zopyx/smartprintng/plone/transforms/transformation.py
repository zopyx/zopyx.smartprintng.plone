################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################

""" HTML transformation classes (based on lxml.html) """

import os
import re
import urllib2
import cgi
import tempfile
import inspect
import uuid
import time
import lxml.html

import PIL
from lxml.cssselect import CSSSelector
from Products.CMFCore.utils import getToolByName
from zopyx.smartprintng.plone.logger import LOG
from zopyx.smartprintng.plone.browser.images import resolveImage
from Products.CMFPlone.utils import safe_hasattr

_marker = object()
TRANSFORMATIONS = dict()

url_match = re.compile(r'^(http|https|ftp)://')
leading_numbers = re.compile('^(\d*)', re.UNICODE|re.MULTILINE)
ALL_HEADINGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'h10')

def nodeProcessed(node):
    if node.get('processed'):
        return True

def registerTransformation(method):
    """ Decorator to register a method as a transformation"""
    name = method.__name__
    TRANSFORMATIONS[name] = method

def availableTransformations():
    return TRANSFORMATIONS.keys()

def hasTransformations(transformations):
    available_transformations = availableTransformations()
    for t in transformations:
        if not t in available_transformations:
            return False
    return True

class Transformer(object):

    def __init__(self, transformation_names, context=None, destdir=None):
        self.transformation_names = transformation_names
        self.context = context
        self.destdir = destdir

    def __call__(self, html, input_encoding=None, output_encoding=unicode, return_body=False):

        if not isinstance(html, unicode):
            if not input_encoding:
                raise TypeError('Input data must be unicode')
            html = unicode(html, input_encoding)

        html = html.strip()
        if not html:
            return u''

        root = lxml.html.fromstring(html)

        for name in self.transformation_names:
            method = TRANSFORMATIONS.get(name)
            params = dict(context=self.context,
                          request=getattr(self.context, 'REQUEST', None),
                          destdir=self.destdir,
                          )
            if method is None:
                raise ValueError('No transformation "%s" registered' % name)

            ts = time.time()
            argspec = inspect.getargspec(method)
            if isinstance(argspec, tuple):
                args = argspec[0] # Python 2.4
            else:
                args = argspec.args
            if 'params' in args:
                method(root, params)
            else:
                method(root)

            LOG.info('Transformation %-30s: %3.6f seconds' % (name, time.time()-ts))

        if return_body:
            body = root.xpath('//body')[0]
            html_new = body.text + u''.join([lxml.html.tostring(b, encoding=output_encoding) for b in body])

        else:
            html_new = lxml.html.tostring(root, encoding=output_encoding)
            if html_new.startswith('<div>') and html_new.endswith('</div>'):
                html_new = html_new[5:-6].strip()

        return html_new.strip()

def xpath_query(node_names):
    if not isinstance(node_names, (list, tuple)):
        raise TypeError('"node_names" must be a list or tuple (not %s)' % type(node_names))
    return './/*[%s]' % ' or '.join(['name()="%s"' % name for name in node_names])

@registerTransformation
def dummyTransformation(root):
    """ Dummy transformation doing nothing """
    pass

@registerTransformation
def cleanupEmptyElements(root, tags=['div']):
    """ Remove tags with empty subtree (no text in subtree) """    
    for node in root.xpath(xpath_query(tags)):
        if not node.text_content().strip():
            node.getparent().remove(node)

UUID4TAGS = ALL_HEADINGS + ('img', 'table', 'li', 'dt', 'ul', 'ol', 'dl')
@registerTransformation
def addUUIDs(root, tags=UUID4TAGS):
    """ Add a unique/random UUID to all (specified) tags """
    for node in root.xpath(xpath_query(tags)):
        node_id = node.get('id', _marker)
        if node_id is _marker:
            node.attrib['id'] = str(uuid.uuid4())


@registerTransformation
def addUUIDsToAllTags(root, tags=UUID4TAGS):
    """ Add a unique/random UUID to all tags """
    for node in root.xpath('//*'):
        node_id = node.get('id', _marker)
        if node_id is _marker:
            node.attrib['id'] = str(uuid.uuid4())

@registerTransformation
def shiftHeadings(root):
    """ H1 -> H2, H2 -> H3.... """
    for node in root.xpath(xpath_query(ALL_HEADINGS)):
        level = int(node.tag[1:])
        node.tag = 'h%d' % (level+1)

@registerTransformation
def cleanupTables(root):
    """ Remove crap from table markup """

    # adjust table class
    for table in root.xpath(xpath_query(('table',))):

        # remove col/colgroup tags
        for node in table.xpath(xpath_query(('col', 'colgroup'))):
            node.getparent().remove(node)

        # remove attribute crap
        for node in table.xpath('//*'):
            for name in ('border', 'width', 'bordercolor', 'cellspacing', 'cellpadding'):
                if name in node.attrib:        
                    del node.attrib[name]

        # adjust table class
        table.attrib['class'] = 'plain grid'

@registerTransformation
def adjustImagesAfterOfficeImport(root):
    """ This method is called after the conversion using
        Open-Office. All images must be transformed to
        scale 'medium'. In addition we remove all other attributes.
    """

    for img in root.xpath(xpath_query(('img',))):
        img.attrib['src'] = img.attrib['src'] + '/image_medium'
        for k in img.attrib.keys()[:]:
            if k not in ('src',):
                del img.attrib[k]

@registerTransformation
def fixHeadingsAfterOfficeImport(root):
    """ Remove leading section numbers from headings """

    regex = re.compile(r'^([\d*\.]*)', re.UNICODE)
    for heading in root.xpath(xpath_query(ALL_HEADINGS)):
        text = heading.text_content().strip()
        text = regex.sub('', text)
        heading.clear()
        heading.text = text.strip()

@registerTransformation
def ignoreHeadingsForStructure(root):
    """ Inspect all div.ignore-headings-for-structure and
        convert all headings into div.level-hX. The purpose
        of this method is to exclude generated HTML snippets
        from being relevant for the overall structure since
        all headings are relevant for numbering and the table of
        contents.
    """

    for div in root.xpath('//div'):
        cls = div.get('class', '')
        if not 'ignore-headings-for-structure' in cls:
            continue

        for heading in div.xpath(xpath_query(ALL_HEADINGS)):
            level = int(heading.tag[1:])
            heading.tag = 'div'
            heading.attrib['class'] = 'heading-level-%d' % level
        

@registerTransformation
def adjustAnchorsToLinkables(root):
    """ Links to linkables (tables, headings and images) in the P&P source
        files are stored as "resolveuid/<UID><id-of-linkable>". Since the PDF
        conversion is based on a single HTML file we to replace the href
        values with the value of <id-of-linkable>.
        (used for PDF only)
    """

    # first collect all possible target link-id
    link_ids = [node.get('id') for node in root.xpath('//*[@id]')]

    # now search for links 
    for link in root.xpath('//a'):
        href = link.get('href')
        # check for the typical internal link pattern
        if href and href.startswith('resolveuid') and '#' in href:
            ref_id = href.rsplit('#')[-1]
            if ref_id in link_ids:
                # replace target link if it exists                         
                link.attrib['href'] = '#%s' % ref_id
            else:
                # otherwise convert the link into a span
                text = link.text_content()
                link.tag = 'span'
                link.text = text
                del link.attrib['href']

@registerTransformation
def cleanupForEPUB(root):
    """ Run some cleanup transformation in order to make Calibre
        (almost) happy.
    """

    # set class=chapter for all h1+h2 node. This is the default trigger
    # for the structure detection of Calibre
    # The epub_pagebreak parameter is submitted as h1|h2|... string from the
    # epub conversion form
#    break_at = params['request'].get('epub_pagebreak', 'h1').split('|')
    break_at = ('h1', 'h2')
    for node in root.xpath(xpath_query(break_at)):
        node.attrib['class'] = 'chapter'

    # remove div.contentinfo (containing the EDIT link)
    # remove table list
    # remove image list
    selector = CSSSelector('div.contentinfo')
    for div in selector(root):
        div.getparent().remove(div)

    selector = CSSSelector('div#table-list,div#images-lists,div#table-of-contents')
    for div in selector(root):
        div.getparent().remove(div)

    # image captions
    selector = CSSSelector('span.image-caption-with-title')
    for span in selector(root):
        span.getparent().remove(span)

    # all image 'src' attributes must be prefixed with 'preview_'
    for img in root.xpath('//img'):
        src = img.get('src')
        if src.endswith('image_preview'):
            img.attrib['src'] = 'preview_' + src.split('/')[0]
        else:
            img.attrib['src'] = 'preview_' + src

@registerTransformation
def makeImagesLocal(root, params):
    """ deal with internal and external image references """

    ref_catalog = getToolByName(params['context'], 'reference_catalog')
    destdir = params['destdir']
    ini_filename = os.path.join(destdir, 'images.ini')
    fp_ini = file(ini_filename, 'w')
    images_seen = dict()

    for document_node in CSSSelector('div.level-0')(root):
        document_obj = ref_catalog.lookupObject(document_node.get('uid'))

        for img in document_node.xpath(xpath_query(['img'])):
            # 'internal' images are marked with class="internal resource"
            # in order to prevent image fetching later on
            if 'internal-resource' in (img.get('class') or '') or img.get('processed'):
                continue
            
            scale = ''
            src = img.get('src')
            LOG.info('Introspecting image: %s' % src)

            img_obj = resolveImage(document_obj, src)

            if img_obj is None:
                # like some external image URL
                LOG.info('  Remote image fetching: %s' % src)

                try:
                    response = urllib2.urlopen(str(src))
                    img_data = response.read()
                    img_basename = src.split('/')[-1]                    
                except (ValueError, urllib2.URLError), e:
                    LOG.warn('No image found: %s - removed from output (reason: %s)' % (src, e))
                    img.getparent().remove(img)
                    continue 

                tmpname = tempfile.mktemp(dir=destdir) + '_' + img_basename
                file(tmpname, 'wb').write(img_data)
                # write supplementary information to an .ini file per image
                img_id = os.path.basename(tmpname)
                print >>fp_ini, '[%s]' % img_id
                print >>fp_ini, 'id = %s' % img_id
                print >>fp_ini, 'filename = %s' % tmpname
                print >>fp_ini, 'url = %s' % str(src)
                print >>fp_ini, 'scale = %s' % ''
                img.attrib['src'] = img_id
                img.attrib['originalscale'] = ''
                images_seen[src] = img_id
                LOG.info('  Assigned new id: %s' % img_id)
                continue

            # resolved did find a local image
            LOG.info('  Local processing: %s' % src)
            img_filename = images_seen.get(src)
            if not img_filename:
                img_data = None
                for attr in ['data', '_data']:
                    try:
                        img_data = str(getattr(img_obj, attr))
                        continue
                    except AttributeError:
                        pass
                if img_data is None:
                    LOG.warn('No image found: %s - removed from output' % src)
                    img.extract()
                    continue

                tmpname = tempfile.mktemp(dir=destdir)
                file(tmpname, 'wb').write(img_data)
                # determine graphic format using PIL
                pil_image = PIL.Image.open(tmpname)
                format = pil_image.format.lower()

                # generate unique and speaking image names
                img_id = img_obj.getId()
                dest_img_name = os.path.join(destdir, img_id)
                if not os.path.exists(dest_img_name):
                    os.rename(tmpname, dest_img_name)
                else:                    
                    running = True 
                    count = 0
                    while running:
                        img_id = os.path.splitext(img_obj.getId())[0]
                        img_id = '%s-%d.%s' % (img_id, count, format)
                        dest_img_name = os.path.join(params['destdir'], img_id)
                        if not os.path.exists(dest_img_name):
                            os.rename(tmpname, dest_img_name)
                            tmpname = dest_img_name
                            running = False
                            del pil_image
                        else:
                            count += 1
                LOG.info('  Exported to: %s' % dest_img_name)

                # now also export the preview scale as well 
                # (needed for EPUB export/conversion)
                preview_filename = os.path.join(os.path.dirname(dest_img_name), 'preview_' + os.path.basename(dest_img_name))
                preview_img = img_obj.Schema().getField('image').getScale(img_obj, scale='preview')
                if preview_img == '': # no scales created?
                    img_obj.Schema().getField('image').createScales(img_obj)
                    preview_img = img_obj.Schema().getField('image').getScale(img_obj, scale='preview')

                if safe_hasattr(preview_img, 'data'):
                    file(preview_filename, 'wb').write(str(preview_img.data))                                                    
                    LOG.info('  Exported preview scale to: %s' % preview_filename)

                # determine image scale from 'src' attribute
                src_parts = src.split('/')
                if '@@images' in src_parts:
                    scale = src_parts[-1]
                elif src_parts[-1].startswith('image_'):
                    scale = src_parts[-1][6:]

                print >>fp_ini, '[%s]' % os.path.basename(dest_img_name)
                print >>fp_ini, 'filename = %s' % dest_img_name 
                print >>fp_ini, 'id = %s' % img_id 
                print >>fp_ini, 'title = %s' % img_obj.Title()
                print >>fp_ini, 'description = %s' % img_obj.Description()
                print >>fp_ini, 'scale = %s' % scale
                images_seen[src] = os.path.basename(dest_img_name)
                img_filename = dest_img_name

            img.attrib['src'] = os.path.basename(img_filename)         
            LOG.info('  Assigned new id: %s' % img.get('src'))
            img.attrib['originalscale'] = scale
            img.attrib['style'] = 'width: 100%'  # need for PrinceXML8
            img.attrib['processed'] = '1' 

            # image scaling
            # add content-info debug information
            # don't add scale as style since the outer image-container
            # has the style set
            try:
                pdf_scale = img_obj.getField('pdfScale').get(img_obj)
            except AttributeError:
                pdf_scale = 100
            img.attrib['scale'] = str(pdf_scale)

            # now move <img> tag into a dedicated <div>
            div = lxml.html.Element('div')
            div.attrib['class'] = 'image-container'
            div.attrib['style'] = 'width: %d%%' % pdf_scale
            div.attrib['scale'] = str(pdf_scale)
            new_img =  lxml.html.Element('img')
            new_img.attrib.update(img.attrib.items())
            div.insert(0, new_img)

            displayInline_field = img_obj.getField('displayInline')
            if displayInline_field and not displayInline_field.get(img_obj):

                # image caption
                img_caption_position = img_obj.getField('captionPosition').get(img_obj)
                img_caption = lxml.html.Element('div')
                img_caption.attrib['class'] = 'image-caption'                       

                # exclude from image enumeration
                exclude_field = img_obj.getField('excludeFromImageEnumeration')
                if exclude_field and not exclude_field.get(img_obj):

                    # add description
                    span = lxml.html.Element('span')
                    description = unicode(img_obj.Description(), 'utf-8')
                    class_ = description and 'image-caption-description image-caption-with-description' or \
                                             'image-caption-description image-caption-without-description'
                    if description:
                        span.text = description
                    span.attrib['class'] = class_
                    img_caption.insert(0, span)

                    if not description:
                        warn = lxml.html.Element('span')
                        warn.attrib['class'] = 'warning-no-description'
                        warn.text = u'image has no description'
                        img_caption.append(warn)

                    # add title
                    span = lxml.html.Element('span')
                    title = unicode(img_obj.Title(), 'utf-8')
                    class_ = description and 'image-caption-title image-caption-with-title' or \
                                             'image-caption-title image-caption-without-title'
                    if title:
                        span.text = title
                    span.attrib['class'] = class_
                    img_caption.insert(0, span)

                    if not title:
                        warn = lxml.html.Element('span')
                        warn.attrib['class'] = 'warning-no-title'
                        warn.text = u'image has no title'
                        img_caption.append(warn)

                    # add title and description to container
                    if img_caption_position == 'top':
                        div.insert(0, img_caption)
                    else:
                        div.append(img_caption)

                div.tail = img.tail
                img.getparent().replace(img, div)

    fp_ini.close()

@registerTransformation
def cleanupHtml(root):
    """ Perform some basic HTML cleanup """

    forbidden_tags = ['meta']
    for node in root.xpath('//*'):

        # remove style attributes
        try:
            del node.attrib['style']
        except KeyError:
            pass

        # remove forbidden tags
        if node.tag in forbidden_tags:
            node.getparent().remove(node)

        # remove links using href with empty contents
        if node.tag == 'a':
            if node.get('href') and not node.text_content().strip():
                node.getparent().remove(node)

@registerTransformation
def footnotesForHtml(root):
    """" Convert <em>[[text:footnote-text]]</em for consolidated HTML
         representation.
    """

    for node in CSSSelector('span.footnoteText')(root):
        footnote_text = node.text_content()
        if footnote_text:
            node.attrib['title'] = footnote_text
            node.text = u'Remark'

@registerTransformation
def rescaleImagesToOriginalScale(root):
    """ makeImagesLocal() exports all images in their original size
        and adjust the URL according to that. For HTML we need to 
        restore the original scale which is stored by makeImagesLocal()
        on the 'originalscale' attribute on each <img> tag.
    """

    for img in root.xpath('//img'):
        scale = img.get('originalscale')
        if scale:
            img.attrib['src'] = img.attrib['src'] + '/image_%s' % scale

@registerTransformation
def addAnchorsToHeadings(root):
    """ obsolete """

@registerTransformation
def removeTableOfContents(root):
    """ Remove some of the listings not needed for HTML view """

    for toc in CSSSelector('div#table-of-contents')(root):
        toc.getparent().remove(toc)

@registerTransformation
def addTableOfContents(root):
    """ Add a table of contents to the #toc node """

    toc = list()

    # first find all related entries (.bookmark-title class)
    for count, e in enumerate(root.xpath(xpath_query(ALL_HEADINGS))):
        level = int(e.tag[-1]) - 1 # in Plone everything starts with H2
        text = e.text_content()
        id = 'toc-%d' % count
        new_anchor = lxml.html.Element('a')
        new_anchor.attrib['name'] = id
        e.insert(0, new_anchor)
        toc.append(dict(text=text,
                        level=level,
                        id=id))

    div_toc = lxml.html.Element('div')
    div_toc.attrib['id'] = 'toc'
    div_ul = lxml.html.Element('ul')
    div_toc.append(div_ul)

    for d in toc:
        li = lxml.html.Element('li')
        li.attrib['class'] = 'toc-%s' % d['level']
        a = lxml.html.Element('a')
        a.attrib['href'] = '#' + d['id']
        a.attrib['class'] = 'toc-%s' % d['level']
        span = lxml.html.Element('span')
        span.text = d['text']
        a.insert(0, span)
        li.append(a)
        div_ul.append(li)

    # check for an existing TOC (div#toc) 
    nodes = CSSSelector('div#toc')(root)
    if nodes:
        # replace it with the generated TOC
        toc = nodes[0]
        toc.getparent().replace(toc, div_toc)
    else:
        # append generated TOC to body tag
        body = root.xpath('//body')[0]
        body.insert(0, div_toc)

@registerTransformation
def addTableList(root):
    """ Add a table list based on the <caption> tags """

    tables = list()
    
    for count, caption in enumerate(root.xpath('//caption')):
        text = caption.text_content()
        id = 'table-%d' % count
        new_anchor = lxml.html.Element('a')
        new_anchor.attrib['name'] = id
        caption.insert(0, new_anchor)
        tables.append(dict(text=text,
                           count=count,
                           id=id))

    if tables:            
        div_tables = lxml.html.Element('div')
        div_tables.attrib['id'] = 'table-list'
        div_ul = lxml.html.Element('ul')
        div_tables.append(div_ul)

        for d in tables:
            li = lxml.html.Element('li')
            li.attrib['class'] = 'table-list-entry' 
            a = lxml.html.Element('a')
            a.attrib['href'] = '#' + d['id']
            a.attrib['class'] = 'table-list-entry' 
            span = lxml.html.Element('span')
            span.text = d['text']
            a.insert(0, span)
            li.append(a)
            div_ul.append(li)

        # check for an existing div#table-list) 
        nodes = CSSSelector('div#table-list')(root)
        if nodes:
            # replace it
            nodes[0].replace(nodes[0], div_tables)
        else:
            body = root.xpath('//body')[0]
            body.append(div_tables)

@registerTransformation
def addImageList(root):
    """ Add an image list based on the <caption> tags """

    images = list()
    
    count = 0
    for caption in root.xpath('//span'):
        # <span> with image captions may contain several css classes. Unfortunately
        # BeautifulSoup is unable to find elements by-CSS-class if the related element
        # contains more than one CSS class
        if not 'image-caption-with-description' in caption.get('class', ''):
            continue
        text = caption.text_content()
        id = 'image-%d' % count
        new_anchor = lxml.html.Element('a')
        new_anchor.attrib['name'] = id
        caption.insert(0, new_anchor)
        images.append(dict(text=text,
                           id=id))
        count += 1

    div_images = lxml.html.Element('div')
    div_images.attrib['id'] = 'images-list'
    div_ul = lxml.html.Element('ul')
    div_images.append(div_ul)

    if images:
        for d in images:
            li = lxml.html.Element('li')
            li.attrib['class'] = 'image-list-entry' 
            a = lxml.html.Element('a')
            a.attrib['href'] = '#' + d['id']
            a.attrib['class'] = 'image-list-entry' 
            span = lxml.html.Element('span')
            span.text = d['text']
            a.insert(0, span)
            li.append(a)
            div_ul.append(li)

        # check for an existing div#image-list) 
        nodes = CSSSelector('div#image-list')(root)
        if nodes:
            # replace it
            nodes[0].replace(nodes[0], div_images)
        else:
            # add to end of document
            body = root.xpath('//body')[0] 
            body.append(div_images)

@registerTransformation
def leaveLinksToPrinceXML(root):
    """ Replace all special CSS classes for A nodes in order to leave
        the rendering of links to PrinceXML.
    """

    for link in root.xpath('//a'):
        href = link.get('href')
        if href:
            class_ = link.get('class', '')
            link.attrib['class'] = class_ + ' no-decoration'

@registerTransformation
def removeLinks(root):
    """ replace all links with a <span> tag and the anchor text """

    for link in root.xpath('//a'):
        tag = lxml.html.Element('span')
        tag.text = link.text_content()
        link.getparent().replace(link, tag)

@registerTransformation
def convertFootnotes(root):

    # Special format for footnotes:
    # <span class="footnoteText">some footnote text</span>

    for node in CSSSelector('span.footnoteText')(root):
        footnote_text = node.text_content()
        if footnote_text:
            node.attrib['class'] = 'generated-footnote'

    # generate footnotes from <a href>...</a> fields
    for a in root.xpath('//a'):
        href = a.get('href', '')
        if not href or not url_match.match(href) or 'editlink' in a.get('class', ''):
            continue

        text = a.text_content().strip()
        if text:
            # don't convert URL links with an URL as pcdata into a footnote
            if url_match.match(text):
                continue
            new_a = lxml.html.Element('a')
            new_a.text = cgi.escape(href)
            new_a.attrib['href'] = href

            span = lxml.html.Element('span')
            span.attrib['class'] = 'generated-footnote'
            span.append(new_a)

            span2 = lxml.html.Element('span')
            span2.attrib['class'] = 'generated-footnote-text'
            span2.text = text
            span2.append(span)

            a.getparent().replace(a, span2)

@registerTransformation
def removeInternalLinks(root):

    for a in root.xpath('//a'):
        href = a.get('href')
        if nodeProcessed(a) or not href:
            continue
        # internal links _don't_ start with http:// etc. so we perform a
        # negative check
        if not url_match.match(href): #
            span = lxml.html.Element('span')
            span.text = a.text_content()
            a.getparent().replace(a, span)

@registerTransformation
def removeListings(root): 
    """ Remove some of the listings not needed for HTML view """
    
    # Toc first
    for toc in CSSSelector('div#table-of-contents')(root):
        toc.getparent().remove(toc)

    # remove all image containers
    for container in CSSSelector('div.image-container')(root):
        img = container.xpath('//img')[0]
        container.getparent().replace(container, img)

@registerTransformation
def removeProcessedFlags(root):
    """ This method is called while generating PDF
        from the (splitted) HTML (HTML+PDF view).
        Remove the 'processed="1" attribute.
    """ 

    for node in root.xpath('//*[@processed]'):
        del node.attrib['processed']

@registerTransformation
def replaceUnresolvedLinks(root):
    """ This transformation replaces all a.external-link
        nodes with a proper footnote.
        Used for PDF generation only (html_mode = 'split')
    """

    for link in CSSSelector('a.external-link')(root):
        href = link.attrib['href']

        span1 = lxml.html.Element('span')
        span1.attrib['class'] = 'generated-footnote-text'
        span1.text = link.text_content()

        span2 = lxml.html.Element('span')
        span2.attrib['class'] = 'generated-footnote'
        span2.text = href
        span1.append(1, span2)
        link.getparent().replace(link, span1)


@registerTransformation
def removeCrapFromHeadings(root):
    """ Ensure that HX tags containing only text """

    for node in root.xpath(xpath_query(ALL_HEADINGS)):
        text = node.text_content()
        if text:
            node.clear()
            node.text = text
        else:
            node.getparent().remove(node)


@registerTransformation
def fixHierarchies(root):
    """ Iterate of all boundary documents. For documents
        with level > 0 we need to shift to hierarchies down.
    """

    for doc in root.xpath('//div'):
        if not 'document-boundary' in doc.get('class', ''):
            continue
        level = int(doc.get('level', '0'))
        if level > 0:
            for heading in doc.xpath(xpath_query(ALL_HEADINGS)):
                heading_level = int(heading.tag[-1])
                heading.tag = 'h%d' % (heading_level + level)

@registerTransformation
def convertWordFootnotes(root):
    """ Convert footnotes from Word conversion to PrinceXML format """

    # iterate over all <a href="ftn.."> elements
    # <p class="P2"><span class="footnodeNumber"><a class=
    # "Footnote_20_Symbol" id="ftn2" href="#body_ftn2" name=
    # "ftn2">2</a></span> Fussnotentext 2</p>

    for anchor in root.xpath('//a'):
        anchor_id = anchor.get('id')
        if not anchor_id or not anchor_id.startswith('ftn'):
            continue

        # get hold of the outer <p> tag
        p_tag =  anchor.getparent().getparent()
        assert p_tag.tag.lower() == 'p'

        # 'text' is now "2 Fussnotentext"
        text = p_tag.text_content()
        # get rid of the leading footnote number
        text = leading_numbers.sub(u'', text).strip()

        # now find referencing footnote
        # <div class="Standard">
        #   Noch eine Fussnote <span class="Footnote_20_anchor" title=
        #   "Footnote: Fussnotentext 2"><a href="#ftn2" id="body_ftn2"
        #   name="body_ftn2">2</a></span>
        # </div>
        result = root.xpath("//a[@href='#%s']" % anchor_id)
        if not result:
            continue

        footnote_anchor = result[0]

        span = lxml.html.Element('span')
        span.attrib['class'] = 'footnoteText'
        span.text = text
        span.append(span)

        footnote_anchor.getparent().replace(footnote_anchor, span)
        p_tag.getparent().remove(p_tag)

@registerTransformation
def fixAmpersand(root):
    """ Convert solitary '&' to '&amp;' """

    for node in root.xpath('//*'):
        if not '&' in (node.text or ''):
            continue
        text = node.text
        text = text.replace('&amp;', '&')
        node.text = text
        

@registerTransformation
def convertWordFootnotes2(root):
    """ Convert footnotes from Word conversion to PrinceXML format """

    # iterate over all 
    # <div id="sdfootnote1">
    # <p class="c2"><a name="_GoBack"></a> <a class="sdfootnotesym" name="sdfootnote1sym" href="#sdfootnote1anc" id="sdfootnote1sym">1</a>
    # Das ist der Fussnotentext</p>
    # <p class="sdfootnote-western"><br></p>
    # </div>
    # elements

    selector = CSSSelector('a.sdfootnotesym')
    for anchor in selector(root):
        anchor_id = anchor.get('id') or anchor.get('name')

        # get hold of the outer tag
        parent=  anchor.getparent()

        # 'text' is now "2 Fussnotentext"
        text = parent.text_content()
        text = leading_numbers.sub(u'', text).strip()

        # now find referencing footnote
        # <p class="western c1">Beispiel Text (dies ist eine Fussnote
        # <a class="sdfootnoteanc" name="sdfootnote1anc" href="#sdfootnote1sym" id="sdfootnote1anc"><sup>1</sup></a> )</p>

        result = root.xpath("//a[@href='#%s']" % anchor_id)
        if not result:
            continue

        # and replace it with a span.footnoteText
        footnote_anchor = result[0]
        span = lxml.html.Element('span')
        span.attrib['class'] = 'footnoteText'
        span.text = text
        footnote_anchor.getparent().replace(footnote_anchor, span)

        # remove footnote (the outer div, see above)
        div_parent = parent.getparent()
        div_parent.getparent().remove(div_parent)

@registerTransformation
def adjustHeadingsFromAggregatedHTML(root):
    """ For an aggregated HTML documented from a nested folder
        structure we need to adjust the HX headings of the contained
        AuthoringContentPage documents. The 'level' attribute of the
        related document nodes is taken as an offset for recalculating
        the headings.
    """

    # search all documents first
    selector = CSSSelector('div.portal-type-authoringcontentpage')
    for node in selector(root):    
        # get their level
        level = int(node.get('level'))

        # create a sorted list of used headings
        heading_levels_used = list()
        for heading in node.xpath(xpath_query(ALL_HEADINGS)):
            heading_level = int(heading.tag[1:])
            if not heading_level in heading_levels_used:
                heading_levels_used.append(heading_level)
        heading_levels_used.sort()

        # now add an offset to the heading level
        for heading in node.xpath(xpath_query(ALL_HEADINGS)):
            heading_level = int(heading.tag[1:])
            new_level = level + heading_levels_used.index(heading_level) 
            heading.tag = 'h%d' % new_level

@registerTransformation
def removeEmptyNodesFromWord(root):
    """ Remove empty paragraphs from imported Word markup """
    for node in root.xpath('//p'):
        # don't touch nodes containing images
        if node.xpath('.//img'):
            continue
        
        text = lxml.html.tostring(node, encoding=unicode, method='text').strip()
        if not text:
            node.getparent().remove(node)

    # also remove the FOOTER culprit
    selector = CSSSelector('div[type="FOOTER"]')
    for node in selector(root):
        node.getparent().remove(node)


@registerTransformation
def mergeSingleSpanIntoParagraph(root):
    """ Merge solitaire <span> element inside a paragraph 
        into the paragraph content.
    """

    for node in root.xpath('//p'):
        spans = node.xpath('.//span')
        if len(spans) == 1:
            if not spans[0].getchildren():
                text = spans[0].text
                spans[0].getparent().remove(spans[0])
                node.text = text

@registerTransformation
def convertWordEndnotes(root):
    """ Convert Word endnotes into a simple list """

    endnotes = list()
    for node in root.xpath('//div'):
        node_id = node.get('id', '')
        if not node_id.startswith('sdendnote'):
            continue
        endnote_txt = node.xpath('.//p')[0].text_content()
        endnote_num = node.xpath('.//a')[0].text_content()
        endnotes.append(dict(text=endnote_txt, number=endnote_num, id=node_id))
        node.getparent().remove(node)

    if endnotes:
        ul = lxml.html.Element('ul')
        ul.attrib['class'] = 'endnotes'
        for endnote in endnotes:
            li = lxml.html.Element('li')
            li.attrib['class'] = 'endnote'

            span = lxml.html.Element('span')
            span.attrib['class'] = 'endnote-number'
            span.attrib['style'] = 'display: none'
            span.text = endnote['number']
            li.append(span)

            span = lxml.html.Element('span')
            span.attrib['class'] = 'endnote-text'
            span.attrib['id'] = endnote['id'] + 'sym'
            span.text = endnote['text']
            li.append(span)

            ul.append(li)
        root.xpath('//body')[0].append(ul)

    # Rename all 'name' attributes from the anchors to endnotes since TinyMCE
    # considers this as an anchor and not as a link to an anchor and therefore
    # TinyMCE will remove the inner text
    selector = CSSSelector('a.sdendnoteanc')
    for anchor in selector(root):
        try:
            del anchor.attrib['name']
        except KeyError:
            pass


@registerTransformation
def addIndexList(root):
    """ Add an index listing for all terms inside <span class="index-term"> """

    indexes = dict()
    for num, node in enumerate(CSSSelector('span.index-term')(root)):
        term = node.text_content().strip()
        term_id = 'index-term-%d' % num
        node.attrib['id'] = term_id
        if not term in indexes:
            indexes[term] = list()
        indexes[term].append(term_id)

    if not indexes:
        return

    div_indexes = lxml.html.Element('div')
    div_indexes.attrib['id'] = 'indexes-list'
    div_ul = lxml.html.Element('ul')
    div_indexes.append(div_ul)

    index_terms = sorted(indexes.keys())
    for index_term in index_terms:
        term_ids = indexes[index_term]

        li = lxml.html.Element('li')
        li.attrib['class'] = 'index-term-entry' 

        span = lxml.html.Element('span')
        span.attrib['class'] = 'index-term-entry' 
        span.text = index_term
        li.append(span)

        num_term_ids = len(term_ids)
        for i, term_id in enumerate(term_ids):
            a = lxml.html.Element('a')
            a.attrib['href'] = '#' + term_id
            a.attrib['class'] = 'index-term-entry' 
            a.text = (i+1 < num_term_ids) and ', ' or ''
            li.append(a)

        div_ul.append(li)

    # check for an existing div#indexes-list) 
    nodes = CSSSelector('div#indexes-list')(root)
    if nodes:
        # replace it
        nodes[0].replace(nodes[0], div_indexes)
    else:
        # add to end of document
        body = root.xpath('//body')[0] 
        body.append(div_indexes)
