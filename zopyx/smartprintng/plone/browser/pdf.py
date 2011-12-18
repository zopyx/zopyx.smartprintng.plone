################################################################
# zopyx.smartprintng.plone
# (C) 2011,  ZOPYX Limited & Co. KG, D-72070 Tuebingen, Germany
################################################################

import os
import codecs
import shutil
import tempfile
import zipfile

from compatible import InitializeClass
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.ATContentTypes.interface.folder import IATFolder
from ZPublisher.Iterators import filestream_iterator
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile as ViewPageTemplateFile2

from zopyx.smartprintng.plone.logger import LOG
from zopyx.smartprintng.plone.resources import resources_registry
from zopyx.smartprintng.plone import Transformer

import splitter
from util import getLanguageForObject

cwd = os.path.dirname(os.path.abspath(__file__))

# server host/port of the SmartPrintNG server
URL = os.environ.get('SMARTPRINTNG_SERVER', 'http://localhost:6543')
LOCAL_CONVERSION = 'SMARTPRINTNG_LOCAL_CONVERSION' in os.environ
ZIP_OUTPUT = 'SMARTPRINTNG_ZIP_OUTPUT' in os.environ

class ProducePublishView(BrowserView):
    """ Produce & Publish view (using Produce & Publish server) """

    template = ViewPageTemplateFile('../resources_default/pdf_template_standalone.pt')

    # default transformations used for the default PDF view.
    # 'transformations' can be overriden within a derived ProducePublishView.
    # If you don't need any transformation -> redefine 'transformations'
    # as empty list or tuple

    transformations = (
        'makeImagesLocal',
#        'removeEmptyElements',
#        'removeInternalLinks',
#        'annotateInternalLinks',
#        'cleanupTables',
        'convertFootnotes',
        'removeCrapFromHeadings',
        'fixHierarchies',
        'addTableOfContents',
        )

    def copyResources(self, resources_dir, destdir):
        """ Copy over resources for a global or local resources directory into the 
            destination directory.
        """
        if os.path.exists(resources_dir):
            for name in os.listdir(resources_dir):
                fullname = os.path.join(resources_dir, name)
                if os.path.isfile(fullname):
                    shutil.copy(fullname, destdir)

    def transformHtml(self, html, destdir, transformations=None):
        """ Perform post-rendering HTML transformations """

        if transformations is None:
            transformations = self.transformations

        # the request can override transformations as well
        if self.request.has_key('transformations'):
            t_from_request = self.request['transformations']
            if isinstance(t_from_request, basestring):
                transformations = t_from_request and t_from_request.split(',') or []
            else:
                transformations = t_from_request

        T = Transformer(transformations, context=self.context, destdir=destdir)
        return T(html)

    def __call__(self, *args, **kw):

        try:
            return self.__call2__(*args, **kw)
        except:
            LOG.error('Conversion failed', exc_info=True)
            raise


    def __call2__(self, *args, **kw):
        """ URL parameters:
            'language' -  'de', 'en'....used to override the language of the
                          document
            'converter' - default to on the converters registered with
                          zopyx.convert2 (default: pdf-prince)
            'resource' - the name of a registered resource (directory)
            'template' - the name of a custom template name within the choosen
                         'resource' 
        """

        # Output directory
        tmpdir_prefix = os.path.join(tempfile.gettempdir(), 'produce-and-publish')
        if not os.path.exists(tmpdir_prefix):
            os.makedirs(tmpdir_prefix)
        destdir = tempfile.mkdtemp(dir=tmpdir_prefix, prefix=self.context.getId() + '-')

        # debug/logging
        params = kw.copy()
        params.update(self.request.form)
        LOG.info('new job (%s, %s) - outdir: %s' % (args, params, destdir))

        # get hold of the language (hyphenation support)
        language = getLanguageForObject(self.context)
        if params.get('language'):
            language = params.get('language')

        # Check for CSS injection
        custom_css = None
        custom_stylesheet = params.get('custom_stylesheet')
        if custom_stylesheet:
            custom_css = str(self.context.restrictedTraverse(custom_stylesheet, None))
            if custom_css is None:
                raise ValueError('Could not access custom CSS at %s' % custom_stylesheet)

        # check for resource parameter
        resource = params.get('resource')
        if resource:
            resources_directory = resources_registry.get(resource)
            if not resources_directory:
                raise ValueError('No resource "%s" configured' % resource)
            if not os.path.exists(resources_directory):
                raise ValueError('Resource directory for resource "%s" does not exist' % resource)
            self.copyResources(resources_directory, destdir)

            # look up custom template in resources directory
            template_name = params.get('template', 'pdf_template')
            if not template_name.endswith('.pt'):
                template_name += '.pt'
            template_filename = os.path.join(resources_directory, template_name)
            if not os.path.exists(template_filename):
                raise IOError('No template found (%s)' % template_filename)
            template = ViewPageTemplateFile2(template_filename)

        else:
            template = self.template

        # call the dedicated @@asHTML on the top-level node. For a leaf document
        # this will return either a HTML fragment for a single document or @@asHTML
        # might be defined as an aggregator for a bunch of documents (e.g. if the
        # top-level is a folderish object

        html_view = self.context.restrictedTraverse('@@asHTML', None)
        if not html_view:
            raise RuntimeError('Object at does not provide @@asHTML view (%s, %s)' % 
                               (self.context.absolute_url(1), self.context.portal_type))
        html_fragment = html_view()

        # arbitrary application data
        data = params.get('data', None)

        # Now render the complete HTML document
        html = template(self,
                        language=language,
                        request=self.request,
                        body=html_fragment,
                        custom_css=custom_css,
                        data=data,
                        )

        # and apply transformations
        html = self.transformHtml(html, destdir)

        # hack to replace '&' with '&amp;'
        html = html.replace('& ', '&amp; ')

        # and store it in a dedicated working directory
        dest_filename = os.path.join(destdir, 'index.html')
        fp = codecs.open(dest_filename, 'wb', encoding='utf-8')
        fp.write(html)
        fp.close()  

        # split HTML document into parts and store them on the filesystem
        # (making only sense for folderish content)
        if IATFolder.providedBy(self.context) and not 'no-split' in params:
            splitter.split_html(dest_filename, destdir)

        # copy over global styles etc.
        resources_dir = os.path.join(cwd, 'resources')
        self.copyResources(resources_dir, destdir)

        # copy over language dependent hyphenation data
        if language:
            hyphen_file = os.path.join(resources_dir, 'hyphenation', language + '.hyp')
            if os.path.exists(hyphen_file):
                shutil.copy(hyphen_file, destdir)

            hyphen_css_file = os.path.join(resources_dir, 'languages', language + '.css')
            if os.path.exists(hyphen_css_file):
                shutil.copy(hyphen_css_file, destdir)

        # now copy over resources (of a derived view)
        self.copyResources(getattr(self, 'local_resources', ''), destdir)
        if ZIP_OUTPUT or 'zip_output' in params:
            archivename = tempfile.mktemp(suffix='.zip')
            fp = zipfile.ZipFile(archivename, "w", zipfile.ZIP_DEFLATED) 
            for root, dirs, files in os.walk(destdir):
                #NOTE: ignore empty directories
                for fn in files:
                    absfn = os.path.join(root, fn)
                    zfn = absfn[len(destdir)+len(os.sep):] #XXX: relative path
                    fp.write(absfn, zfn)
            fp.close()
            LOG.info('ZIP file written to %s' % archivename)

        if 'no_conversion' in params:
            return destdir
        
        if LOCAL_CONVERSION:
            from zopyx.convert2 import Converter
            c = Converter(dest_filename)
            result = c(params.get('converter', 'pdf-pisa'))
            if result['status'] != 0:
                raise RuntimeError('Error during PDF conversion (%r)' % result)
            pdf_file = result['output_filename']
            LOG.info('Output file: %s' % pdf_file)
            return pdf_file
        else:
            # Produce & Publish server integration
            from zopyx.smartprintng.client.zip_client import Proxy2
            proxy = Proxy2(URL)
            result = proxy.convertZIP2(destdir, self.request.get('converter', 'pdf-prince'))
            LOG.info('Output file: %s' % result['output_filename'])
            return result['output_filename']

