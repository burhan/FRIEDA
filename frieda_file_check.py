#!/usr/bin/python

import frieda_settings as settings

# python libraries
import os
import sys
import time
import commands
import logging
import hashlib
import shelve

if __name__ == '__main__':
    try:
        logging.basicConfig(filename=settings.LOG_FILENAME, level=settings.LOG_LEVEL,
                            format="%(asctime)s %(levelname)s: %(message)s")
    except IOError:
        LOG_FILENAME = '/tmp/frieda_%s.log' % time.strftime('%b_%d_%Y_%I%M%P')
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,
                            format="%(asctime)s %(levelname)s: %(message)s")

try:
    import PythonMagick
    python_magick = True
except ImportError:
    no_python_magick = False
    logging.debug("PythonMagick not found; cannot convert 16-bit TIFFs to 8-bit to render properly in ODP/PPT.  "
                  "Install PythonMagick with `sudo apt-get install python-pythonmagick` (e.g., ubuntu)"
                  "or from http://www.imagemagick.org/download/python/")
    # Skip conversion of 16-bit TIFFs (rendered as black in ODP/PPT) to 8-bit TIFFs (properly rendered)

try:
    from odf.opendocument import OpenDocumentPresentation
    from odf.style import Style, MasterPage, PageLayout, PageLayoutProperties, GraphicProperties, DrawingPageProperties
    from odf.draw  import Page, Frame, Image
except ImportError:
    logging.critical("ODFPY is not found; cannot create an OpenDocument.  "
                     "ODFPY can be obtained from http://odfpy.forge.osor.eu/ or http://pypi.python.org/pypi/odfpy/ "
                     "or http://opendocumentfellowship.com/projects/odfpy")
    sys.exit()

try:
    from PIL import Image as PILImage # PIL; changed name to not overlap with ODF.draw.Image
except ImportError:
    logging.critical("PIL (PythonImagingLibrary is not found; cannot process images.  "
                     "PIL can be obtained from http://www.pythonware.com/products/pil/  "
                     "http://effbot.org/downloads/#pil or http://pypi.python.org/pypi/PIL"
                     "or installed via `sudo apt-get install python-imaging`")
    sys.exit()

from frieda_sendmail import EmailSet, SMTPEmail

def get_hash(emailaddr):
    '''Don't modify this function/salt, or all directories should change
    >>> get_md5('jal2018') == 'fe876e4fda'
    True
    '''
    return hashlib.sha512(emailaddr.upper()+settings.HASHSALT).hexdigest()[0:settings.HASHLENGTH]

def get_media_dir(emailaddr, as_url=False, trailing_slash=False):
    root = settings.WEB_ROOT_URL if as_url else settings.WEB_ROOT_DIR
    return os.path.join(root, get_hash(emailaddr), emailaddr)

def get_media_path(emailaddr, filename='', as_url=True):
    root = settings.WEB_ROOT_URL if as_url else settings.WEB_ROOT_DIR
    return os.path.join(root, get_hash(emailaddr), emailaddr, filename)

def run_command(command):
    logging.debug(command)
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
        logging.error("%s %s %s" % (command, status, output))
    logging.debug(output)
    return (status==0)

def run_command_get_output(command):
    logging.debug(command)
    (status, output) = commands.getstatusoutput(command)
    if status != 0:
        logging.error("%s %s %s" % (command, status, output))
    logging.debug(output)
    return output

def kill_soffice():
    uno_pid = run_command_get_output("ps aux | grep soffice.bin | grep -v grep | gawk '{ print $2 }'")
    status = 0
    for u in uno_pid.split():
        status = run_command('kill -9 %s' % u)
    return status

def ensure_path_exists(path_dir):
    if not os.path.exists(path_dir):
        run_command('mkdir -p %s' % path_dir)
    return True


def sort_files_by_time(filelist, root=''):
    if len(filelist) <= 0:
        return []
    filelist_tuple = [(os.path.getmtime(os.path.join(root,f)), f) for f in filelist]
    filelist_tuple.sort()
    return zip(*filelist_tuple)[1]



