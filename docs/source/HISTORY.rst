Changelog
=========

2.1.19 (2012-02-20)
-------------------
- unicode fix in HTML splitter code

2.1.18 (2012-02-10)
-------------------
- folder aggregator now support (experimental) document filter
  based on UIDs (filter_uid parameter)
- makeImageLocal() transformation removed parts of the document
  while replacing the old image with an image container
- added experimental addIndexList transformation

2.1.17 (2011-12-28)
-------------------
- checking html input in transformation machinery for empty strings

2.1.16 (2011-12-21)
-------------------
- better footnote handling

2.1.15 (2011-12-20)
-------------------
- convertWordEndnotes() transformation added

2.1.14 (2011-12-19)
-------------------
- fixed image width 100% for images inside an image-container
  (PrinceXML 8 compatibility)

2.1.13 (2011-12-18)
-------------------
- some fixes discovered using PyFlakes

2.1.12 (2011-12-12)
-------------------
- added some transformations for better
  Word import

2.1.11 (2011-11-23)
-------------------
- update trove classifiers

2.1.10 (2011-11-17)
-------------------
- improved aggregator for nested content folders
- support for content hierarchies up to level 8
- support for new environment variable SMARTPRINTNG_ZIP_OUTPUT

2.1.9 (2011-11-11)
------------------
- fixed bug in makeImagesLocal() transformation
  where the document root has not been used properly
  for finding images by traversal 

2.1.8 (2011-11-11)
------------------
- support for new ``SMARTPRINTNG_LOCAL_CONVERSION`` environment
  variable

2.1.7 (2011-11-08)
------------------
- removed some baggage in order to make distro smaller

2.1.6 (2011-11-07)
------------------
- minor fixes in handling of generated files for download 

2.1.5 (2011-11-07)
------------------
- first public (open-source) release

2.1.4 (2011-10-25)
------------------
- fixed unicode/utf-8 issue in makeImagesLocal transformation

2.1.3 (2011-10-14)
------------------
- added fixAmpersand transformation

2.1.2 (2011-10-10)
------------------
- transformations for dealing with converted footnotes from Word

2.1.1 (2011-10-08)
------------------
- compatibility with Dexterity

2.1.0 (2011-09-22)
------------------
- final 2.1.0 release

2.0.9 (2011-09-20)
------------------
- fixed bug in xpath_query() (using relative query)

2.0.8 (2011-09-11)
------------------
- more cleanup

2.0.7 (2011-09-10)
------------------
- some ZCML fixes in order to avoid Plone 4.x startup failures under
  some conditions
- restored compatibility with Plone 3.3.X

2.0.6 (2011-09-08)
------------------
- image exporter did not deal proper with duplicate image ids
- minor fixes

2.0.5 (2011-09-02)
------------------
- new lxml backed transformation pipeline 
- more tests

2.0.4 (2011-08-26)
------------------
- logging resource registration using INFO severity
- new lxml dependency

2.0.3 (2011/08/15)
------------------
- catching HTTPError in image resolver
- fixed another BeautifulSoup misbehaviour in fixHeadingAfterOfficeImport()

2.0.2 (2011-08-02)
------------------
- minor fix

2.0.1 (2011-08-02)
------------------
- integration with new zip client version (Proxy2 implementation)

2.0.0 (2011-07-25)
---------------------
* final release

2.0.0rc2 (2011-07-04)
---------------------
* fix in logger call in folder.py

2.0.0rc1 (2011-07-01)
---------------------
* don't extend images an authoring project
* remove class attributes from headings after office import
* added ignoreHeadingsForStructure transformation

2.0.0b2 (2011-06-16)
--------------------
* minor fixes related to office data import

2.0.0b1 (2011-05-24)
--------------------
* fixes related to office format input

2.0.0a3 (2011-05-17)
--------------------
* added some workaround for image resolver in order to deal with images
  referenced through a fully specified URL with a redirection included
  (TQM issue)

