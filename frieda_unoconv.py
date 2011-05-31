#!/usr/bin/python

### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU Library General Public License as published by
### the Free Software Foundation; version 2 only
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU Library General Public License for more details.
###
### You should have received a copy of the GNU Library General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
### Copyright 2007 Dag Wieers <dag@wieers.com>

import getopt, sys, os, glob, time

#extrapaths = ('/usr/lib/openoffice/program/', '/usr/lib/openoffice.org2.0/program/')
extrapaths = glob.glob('/usr/lib*/openoffice*/program/') + glob.glob('/usr/lib*/ooo*/program') + [ '/Applications/NeoOffice.app/Contents/program', ]
for path in extrapaths:
    try:
        sys.path.append(path)
        import uno, unohelper
        os.environ['PATH'] = '%s:' % path + os.environ['PATH']
        break
    except ImportError:
        sys.path.remove(path)
        continue
else:
    print >>sys.stderr, "frieda_unoconv: Cannot find the pyuno.so library in sys.path and known paths."
    print >>sys.stderr, "Please locate this library and send your feedback to <tools@lists.rpmforge.net>."
    sys.exit(1)

from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
from com.sun.star.io import IOException, XOutputStream
from com.sun.star.script import CannotConvertException
from com.sun.star.uno import Exception as UnoException

__version__ = "$Revision$"
# $Source$

VERSION = '0.3'

doctypes = ('graphics', 'presentation',)

oopid = None

class Fmt:
    def __init__(self, doctype, name, extension, summary, filter):
        self.doctype = doctype
        self.name = name
        self.extension = extension
        self.summary = summary
        self.filter = filter

    def __str__(self):
        return "%s [.%s]" % (self.summary, self.extension)

    def __repr__(self):
        return "%s/%s" % (self.name, self.doctype)

class FmtList:
    def __init__(self):
        self.list = []

    def add(self, doctype, name, extension, summary, filter):
        self.list.append(Fmt(doctype, name, extension, summary, filter))

    def byname(self, name):
        ret = []
        for fmt in self.list:
            if fmt.name == name:
                ret.append(fmt)
        return ret

    def byextension(self, extension):
        ret = []
        for fmt in self.list:
            if '.'+fmt.extension == extension:
                ret.append(fmt)
        return ret

    def bydoctype(self, doctype, name):
        ret = []
        for fmt in self.list:
            if fmt.name == name and fmt.doctype == doctype:
                ret.append(fmt)
                return ret

    def display(self, doctype):
        print >>sys.stderr, "The following list of %s formats are currently available:\n" % doctype
        for fmt in self.list:
            if fmt.doctype == doctype:
                print >>sys.stderr, "  %-8s - %s" % (fmt.name, fmt)
        print >>sys.stderr

class OutputStream( unohelper.Base, XOutputStream ):
    def __init__( self ):
        self.closed = 0

    def closeOutput(self):
        self.closed = 1

    def writeBytes( self, seq ):
        sys.stdout.write( seq.value )

    def flush( self ):
        pass

fmts = FmtList()