def gen_announcement_email(full_email, linked_files, num_images=0, ppt_content=None):
    if ppt_content == None:
        ppt_content = []

    if len(linked_files) == 0:
        return False
    slide = 1
    slide_contents_list = []
    slide_contents_list.append("<p>Powerpoint Slide Contents:</p><ul>")
    for (subdir,cnt) in ppt_content:
        if cnt > 1:
            slide_contents_list.append("<li>Slides %d-%d: %s" % (slide, slide+cnt-1, subdir))
        else:
            slide_contents_list.append("<li>Slide  %d   : %s" % (slide, subdir))
        slide += cnt
    slide_contents_list.append("</ul>")
    slide_contents = ''.join(slide_contents_list)
    file_link_list = []
    for lf in linked_files:
        file_link_list.append(
                settings.FILE_LINKS_FORMAT.format(linked_file_url=get_media_path(emailaddr,lf),
                                                  email = emailaddr,
                                                  linked_file_name=lf,
                                                  ))
    file_links = ''.join(file_link_list)

    emailaddr = full_email
    fromaddr = settings.DEFAULT_FROMADDR

    email = SMTPEmail(fromaddr = fromaddr)
    email.add_recipients([full_email,])
    email.set_subject(settings.EMAIL_SUBJECT.format(num_images=num_images, email=emailaddr))
    browse_files_link
    email.set_body(settings.BODY.format(file_links=file_links, slide_contents=slide_contents,
                                        email=emailaddr, num_images=num_images,
                                        browse_files_url=get_media_path(emailaddr)))
    if num_images > 0:
        logging.debug('Creating Email')
        return email
    else:
        return None

def get_latest_time(file_name):
    return max(0.0,os.path.getmtime(file_name),)
               # os.path.getatime(file_name),
               # os.path.getctime(file_name))

def files_modified_recently(subdir, delay_time = settings.DELAY_TIME_SEC):
    latest_mod_time = 0
    for root,dir_list,wfile_list in os.walk(subdir):
        for s in settings.SKIPPED_DIRS:
            if s in dir_list:
                dir_list.remove(s) # skip visiting

        for f in wfile_list:
            mod_time =  get_latest_time(os.path.join(root,f))
            if mod_time > latest_mod_time:
                latest_mod_time = mod_time

    cur_time = time.time()
    logging.debug("Last modified time: %s, Cur time: %s" % (time.ctime(latest_mod_time), time.ctime(cur_time)))

    if cur_time < delay_time + latest_mod_time:
        return True # files were modified too recently
    elif cur_time == 0:
        return True # no files present
    else:
        return False


def getImageInfoFileName(picture_file_name):
    try:
        the_image = PILImage.open(picture_file_name)
        (w,h) = the_image.size
        ct = the_image.format.lower()
        return ct,w,h
    except(IOError):
        return "not image", 1,1

def process_user_image_files(emailaddr):
    pagewidth = 800
    pageheight = 600
    logging.debug("cur_path %s" % (os.path.realpath('.'),) )
    odpfile = 'tfs_%s_%s.odp' % (emailaddr, time.strftime('%b_%d_%Y_%I%M%P'))
    ppt_content = []

    file_list = []
    for wroot, wsubdir, wfiles in os.walk('.'):
        wfiles = sort_files_by_time(wfiles, wroot)
        wsubdir = sort_files_by_time(wsubdir, wroot)
        cnt = 0
        for f in wfiles:
            cnt += 1
            file_list.append(os.path.join(wroot, f))
        if cnt != 0:
            wroot2 = '/' if len(wroot) < 2 else wroot[1:]
            ppt_content.append((wroot2, cnt))

    logging.debug('file_list: %r' % file_list)
    doc = OpenDocumentPresentation()
    pagelayout = PageLayout(name="MyLayout")
    pagelayout.addElement(PageLayoutProperties(backgroundcolor="#000000", margin="0pt", pagewidth="%dpt" %pagewidth,
                                               pageheight="%dpt" % pageheight, printorientation="landscape"))
    doc.automaticstyles.addElement(pagelayout)
    photostyle = Style(name="RadTeaching-photo", family="presentation")
    doc.styles.addElement(photostyle)
    dstyle = Style(name="d", family="drawing-page")
    dstyle.addElement(GraphicProperties(fillcolor="#000000"))
    dstyle.addElement(DrawingPageProperties(fill=True,
                                            fillcolor="#000000"))
    doc.automaticstyles.addElement(dstyle)


    masterpage = MasterPage(name="RadTeaching", pagelayoutname=pagelayout)
    doc.masterstyles.addElement(masterpage)
    images_added = 0
    # os.chdir(subdir)
    for picture in file_list:
        try:
            pictdata = open(picture).read()
            logging.debug("Adding %s" % (picture))
        except:
            logging.debug("Skipping %s" % (picture))
            continue
        ct,w,h = getImageInfoFileName(picture)
        if ct == 'not image':
            if picture[-4:] == '.dcm':
                png_picture = picture.replace('.dcm','.png')
                logging.debug("Converting %s to %s" % (picture, png_picture) )
                run_command(""" dcmj2pnm +on +Wi 1 %s %s """ % (picture, png_picture))
                picture = png_picture
                ct,w,h = getImageInfoFileName(picture)

        if ct not in ("jpeg", "jpg", "tiff", "png", "bmp", "gif", "tif"):
            logging.debug("Skipping %s unrecognized type %s" % (picture,ct) )
            continue
        if ct == "tiff" or ct == "tif":
            png_picture = picture.replace(".tiff",".tif").replace(".tif", ".png")
            logging.debug("Converting %s to %s" % (picture, png_picture))
            img = PythonMagick.Image()
            img.read(picture)
            if img.depth() > 8: # powerpoint can't handle 16 bit TIFF images.
                img.write(png_picture)
                del img
                picture = png_picture
                ct,w,h = getImageInfoFileName(picture)

        images_added += 1
        if w*pageheight > h*pagewidth: #check if width or height is limit to zooming
            h = float(h) * (pagewidth-2.0)/float(w)
            w = pagewidth - 2.0
        else:
            w = float(w)*(pageheight-2.0) / float(h)
            h = pageheight -2.0

        page = Page(stylename=dstyle, masterpagename=masterpage)
        doc.presentation.addElement(page)

        offsetx = (pagewidth - w)/2.0
        offsety = (pageheight - h)/2.0
        photoframe = Frame(stylename=photostyle, width='%fpt' % w, height='%fpt' % h,
                           x = '%fpt' % offsetx, y='%fpt' % offsety)
        page.addElement(photoframe)
        href = doc.addPicture(picture)
        photoframe.addElement(Image(href=href))

    if images_added > 0:
        logging.debug('Saving ODP as %s/%s' % (os.path.realpath('.'), odpfile))
        doc.save(odpfile)
    return (odpfile, images_added, ppt_content) if images_added > 0 else (False, 0, None)