InitializeClass(ProducePublishView)


class PDFDownloadView(ProducePublishView):

    def __call__(self, *args, **kw):

        if not 'resource' in kw:
            kw['resource'] = 'pp-default'
        if not 'template' in kw:
            kw['template'] = 'pdf_template_standalone'
        kw['no-split'] = True

        output_file = super(PDFDownloadView, self).__call__(*args, **kw)
        mimetype = os.path.splitext(os.path.basename(output_file))[1]
        R = self.request.response
        R.setHeader('content-type', 'application/%s' % mimetype)
        R.setHeader('content-disposition', 'attachment; filename="%s.%s"' % (self.context.getId(), mimetype))
        R.setHeader('pragma', 'no-cache')
        R.setHeader('cache-control', 'no-cache')
        R.setHeader('Expires', 'Fri, 30 Oct 1998 14:19:41 GMT')
        R.setHeader('content-length', os.path.getsize(output_file))
        return filestream_iterator(output_file, 'rb').read()

InitializeClass(PDFDownloadView)


class GenericDownloadView(ProducePublishView):

    def __call__(self, *args, **kw):

        output_file = super(GenericDownloadView, self).__call__(*args, **kw)
        mimetype = os.path.splitext(os.path.basename(output_file))[1]
        # return output file over HTTP
        R = self.request.response
        R.setHeader('content-type', 'application/%s' % mimetype)
        R.setHeader('content-disposition', 'attachment; filename="%s.%s"' % (self.context.getId(), mimetype))
        R.setHeader('content-length', os.path.getsize(output_file))
        R.setHeader('pragma', 'no-cache')
        R.setHeader('cache-control', 'no-cache')
        R.setHeader('Expires', 'Fri, 30 Oct 1998 14:19:41 GMT')
        return filestream_iterator(output_file, 'rb')

InitializeClass(GenericDownloadView)