### Graphics
fmts.add('graphics', 'bmp', 'bmp', 'Windows Bitmap', 'draw_bmp_Export')
fmts.add('graphics', 'emf', 'emf', 'Enhanced Metafile', 'draw_emf_Export')
fmts.add('graphics', 'eps', 'eps', 'Encapsulated PostScript', 'draw_eps_Export')
fmts.add('graphics', 'gif', 'gif', 'Graphics Interchange Format', 'draw_gif_Export')
fmts.add('graphics', 'html', 'html', 'HTML Document (OpenOffice.org Draw)', 'draw_html_Export')
fmts.add('graphics', 'jpg', 'jpg', 'Joint Photographic Experts Group', 'draw_jpg_Export')
fmts.add('graphics', 'met', 'met', 'OS/2 Metafile', 'draw_met_Export')
fmts.add('graphics', 'odd', 'odd', 'OpenDocument Drawing', 'draw8')
fmts.add('graphics', 'otg', 'otg', 'OpenDocument Drawing Template', 'draw8_template')
fmts.add('graphics', 'pbm', 'pbm', 'Portable Bitmap', 'draw_pbm_Export')
fmts.add('graphics', 'pct', 'pct', 'Mac Pict', 'draw_pct_Export')
fmts.add('graphics', 'pdf', 'pdf', 'Portable Document Format', 'draw_pdf_Export')
fmts.add('graphics', 'pgm', 'pgm', 'Portable Graymap', 'draw_pgm_Export')
fmts.add('graphics', 'png', 'png', 'Portable Network Graphic', 'draw_png_Export')
fmts.add('graphics', 'ppm', 'ppm', 'Portable Pixelmap', 'draw_ppm_Export')
fmts.add('graphics', 'ras', 'ras', 'Sun Raster Image', 'draw_ras_Export')
fmts.add('graphics', 'std', 'std', 'OpenOffice.org 1.0 Drawing Template', 'draw_StarOffice_XML_Draw_Template')
fmts.add('graphics', 'svg', 'svg', 'Scalable Vector Graphics', 'draw_svg_Export')
fmts.add('graphics', 'svm', 'svm', 'StarView Metafile', 'draw_svm_Export')
fmts.add('graphics', 'swf', 'swf', 'Macromedia Flash (SWF)', 'draw_flash_Export')
fmts.add('graphics', 'sxd', 'sxd', 'OpenOffice.org 1.0 Drawing', 'StarOffice XML (Draw)')
fmts.add('graphics', 'sxd3', 'sxd', 'StarDraw 3.0', 'StarDraw 3.0')
fmts.add('graphics', 'sxd5', 'sxd', 'StarDraw 5.0', 'StarDraw 5.0')
fmts.add('graphics', 'tiff', 'tiff', 'Tagged Image File Format', 'draw_tif_Export')
fmts.add('graphics', 'vor', 'vor', 'StarDraw 5.0 Template', 'StarDraw 5.0 Vorlage')
fmts.add('graphics', 'vor3', 'vor', 'StarDraw 3.0 Template', 'StarDraw 3.0 Vorlage')
fmts.add('graphics', 'wmf', 'wmf', 'Windows Metafile', 'draw_wmf_Export')
fmts.add('graphics', 'xhtml', 'xhtml', 'XHTML', 'XHTML Draw File')
fmts.add('graphics', 'xpm', 'xpm', 'X PixMap', 'draw_xpm_Export')