def check_dir_new_file(full_email, email_set, stat_shelf, samba_dir):
    os.chdir(os.path.join(samba_dir,full_email))

    (wlk_root, wlk_subdir, wlk_files) = os.walk('.').next()
    linked_files = []

    if len(wlk_subdir)==0 and len(wlk_files)==0:
        # logging.debug('No files in %s' % os.path.realpath('.'))
        return False
    if files_modified_recently('.'):
        logging.debug('Files in %s modified recently' % os.path.realpath('.'))
        return False
    amp_loc = full_email.find('@')
    if amp_loc > 0:
        emailaddr = full_email[:amp_loc]
    else:
        emailaddr = full_email

    run_command("""for i in `ls -tR *.dcm */*.dcm */*/*.dcm */*/*/*.dcm */*/*/*/*.dcm */*/*/*/*/*.dcm 2> /dev/null`; """
                """do echo $i; """
                """dcmodify --ignore-errors -m "(0010,0010)=X" -m "(0010,0020)=X" -m "(0010,0030)=X" -m "(0009,1040)=X" -m "(0008,0090)=X" -m "(0008,0050)=X" -m "(0010,1000)=X" $i; """
                """rm $i.bak ; """
                """done""")
    ## Above calls dcmodify to deidentify several fields by setting them to "X" ;
    ## done before moving files to webdata directory or before checking last modification time.
    ## (0010,0010) - Patient Name, (0010,0020) - Patient ID, (0010,0030) - Patient Birth Date,
    ## (0009,1040) - Unknown (but contained patient name), (0008,0050) - Accession #, (0008,0090) - Ref Physician Name

    email_zip_path = get_media_path(emailaddr, settings.ZIP_DIR, as_url=False)
    logging.debug("Creating Zip File of Current Files in Apache Zip Path: %s" % email_zip_path)
    ensure_path_exists(email_zip_path)
    zip_file_str = os.path.join(settings.ZIP_DIR, 'tfs_%s.zip' % time.strftime('%b_%d_%Y_%I%M%P'))
     
    run_command("""zip -r %s .""" % get_media_path(emailaddr, zip_file_str, as_url=False))

    email_tmp_path = get_media_path(emailaddr, settings.TMP_DIR, as_url=False)

    logging.debug("Removing Old Files from Apache Tmp Path: %s" % email_tmp_path)
    ensure_path_exists(email_tmp_path)
    run_command("""rm -rfv %r """ % str(email_tmp_path))
    mytime = time.strftime('%d_%b_%Y__%H_%M_%S')
    email_tmp_path = os.path.join(email_tmp_path, mytime)
    ensure_path_exists(email_tmp_path)

    logging.debug("Moving Files to Apache Tmp Path: %s" % email_tmp_path)
    for ws in wlk_subdir + wlk_files:
        run_command("""mv -t %s/ %r """ % (email_tmp_path, str(ws)))

    os.chdir(email_tmp_path)
    (t_root, t_subdir, t_files) = os.walk('.').next()

    (tmp_odp, num_images, ppt_content) = process_user_image_files(emailaddr)
    try:
        if num_images > 0 and stat_shelf != None:
            # log statistics
            userppt = emailaddr + 'ppt'
            userimg = emailaddr + 'img'
            ppt = 'ppt'
            img = 'img'
            for k, v in ((userppt,1), (userimg, num_images), (ppt,1), (img, num_images)):
                if stat_shelf.has_key(k):
                    stat_shelf[k] += v
                else:
                    stat_shelf[k] = v
    except:
        logging.error("Statistics Failed")

    if tmp_odp:
        success = run_command(""" frieda_unoconv -f ppt %r """ % str(os.path.join(t_root,tmp_odp)))
        tmp_ppt = tmp_odp[:-3] + 'ppt'
        if success:
            logging.debug('Converted %s to ppt successfully; removing odp' % tmp_odp)
        else:
            logging.error('Unsuccessful ppt conversion; trying again after 60s')
            time.sleep(15)
            kill_soffice()
            time.sleep(45)
            if not os.path.exists(os.path.join(email_tmp_path,tmp_ppt)):
                success = run_command(""" frieda_unoconv -f ppt %r """ % str(os.path.join(t_root,tmp_odp)))
        odp_path = get_media_path(emailaddr, settings.ODP_DIR, as_url=False)
        ensure_path_exists(odp_path)
        run_command("mv -t %s/ '%s'" % (odp_path, os.path.join(email_tmp_path, tmp_odp)))
        mv_ppt = run_command("""mv -t %s/ %r """ % (get_media_path(emailaddr, as_url=False),
                                                    str(os.path.join(email_tmp_path, tmp_ppt))))


        linked_files.append(tmp_odp[:-3] + 'ppt')
    linked_files.append(zip_file_str)

    if len(linked_files) == 0:
        return False

    email_set.add_smtp_email(gen_announcement_email(full_email, linked_files, num_images, ppt_content))
    return True

