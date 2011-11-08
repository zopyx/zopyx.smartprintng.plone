# -*- coding: iso-8859-15 -*-

#####################################################################
# zopyx.authoring
# (C) 2011, ZOPYX Limited, D-72070 Tuebingen. All rights reserved
#####################################################################

import os
import re
import unittest2
from zopyx.smartprintng.plone.transforms import transformation

dirpath = os.path.dirname(__file__)
UMLAUT = unicode(chr(0xe4), 'iso-8859-15')

HTML4CLEANUP = u"""
<body>
<div></div>
<p>hello world</p>
<div>   </div>
<div><p></p></div>
</body>
"""

DIRTY_TABLE = u"""
<wrapper><table width="200px" class="crap">
<colgroup>
<col>a</col>
</colgroup>
<tr>
<td>blather</td>
</tr>
</table>
</wrapper>
"""

class TestTransformations(unittest2.TestCase):

    def _makeOne(self, *transformation_names):
        return transformation.Transformer(transformation_names)

    def testUnicodeInputCheck(self):
        T = self._makeOne()
        self.assertRaises(TypeError, T, '')
        self.assertRaises(TypeError, T, None)
        T(unicode('foo')) # should not raise TypeError

    def testEmptyTransformations(self):
        T = self._makeOne()
        html = u'<h1>hello world</h1>'
        self.assertEqual(html, T(html))

    def testEmptyTransformationsWithAccentedChars(self):
        T = self._makeOne()
        html = u'<h1>xx-%s-xx</h1>' % UMLAUT
        self.assertEqual(html, T(html))

    def testXpath_query(self):
        self.assertEqual(transformation.xpath_query(['div']), './/*[name()="div"]')
        self.assertEqual(transformation.xpath_query(['h1', 'h2']), './/*[name()="h1" or name()="h2"]')

    def testXpath_queryWithImproperParameterType(self):
        self.assertRaises(TypeError, transformation.xpath_query, 'h1')

    def testCleanupEmptyDivs(self):
        T = self._makeOne('cleanupEmptyElements')
        html = T(HTML4CLEANUP)
        self.assertTrue('<div>' not in html)
        self.assertEqual(html, '<p>hello world</p>')

    def testAddUUIDs(self):
        T = self._makeOne('addUUIDs')
        html = T(u'<wrapper><h1>hello world</h1></wrapper>')
        regex = re.compile('<h1 id="(.*)">')
        mo = regex.search(html)
        self.assertNotEqual(mo, None)
        self.assertEqual(len(mo.group(1)), 36)

    def testAddUUIDsForDiv(self):
        T = self._makeOne('addUUIDs')
        html = T(u'<div>hello world</div>')
        regex = re.compile('<div id="(.*)">')
        mo = regex.match(html)
        self.assertEqual(mo, None)

    def testAddUUIDsWithUmlauts(self):
        T = self._makeOne('addUUIDs')
        html = T(u'<div>%s</div>' % UMLAUT)
        regex = re.compile('<div id="(.*)">')
        mo = regex.match(html)
        self.assertEqual(mo, None)
        self.assertTrue(UMLAUT in html)

    def testShiftHeadings(self):
        T = self._makeOne('shiftHeadings')
        html = u'<h1>foo</h1><h2>bar</h2>'
        html2 = T(html)
        html_expected = html.replace('h2', 'h3').replace('h1', 'h2')
        self.assertEqual(html2, html_expected)

    def testCleanupTable(self):
        T = self._makeOne('cleanupTables')
        html2 = T(DIRTY_TABLE)
        self.assertTrue('class="plain grid"' in html2)
        self.assertFalse('<col>' in html2)
        self.assertFalse('<colgroup>' in html2)
        self.assertFalse('border' in html2)
        self.assertFalse('width' in html2)
        self.assertFalse('cellspacing' in html2)

    def testFixHeadingsAfterOfficeImport(self):
        T = self._makeOne('fixHeadingsAfterOfficeImport')
        self.assertEqual(T(u'<wrapper><h1>1. foo</h1></wrapper>'), '<wrapper><h1>foo</h1></wrapper>')