### Presentation
fmts.add('presentation', 'bmp', 'bmp', 'Windows Bitmap', 'impress_bmp_Export')
fmts.add('presentation', 'emf', 'emf', 'Enhanced Metafile', 'impress_emf_Export')
fmts.add('presentation', 'eps', 'eps', 'Encapsulated PostScript', 'impress_eps_Export')
fmts.add('presentation', 'gif', 'gif', 'Graphics Interchange Format', 'impress_gif_Export')
fmts.add('presentation', 'html', 'html', 'HTML Document (OpenOffice.org Impress)', 'impress_html_Export')
fmts.add('presentation', 'jpg', 'jpg', 'Joint Photographic Experts Group', 'impress_jpg_Export')
fmts.add('presentation', 'met', 'met', 'OS/2 Metafile', 'impress_met_Export')
fmts.add('presentation', 'odd', 'odd', 'OpenDocument Drawing (Impress)', 'impress8_draw')
fmts.add('presentation', 'odg', 'odg', 'OpenOffice.org 1.0 Drawing (OpenOffice.org Impress)', 'impress_StarOffice_XML_Draw')
fmts.add('presentation', 'odp', 'odp', 'OpenDocument Presentation', 'impress8')
fmts.add('presentation', 'otp', 'otp', 'OpenDocument Presentation Template', 'impress8_template')
fmts.add('presentation', 'pbm', 'pbm', 'Portable Bitmap', 'impress_pbm_Export')
fmts.add('presentation', 'pct', 'pct', 'Mac Pict', 'impress_pct_Export')
fmts.add('presentation', 'pdf', 'pdf', 'Portable Document Format', 'impress_pdf_Export')
fmts.add('presentation', 'pgm', 'pgm', 'Portable Graymap', 'impress_pgm_Export')
fmts.add('presentation', 'png', 'png', 'Portable Network Graphic', 'impress_png_Export')
fmts.add('presentation', 'pot', 'pot', 'Microsoft PowerPoint 97/2000/XP Template', 'MS PowerPoint 97 Vorlage')
fmts.add('presentation', 'ppm', 'ppm', 'Portable Pixelmap', 'impress_ppm_Export')
fmts.add('presentation', 'ppt', 'ppt', 'Microsoft PowerPoint 97/2000/XP', 'MS PowerPoint 97')
fmts.add('presentation', 'pwp', 'pwp', 'PlaceWare', 'placeware_Export')
fmts.add('presentation', 'ras', 'ras', 'Sun Raster Image', 'impress_ras_Export')
fmts.add('presentation', 'sda', 'sda', 'StarDraw 5.0 (OpenOffice.org Impress)', 'StarDraw 5.0 (StarImpress)')
fmts.add('presentation', 'sdd', 'sdd', 'StarImpress 5.0', 'StarImpress 5.0')
fmts.add('presentation', 'sdd3', 'sdd', 'StarDraw 3.0 (OpenOffice.org Impress)', 'StarDraw 3.0 (StarImpress)')
fmts.add('presentation', 'sdd4', 'sdd', 'StarImpress 4.0', 'StarImpress 4.0')
fmts.add('presentation', 'sti', 'sti', 'OpenOffice.org 1.0 Presentation Template', 'impress_StarOffice_XML_Impress_Template')
fmts.add('presentation', 'stp', 'stp', 'OpenDocument Presentation Template', 'impress8_template')
fmts.add('presentation', 'svg', 'svg', 'Scalable Vector Graphics', 'impress_svg_Export')
fmts.add('presentation', 'svm', 'svm', 'StarView Metafile', 'impress_svm_Export')
fmts.add('presentation', 'swf', 'swf', 'Macromedia Flash (SWF)', 'impress_flash_Export')
fmts.add('presentation', 'sxi', 'sxi', 'OpenOffice.org 1.0 Presentation', 'StarOffice XML (Impress)')
fmts.add('presentation', 'tiff', 'tiff', 'Tagged Image File Format', 'impress_tif_Export')
fmts.add('presentation', 'vor', 'vor', 'StarImpress 5.0 Template', 'StarImpress 5.0 Vorlage')
fmts.add('presentation', 'vor3', 'vor', 'StarDraw 3.0 Template (OpenOffice.org Impress)', 'StarDraw 3.0 Vorlage (StarImpress)')
fmts.add('presentation', 'vor4', 'vor', 'StarImpress 4.0 Template', 'StarImpress 4.0 Vorlage')
fmts.add('presentation', 'vor5', 'vor', 'StarDraw 5.0 Template (OpenOffice.org Impress)', 'StarDraw 5.0 Vorlage (StarImpress)')
fmts.add('presentation', 'wmf', 'wmf', 'Windows Metafile', 'impress_wmf_Export')
fmts.add('presentation', 'xhtml', 'xml', 'XHTML', 'XHTML Impress File')
fmts.add('presentation', 'xpm', 'xpm', 'X PixMap', 'impress_xpm_Export')

