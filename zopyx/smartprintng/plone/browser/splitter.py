################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################

import os
import codecs
from cStringIO import StringIO
from BeautifulSoup import BeautifulSoup, Tag, NavigableString

from util import _findTextInNode

def split_html(html_filename, split_at_level=0):
    """ Split aggregated and rendered HTML document at
        some <hX> tag(s). split_at_level=0 -> split at
        H1 tags, split_at_level=1 -> split at H1 and H2
        tags.
        Returns a list of dicts with keys 'html' referring
        to the subdocument and 'level' indicating the split
        point.
    """

    destdir = os.path.dirname(html_filename)
    soup = BeautifulSoup(file(html_filename).read())

    fp = StringIO(soup.__str__(prettyPrint=True))
    docs = list()
    current_doc = list()
    for line in fp:
        line = line.rstrip()
        for level in range(split_at_level+1):
            if '<h%d' % (level+1) in line.lower():
                html = '\n'.join(current_doc)
                soup = BeautifulSoup(html)
                try:
                    title = _findTextInNode(soup.find('h1'))
                except AttributeError:
                    title = u''

                # count tables and images
                number_tables = len(soup.findAll('table'))
                number_images = len(soup.findAll('div', {'class' : 'image-caption'}))

                # find all linkable nodes with an ID attribute
                node_ids = list()
                for node in soup.recursiveChildGenerator():
                    if not isinstance(node, Tag):
                        continue
                    node_id = node.get('id')
                    if node_id:
                        node_ids.append(node_id)

                html = soup.prettify()
                docs.append(dict(html=html, 
                                 level=level, 
                                 title=title, 
                                 node_ids=node_ids,
                                 number_images=number_images,
                                 number_tables=number_tables))
                current_doc = []
                break
                
        current_doc.append(line)

    # now deal with the remaining part of the document
    html = '\n'.join(current_doc)
    soup = BeautifulSoup(html)
    try:
        title = _findTextInNode(soup.find('h1'))
    except AttributeError:
        title = u''

    # count tables and images
    number_tables = len(soup.findAll('table'))
    number_images = len(soup.findAll('div', {'class' : 'image-caption'}))

    # find all linkable nodes with an ID attribute
    node_ids = list()
    for node in soup.recursiveChildGenerator():
        if not isinstance(node, Tag):
            continue
        node_id = node.get('id')
        if node_id:
            node_ids.append(node_id)

    html = soup.prettify()
    docs.append(dict(html=html, 
                     level=0, 
                     title=title, 
                     node_ids=node_ids,
                     number_images=number_images,
                     number_tables=number_tables))

    # now store files on the filesystem
    ini_filename = os.path.join(destdir, 'documents.ini')
    fp_ini = codecs.open(ini_filename, 'w', 'utf-8')

    for count, d in enumerate(docs[1:]):
        filename = os.path.join(destdir, 'split-0/%d-level-%d.html' % (count, d['level']))
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))                
        file(filename, 'w').write(d['html'])

        print >>fp_ini, '[%d]' % count
        print >>fp_ini, 'filename = %s' % filename
        print >>fp_ini, 'title = %s' % d['title']
        print >>fp_ini, 'number_tables= %d' % d['number_tables']
        print >>fp_ini, 'number_images = %d' % d['number_images']
        print >>fp_ini, 'node_ids = '
        for node_id in d['node_ids']:
            print >>fp_ini, '    ' + node_id
        print >>fp_ini 

    fp_ini.close()
    return docs[1:]