def check_dirs_new_files(samba_dir=settings.NETWORK_FILESERVER_ROOT):
    os.chdir(samba_dir)
    email_dirs = os.walk(samba_dir).next()[1]
    improper_dirs = [e for e in email_dirs if len(e) > 0 and e[0] == '_']
    # get rid of subdirs beginning with '.' like '.ipython/'

    for d in improper_dirs:
        if d[0] == '_' and d.find('__') > 0:
            if files_modified_recently(d):
                continue
            emailaddr = d[1:d.find('__')]
            email_dir = os.path.join(samba_dir, emailaddr)
            ensure_path_exists(email_dir)
            run_command("""mv -t %s/ %r """ % (email_dir, str(d)))

    email_dirs = os.walk(samba_dir).next()[1]
    email_dirs = [e for e in email_dirs if len(e) > 0 and e[0] != '.' and e[0] != '_']
    email_dirs = filter(lambda d: not os.path.islink(d), email_dirs)
    # Make sure the fixed improper dirs are registered

    email_set = EmailSet()
    try:
        logging.debug("Opening Statistic Shelf")
        stat_shelf = shelve.open(os.path.join(settings.LOG_LOCATION, settings.SHLF_FILE))
    except:
        logging.error("Stastics shelf could not be opened.  Check file permissions.")
        stat_shelf = None
    try:
        for emailaddr in email_dirs:
            logging.debug("Current Email: %s" % emailaddr)
        check_dir_new_file(emailaddr, email_set, stat_shelf, samba_dir)
    except Exception as inst:
        logging.error("Exception: %r %r" % (type(inst), inst.args))
    finally:
        if stat_shelf:
            logging.debug("Closing Statistic Shelf")
            stat_shelf.close()
    if not settings.USE_ALTERNATE_SMTP_MAIL_SERVER:
        email_set.send_emails()
    else:
        email_set.alt_send_emails()

    ## Close unoconv listenner
    kill_soffice()


if __name__ == '__main__':
    logging.debug("Launching tfs_check.py %s" % time.ctime())
    check_dirs_new_files(settings.NETWORK_FILESERVER_ROOT)
    logging.debug("Ending tfs_check.py %s" % time.ctime())