class Options:
    def __init__(self, args):
        self.stdout = False
        self.showlist = False
        self.listener = False
        self.format = None
        self.verbose = 0
        self.doctype = None
        self.server = 'localhost'
        self.port = '2002'
        self.connection = None
        self.filenames = []

        ### Get options from the commandline
        try:
            opts, args = getopt.getopt (args, 'c:d:f:hLlp:s:t:v',
                ['connection=', 'doctype=', 'format=', 'help', 'listener', 'port=', 'server=', 'show', 'stdout', 'verbose', 'version'] )
        except getopt.error, exc:
            print 'unoconv: %s, try unoconv -h for a list of all the options' % str(exc)
            sys.exit(255)

        for opt, arg in opts:
            if opt in ['-h', '--help']:
                self.usage()
                print
                self.help()
                sys.exit(1)
            elif opt in ['-c', '--connection']:
                self.connection = arg
            elif opt in ['-d', '--doctype']:
                self.doctype = arg
            elif opt in ['-f', '--format']:
                self.format = arg
            elif opt in ['-l', '--listener']:
                self.listener = True
            elif opt in ['--show']:
                self.showlist = True
            elif opt in ['-p', '--port']:
                self.port = arg
            elif opt in ['-s', '--server']:
                self.server = arg
            elif opt in ['--stdout']:
                self.stdout = True
            elif opt in ['-v', '--verbose']:
                self.verbose = self.verbose + 1
            elif opt in ['--version']:
                self.version()
                sys.exit(255)

        ### Enable verbosity
        if self.verbose >= 3:
            print >>sys.stderr, 'Verbosity set to level %d' % (self.verbose - 1)

        self.filenames = args

        if not self.listener and not self.showlist and self.doctype != 'list' and not self.filenames:
            print >>sys.stderr, 'unoconv: you have to provide a filename as argument'
            print >>sys.stderr, 'Try `unoconv -h\' for more information.'
            sys.exit(255)

        ### Set connection string
        if not self.connection:
            self.connection = "socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (self.server, self.port)
#            self.connection = "socket,host=%s,port=%s;urp;" % (self.server, self.port)

        ### Make it easier for people to use a doctype (first letter is enough)
        if self.doctype:
            for doctype in doctypes:
                if doctype.startswith(self.doctype):
                    self.doctype = doctype

        ### Check if the user request to see the list of formats
        if self.showlist or self.format == 'list':
            if self.doctype:
                fmts.display(self.doctype)
            else:
                for t in doctypes:
                    fmts.display(t)
            sys.exit(0)

        ### If no format was specified, probe it or provide it
        if not self.format:
            l = sys.argv[0].split('2')
            if len(l) == 2:
                self.format = l[1]
            else:
                self.format = 'pdf'

    def version(self):
        print 'unoconv %s' % VERSION
        print 'Written by Dag Wieers <dag@wieers.com>'
        print 'Homepage at http://dag.wieers.com/home-made/unoconv/'
        print
        print 'platform %s/%s' % (os.name, sys.platform)
        print 'python %s' % sys.version
        print
        print 'build revision $Rev$'

    def usage(self):
        print >>sys.stderr, 'usage: unoconv [options] file [file2 ..]'

    def help(self):
        print >>sys.stderr, '''Convert from and to any format supported by OpenOffice

unoconv options:
  -c, --connection=string  use a custom connection string
  -d, --doctype=type       specify document type
                           (document, graphics, presentation, spreadsheet)
  -f, --format=format      specify the output format
  -l, --listener           start a listener to use by unoconv clients
  -p, --port               specify the port (default: 2002)
                           to be used by client or listener
  -s, --server             specify the server address (default: localhost)
                           to be used by client or listener
      --show               list the available output formats
      --stdout             write output to stdout
  -v, --verbose            be more and more verbose
'''