2.0.0a2 (2011-05-14)
--------------------
* minor fix in safe_get()

2.0.0a1 (2011-05-10)
--------------------
* simplification and refacoring

0.7.0 (2011-02-11)
-------------------
* updated for use with zopyx.authoring 1.5.X
* added GenericDownloadView aka '@@ppConvert'
* exported images now contain a proper extension (fixes issues
  with the XFC converter depending on extension for determining
  the image format)

0.6.24 (2010-12-09)
-------------------
* added addDocumentLinks() transformation
* including content ids of aggregated content

0.6.23 (2010-09-10)
-------------------
* addImageCaptionsInHTML(): honour excludeFromImageEnumeration

0.6.22 (2010-09-09)
-------------------
* fixed improper stripping of image names using an image scale
  (causing issues in the consolidated HTML view of the authoring
  environment)

0.6.21 (2010-08-09)
-------------------
* added support '++resource++' image references (Patrick Gerken)
* added support for FSImage (Patrick Gerken)

0.6.20 (2010-08-05)
-------------------
* added 'removeComments' transformation
* added 'makeImageSrcLocal' transformation

0.6.19 (2010-07-13)
-------------------
* fixed race condition in makeImagesLocal()

0.6.18 (2010-06-14)
-------------------
* images got a new PDF conversion option "Exclude from image enumeration"

0.6.17 (2010-06-12)
-------------------
* inserting H1 title for consolidated HTML
* added extra class to folder title for consolidated HTML 

0.6.16 (2010-05-29)
-------------------
* inserting space for found anchors

0.6.15 (2010-04-15)
-------------------
* minor fix in image handling

0.6.14 (2010-04-14)
-------------------
* minor tweaks for image caption markup

0.6.13 (2010-03-26)
-------------------
* support for span.footnoteText

0.6.12 (2010-03-21)
-------------------
* support for image urls 'resolveuid/<uid>'
* minor fixes and tweaking in image handling (caption generation)

0.6.11 (2010-03-10)
-------------------
* added document extender
* document option for suppressing the title in PDF
* image caption support
* changed default transformations (to makeImagesLocal only)
* removed TOC from default PDF template

0.6.10 (2010-03-03)
-------------------
* support for request/transformations parameter
* various fixes

0.6.9 (2010-02-22)
------------------
* added <em>[[text:footnote-text]]</em> support for generating footnotes
* various changes related to zopyx.authoring integration

0.6.8 (2010-02-03)
------------------

* Folder aggregation now works with all folderish objects providing IATFolder


0.6.7 (2009-11-30)
------------------

* makeImagesLocal: better dealing with virtual hosting

0.6.6 (2009-11-15)
------------------

* fixed CSS issue with TOC markup

0.6.5 (2009-11-12)
------------------

* always use images in their original resolution 
* optional content information with link to the edit mode
  of the aggregated document (you must change the visibility
  of the .content-info class through CSS)
* a request parameter 'show-debug-info' will enable the
  additional content-info view
* better error handling
* better logging
* tweaked markup of generated TOC


0.6.3 (2009-10-27)
------------------

* refactored language handling
* refactored PDF view in order to provide a low-level view 
  returning a reference to the generated PDF file instead
  providing it for HTTP download


0.6.2 (2009-10-24)
------------------

* setting anti-cache headers
* locale-aware sorting in PloneGlossary code

0.6.1 (2009-10-23)
------------------

* PloneGlossary integration: compare title case-insensitive
  (IDG project)

0.6.0 (2009-10-21)
------------------

* refactored and simplified transformation machinery

0.5.0 (2009-10-09)
------------------

* major rewrite

0.3.0 (2009-09-24)
------------------

* refactored views

0.2.0 (2009-09-23)
------------------

* more hyphenation dicts
* restructured resources directory

0.1 (xxxx-xx-xx)
----------------

* Initial release