#        self.assertEqual(T(u'hello world'), '<p>hello world</p>')
        self.assertEqual(T(u'<wrapper><h1></h1></wrapper>'), '<wrapper><h1></h1></wrapper>')
        self.assertEqual(T(u'<wrapper><h1>foo</h1></wrapper>'), '<wrapper><h1>foo</h1></wrapper>')
        self.assertEqual(T(u'<wrapper><h1>1.2 foo</h1></wrapper>'), '<wrapper><h1>foo</h1></wrapper>')

    def testAdjustImagesAfterOfficeImport(self):
        T = self._makeOne('adjustImagesAfterOfficeImport')
        self.assertTrue('src="bla.png/image_medium"' in T(u'<wrapper><img src="bla.png" ></wrapper>'))
        self.assertFalse('height=' in T(u'<wrapper><img src="bla.png" height="200" width="400"></wrapper>'))
        self.assertFalse('width=' in T(u'<wrapper><img src="bla.png" height="200" width="400"></wrapper>'))

    def testIgnoreHeadingsForStructure(self):
        T = self._makeOne('ignoreHeadingsForStructure')
        html = u'<body><div><h1>hello</h1><h2>world</h2></div></body>'
        html2 = T(html)
        self.assertTrue('<h1>' in html2)
        self.assertTrue('<h2>' in html2)

    def testIgnoreHeadingsForStructure2(self):
        T = self._makeOne('ignoreHeadingsForStructure')
        html = u'<body><div class="ignore-headings-for-structure"><h1>hello</h1><h2>world</h2></div></body>'
        html2 = T(html)
        self.assertFalse('<h1>' in html2)
        self.assertFalse('<h2>' in html2)
        self.assertTrue('<div class="heading-level-1">' in html2)
        self.assertTrue('<div class="heading-level-2">' in html2)

    def testAdjustAnchorsToLinkables(self):
        T = self._makeOne('adjustAnchorsToLinkables')
        html = u'<h1 id="12345"/><a href="resolveuid/someuid#12345">link text</a>'
        html2 = T(html)
        self.assertTrue('href="#12345" in html')
        
    def testAdjustAnchorsToLinkablesNonExistingID(self):
        T = self._makeOne('adjustAnchorsToLinkables')
        html = u'<h1 id="does not exist"/><a href="resolveuid/someuid#12345">link text</a>'
        html2 = T(html)
        self.assertFalse('<a' in html2)
        self.assertTrue('<span>link text</span>' in html2)

    def testCleanupForEPUB(self):
        T = self._makeOne('cleanupForEPUB')
        html = u'<div id="table-list" /><div id="table-of-contents"/></div id="images-list"/>'
        html2 = T(html)
        self.assertTrue(len(html2)==0)

    def testCleanupForEPUB2(self):
        T = self._makeOne('cleanupForEPUB')
        html = u'<wrapper><span class="image-caption-with-title">caption</span></wrapper>'
        html2 = T(html)
        self.assertTrue(html2 == '<wrapper></wrapper>')

    def testCleanupForEPUB3(self):
        T = self._makeOne('cleanupForEPUB')
        html = u'<wrapper><div class="content">my info</div></wrapper>'
        html2 = T(html)
        self.assertTrue(html == html2)

        html = u'<wrapper><div class="contentinfo">my info</div></wrapper>'
        html2 = T(html)
        self.assertTrue(html2 == '<wrapper></wrapper>')

    def testCleanupHtml(self):
        T = self._makeOne('cleanupHtml')
        html = u'<html><head><meta http-equiv="content-type" content="text/html"/></head><body><a href="foo"></a><span style="font-size: 20px">bar</span></body></html>'
        html2 = T(html)
        self.assertTrue('<span>bar</span>' in html2)
        self.assertFalse('<meta' in html2)
        self.assertFalse('<a' in html2)

    def testFootnotesForHtml(self):
        T = self._makeOne('footnotesForHtml')
        html = u'<span class="footnoteText">hello world</span>'
        html2 = T(html)
        self.assertEqual('<span class="footnoteText" title="hello world">Remark</span>', html2)

    def testRescaleImagesToOriginalScale(self):
        T = self._makeOne('rescaleImagesToOriginalScale')
        html = u'<img originalscale="small" src="foo.img" />'
        html2  = T(html)
        self.assertTrue('src="foo.img/image_small"' in html2)

    def testRemoveTableOfContents(self):
        T = self._makeOne('removeTableOfContents')
        html = u'<div>foo</div><div id="table-of-contents">toc</div>'
        html2 = T(html)
        self.assertEqual(html2, '<div>foo</div>')

    def testLeaveLinksToPrinceXML(self):
        T = self._makeOne('leaveLinksToPrinceXML')
        html = u'<a class="foo" href="http://www.heise.de">heise online</a>'
        html2 = T(html)
        self.assertTrue('class="foo no-decoration"' in html2)

    def testRemoveLinks(self):
        T = self._makeOne('removeLinks')
        html = u'<a href="http://www.heise.de">heise online</a>'
        html2 = T(html)
        self.assertTrue('<span>heise online</span>')

    def testConvertFootnotes(self):
        T = self._makeOne('convertFootnotes')
        html = u'<wrapper><a href="http://plone.org">plone.org</a></wrapper>'
        html2 = T(html)
        self.assertEqual(html2,
                        '<wrapper><span class="generated-footnote-text">plone.org<span class="generated-footnote"><a href="http://plone.org">http://plone.org</a></span></span></wrapper>')

    def testConvertFootnotes2(self):
        T = self._makeOne('convertFootnotes')
        html = u'<a href="http://plone.org">http://plone.org</a>'
        html2 = T(html)
        self.assertEqual(html, html2),

    def testRemoveInternalLinks(self):
        T = self._makeOne('removeInternalLinks')
        html = u'<wrapper><a href="folder/bla.html">my link</a></wrapper>'
        html2 = T(html)
        self.assertEqual(html2, '<wrapper><span>my link</span></wrapper>')

    def testFixAmpersand(self):
        T = self._makeOne('fixAmpersand')
        html = u'<wrapper><div>Tipps & Tricks</div></wrapper>'
        html2 = T(html)
        self.assertTrue('div>Tipps &amp; Tricks</div>' in html2)

    def testFixAmpersand2(self):
        T = self._makeOne('fixAmpersand')
        html = u'<wrapper><div>Tipps &amp; Tricks</div></wrapper>'
        html2 = T(html)
        self.assertTrue('div>Tipps &amp; Tricks</div>' in html2)

    def testFixAmpersand3(self):
        T = self._makeOne('fixAmpersand')
        html = u'<wrapper><div>a&b&c&d</div></wrapper>'
        html2 = T(html)
        self.assertTrue('div>a&amp;b&amp;c&amp;d</div>' in html2)

    def testRemoveInternalLinks2(self):
        T = self._makeOne('removeInternalLinks')
        html = u'<a href="http://plone.org">http://plone.org</a>'
        html2 = T(html)
        self.assertEqual(html, html2)

    def testRemoveListings(self):
        T = self._makeOne('removeListings')
        html = u'<wrapper><div class="image-container"><img src="foo.gif"></div></wrapper>'
        html2 = T(html)
        self.assertEqual(html2, '<wrapper><img src="foo.gif"></wrapper>')

    def testRemoveCrapFromHeadings(self):
        T = self._makeOne('removeCrapFromHeadings')
        html = u'<wrapper><h1><a href="foo">foo</a>bar</h1></wrapper>'
        html2 = T(html)
        self.assertEqual(html2, '<wrapper><h1>foobar</h1></wrapper>')

    def testRemoveCrapFromHeadings2(self):
        T = self._makeOne('removeCrapFromHeadings')
        html = u'<wrapper><h1>bar</h1></wrapper>'
        html2 = T(html)
        self.assertEqual(html2, '<wrapper><h1>bar</h1></wrapper>')

    def testRemoveCrapFromHeadings3(self):
        T = self._makeOne('removeCrapFromHeadings')
        html = u'<wrapper><h1></h1></wrapper>'
        html2 = T(html)
        self.assertEqual(html2, '<wrapper></wrapper>')


HTML_TEST = u"""
<html>
<body>
<h1>1.1 foo</h1>
<div></div>
<h1>1.2 foo</h1>
</body>
</html>
"""


class TestTransformer(unittest2.TestCase):

    def testPipeline(self):
        T = transformation.Transformer(('cleanupEmptyElements', 'fixHeadingsAfterOfficeImport'))
        result = T(HTML_TEST)
        self.assertFalse('<div>' in result)
        self.assertTrue(result.startswith('<html>'))

    def testPipelineReturnBody(self):
        T = transformation.Transformer(('cleanupEmptyElements', 'fixHeadingsAfterOfficeImport'))
        result = T(HTML_TEST, return_body=True)
        self.assertFalse('<body>' in result)
        self.assertEqual('<h1>foo</h1><h1>foo</h1>', result)

class TestWordTransformations(unittest2.TestCase):

    def testConvertFootnotes(self):
        html = file(os.path.join(dirpath, 'fussnoten-text.html')).read()
        html = unicode(html, 'utf-8')
        T = transformation.Transformer(('convertWordFootnotes',))
        result = T(html)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestWordTransformations))
    suite.addTest(makeSuite(TestTransformations))
    suite.addTest(makeSuite(TestTransformer))
    return suite