class Convertor:
    def __init__(self):
        global oopid
        unocontext = None

        ### Do the OpenOffice component dance
        self.context = uno.getComponentContext()
        resolver = self.context.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", self.context)

        ### Test for an existing connection
        try:
            unocontext = resolver.resolve("uno:%s" % op.connection)
        except Exception, e:
            error(2, "Existing listener not found.\n%s" % e)

            ### Test if we can use an Openoffice *binary* in our (modified) path
            for bin in ('soffice.bin', 'soffice', ):
                error(2, "Trying to launch our own listener using %s." % bin)
                try:
                    oopid = os.spawnvp(os.P_NOWAIT, bin, [bin, "-nologo", "-nodefault", "-accept=%s" % op.connection]);
                    time.sleep(1)
                    unocontext = resolver.resolve("uno:%s" % op.connection)
                    break
                except Exception, e:
                    error(3, "Launch of %s failed.\n%s" % (bin, e))
                    continue

        if not unocontext:
            die(251, "Unable to connect or start own listener. Aborting.")

        ### And some more OpenOffice magic
        unosvcmgr = unocontext.ServiceManager
        self.desktop = unosvcmgr.createInstanceWithContext("com.sun.star.frame.Desktop", unocontext)
        self.cwd = unohelper.systemPathToFileUrl( os.getcwd() )

    def getformat(self, inputfn):
        doctype = None

        ### Get the output format from mapping
        if op.doctype:
            outputfmt = fmts.bydoctype(op.doctype, op.format)
        else:
            outputfmt = fmts.byname(op.format)

            if not outputfmt:
                outputfmt = fmts.byextension('.'+op.format)

        ### If no doctype given, check list of acceptable formats for input file ext doctype
        ### FIXME: This should go into the for-loop to match each individual input filename
        if outputfmt:
            inputext = os.path.splitext(inputfn)[1]
            inputfmt = fmts.byextension(inputext)
            if inputfmt:
                for fmt in outputfmt:
                    if inputfmt[0].doctype == fmt.doctype:
                        doctype = inputfmt[0].doctype
                        outputfmt = fmt
                        break
                else:
                    outputfmt = outputfmt[0]
    #       print >>sys.stderr, 'unoconv: format `%s\' is part of multiple doctypes %s, selecting `%s\'.' % (format, [fmt.doctype for fmt in outputfmt], outputfmt[0].doctype)
            else:
                outputfmt = outputfmt[0]

        ### No format found, throw error
        if not outputfmt:
            if doctype:
                print >>sys.stderr, 'unoconv: format [%s/%s] is not known to unoconv.' % (op.doctype, op.format)
            else:
                print >>sys.stderr, 'unoconv: format [%s] is not known to unoconv.' % op.format
            die(1)

        return outputfmt

    def convert(self, inputfn):
        doc = None
        outputfmt = self.getformat(inputfn)

        if op.verbose > 0:
            print >>sys.stderr, 'Input file:', inputfn

        if not os.path.exists(inputfn):
            print >>sys.stderr, 'unoconv: file `%s\' does not exist.' % inputfn
            exitcode = 1
            return

        try:
            ### Load inputfile
            inputprops = ( PropertyValue( "Hidden" , 0 , True, 0 ), )

            inputurl = unohelper.absolutize(self.cwd, unohelper.systemPathToFileUrl(inputfn))
            doc = self.desktop.loadComponentFromURL( inputurl , "_blank", 0, inputprops )

            if not doc:
                raise UnoException("File could not be loaded by OpenOffice", None)

            error(1, "Selected output format: %s" % outputfmt)
            error(1, "Selected ooffice filter: %s" % outputfmt.filter)
            error(1, "Used doctype: %s" % outputfmt.doctype)

            ### Write outputfile
            outputprops = (
                    PropertyValue( "FilterName" , 0, outputfmt.filter , 0 ),
                    PropertyValue( "Overwrite" , 0, True , 0 ),
                    PropertyValue( "OutputStream", 0, OutputStream(), 0),
                   )

            if not op.stdout:
                (outputfn, ext) = os.path.splitext(inputfn)
                outputfn = outputfn + '.' + outputfmt.extension
                outputurl = unohelper.absolutize( self.cwd, unohelper.systemPathToFileUrl(outputfn) )
                doc.storeToURL(outputurl, outputprops)
                error(1, "Output file: %s" % outputfn)
            else:
                doc.storeToURL("private:stream", outputprops)

            doc.dispose()

        except SystemError, e:
            error(0, "unoconv: SystemError during conversion: %s" % e)
            error(0, "The provided document cannot be converted to the desired format.")
            exitcode = 1

        except UnoException, e:
            error(0, "unoconv: UnoException during conversion: %s" % e.Message)
            error(0, "The provided document cannot be converted to the desired format.")
            exitcode = 1

        except IOException, e:
            error(0, "unoconv: IOException during conversion: %s" % e.Message)
            error(0, "The provided document cannot be exported to %s." % outputfmt)
            exitcode = 1

        except CannotConvertException, e:
            error(0, "unoconv: CannotConvertException during conversion: %s" % e.Message)
            exitcode = 1

