Installation
============

This documentation assumes that your installation of Plone/Zope is based on
zc.buildout.


- edit your *buildout.cfg* -  add *zopyx.smartprintng.plone* to the 
  **eggs** options of your buildout.cfg:

::

    # For Plone 3.x (Client Connector < 2.0)
    find-links = ...
        http://username:password@sdist.zopyx.com

    # For Plone 4.x (Client Connector >2.0)
    find-links = ...
        http://username:password@sdist-pp.zopyx.com
    
    eggs = ...
        zopyx.smartprintng.plone

    # only needed for Plone 3.x    
    zcml = ...
        zopyx.smartprintng.plone


- in addition (and effective 17.08.2011 or later) you need to pin
  the version of the ``BeautifulSoup`` module:

::

    [buildout]
    versions = versions
    ...

    [versions]
    BeautifulSoup = 3.2.0
    ...

-  re-run *bin/buildout*

-  restart Zope/Plone

-  When running the Produce & Publish server on a different server, you must
   adjust the ``SMARTPRINTNG_SERVER`` environment variables within your
   *.bashrc* file (or a similar file) or you put those variables into your
   buildout configuration using the *<environment>* section.  Username and
   password are only needed when you run the Produce & Publish server behind a
   reverse proxy (requiring authentcation).

::

    export SMARTPRINTNG_SERVER=http://user:password@your.server:6543/

or

::

    <environment>
        SMARTPRINTNG_SERVER=http://user:password@your.server:6543/
    </environment>


Supported Plone content-types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


-  Document
-  Folder (nested structure)
-  News item
-  PloneGlossary
-  Collection

Usage
~~~~~

The Plone connector provides a dedicated @@asPlainPDF view that can
be added to the URL of any of the supported content-types of Plone
(Document, Folder, Newsitem, PloneGlossary). So when your document
is for example associated with the URL

::

    http://your.server/plone/my-page

you can generate a PDF by using the URL

::

    http://your.server/plone/my-page/@@asPlainPDF

Parameters
~~~~~~~~~~

The @@asPlainPDF view accepts the following parameters controlling
certain aspects of the PDF conversion:

-  **language** - can be set to 'de', 'en', 'fr' etc. in order to
   control language-specific aspects of the PDF conversion. Most
   important: this parameter controls the hyphenation. The Plone
   connector comes out-of-the-box with hypenation tables for several
   languages.  You can omit this URL parameter if the **Language**
   metadata parameter (of the top-level document) to be converted is
   set within Plone.
-  **converter** - if you are using the Produce & Publish server
   with a converter backend other than PrinceXML you can specify a
   different name (default is *pdf-prince*). See zopyx.convert2
   documentation for details.
- **resource** - can be set in order to specify a registered resource
  directory to be used for  running the conversion. The ```resource``
  parameter must be identical with the ``name`` parameter of
  the related ZCML ``<smartprintng:resourceDirectory>`` directive.

- **template**  - can be used to specify the name of template to be
  used for running the conversion. The ``template`` parameter usually
  refers to a .pt filename inside the ``resource`` directory.  

Miscellaneous
~~~~~~~~~~~~~
You may set the ``SMARTPRINTNG_LOCAL_CONVERSION`` environment variable
(to some value) in order to run the conversion locally inside the Plone
process without using an external Produce & Publish server.           

The environment varialble ``SMARTPRINTNG_ZIP_OUTPUT`` can be set to export
all resources used for the conversion into a ZIP file for debugging purposes.
The path of the generated ZIP file is logged within the standard Zope/Plone
logfile (or the console if Plone is running in foreground).