class Listener:
    def __init__(self):
        error(1, "Start listener on %s:%s" % (op.server, op.port))
        for bin in ('soffice.bin', 'soffice', ):
            error(2, "Warning: trying to launch %s." % bin)
            try:
                os.execvp(bin, [bin, "-nologo", "-nodefault", "-accept=%s" % op.connection]);
            except:
                continue
        else:
            die(254, "Failed to start listener on %s:%s" % (op.server, op.port))
        die(253, "Existing listener found, aborting.")

def error(level, str):
    "Output error message"
    if level <= op.verbose:
        print >>sys.stderr, str

def info(level, str):
    "Output info message"
    if not op.stdout and level <= op.verbose:
        print >>sys.stdout, str

def die(ret, str=None):
    "Print error and exit with errorcode"
    global oopid
    if str:
        error(0, 'Error: %s' % str)
    if oopid:
        error(2, 'Taking down OpenOffice with pid %s.' % oopid)
#        os.setpgid(oopid, 0)
#        os.killpg(os.getpgid(oopid), 15)
        try:
            os.kill(oopid, 15)
            error(2, 'Waiting for OpenOffice with pid %s to disappear.' % oopid)
            os.waitpid(oopid, os.WUNTRACED)
        except:
            error(2, 'No OpenOffice with pid %s to take down' % oopid)
    sys.exit(ret)

def main():
    try:
        if op.listener:
            listener = Listener()
        else:
            convertor = Convertor()

        for inputfn in op.filenames:
            convertor.convert(inputfn)

    except NoConnectException, e:
        error(0, "unoconv: could not find an existing connection to Open Office at %s:%s." % (op.server, op.port))
        if op.connection:
            error(0, "Please start an OpenOffice instance on server '%s' by doing:\n\n    unoconv --listener --server %s --port %s\n\nor alternatively:\n\n    ooffice -nologo -nodefault -accept=\"%s\"" % (op.server, op.server, op.port, op.connection))
        else:
            error(0, "Please start an OpenOffice instance on server '%s' by doing:\n\n    unoconv --listener --server %s --port %s\n\nor alternatively:\n\n    ooffice -nologo -nodefault -accept=\"socket,host=%s,port=%s;urp;\"" % (op.server, op.server, op.port, op.server, op.port))
            error(0, "Please start an ooffice instance on server '%s' by doing:\n\n    ooffice -nologo -nodefault -accept=\"socket,host=localhost,port=%s;urp;\"" % (op.server, op.port))
        exitcode = 1
#    except UnboundLocalError:
#        die(252, "Failed to connect to remote listener.")
    except OSError:
        error(0, "Warning: failed to launch OpenOffice. Aborting.")

### Main entrance
if __name__ == '__main__':
    exitcode = 0

    op = Options(sys.argv[1:])
    try:
        main()
    except KeyboardInterrupt, e:
        die(6, 'Exiting on user request')
    die(exitcode)
