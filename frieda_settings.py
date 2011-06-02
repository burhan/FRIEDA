#!/usr/bin/python

import os

## FRIEDA - File Server Settings


## NETWORK_FILESERVER_ROOT is the location where files are saved
NETWORK_FILESERVER_ROOT = '/home/samba_user/'

## SKIPPED DIRS is a python list of directories to skip processing Directories from the NETWORK_FILESERVER_ROOT
## E.g., if you had sub-directory of NETWORK_FILESERVER_ROOT say: 'dir_to_skip/' you would want to use
## SKIPPED_DIRS = ['dir_to_skip']
SKIPPED_DIRS = []

## This is the root of location of files on the webserver.  (Where FRIEDA moves the files after processing).
WEB_ROOT_DIR = '/home/webdata/data/'
## This is the corresponding root location of the files on the webserver.
WEB_ROOT_URL = 'http://localhost/data/'

## On the webserver the subdirectories where ZIP_DIR, TMP_DIR, and ODP_DIR
## where the temporary files, zip files, and odp files are stored.
ZIP_DIR = 'zips'
TMP_DIR = 'tmp'
ODP_DIR = 'odp'

## LOG_LOCATION is where the log files are stored.
## LOG_FILE is name of log file of logged messages
## LOG_LEVEL is a number representing the level of messages to be stored.
## Lower numbers will increase number of messages logged.
## NOTSET=0; DEBUG=10; INFO=20; WARN=30; ERROR=40; FATAL=50

LOG_LOCATION = '/var/log/tfs'
LOG_FILE = 'frieda.log'
LOG_LEVEL = 10 # DEBUG
LOG_FILENAME = os.path.join(LOG_LOCATION, LOG_FILE)
# SHLF_FILE Stores statistics
SHLF_FILE = 'frieda_stats.shlf'

## Some arbitrary string used as a SALT for the MD5 of the email address
## It is strongly suggested that you alter this string deploying.
HASHSALT = '1a2stjsr374i2tj32h7j8k9l0;'
#
HASHLENGTH = 20

# DELAY_TIME_SEC
DELAY_TIME_SEC = 300


SEND_EMAILS = True
DEFAULT_FROMADDR = 'yourusername@example.org'

## EMAIL_SUBJECT recognizes the following special variables: {num_images}, {email}
EMAIL_SUBJECT = "{num_images} new images in ppt/zip on Radiology Teaching File Server (FRIEDA)"

## EMAIL_BODY recognizes the following special variables
## {num_images}, {email}, {slide_contents} (list of directory listing)
## {file_links} (links to the actual files) {browse_files_url}
EMAIL_BODY = ("""
<p>The following files are available on the teaching file server.</p>
{file_links}
{slide_contents}
<small><p>To browse your files on the teaching file server go to:</p><p><a href='{browse_files_url}'>{browse_files_url}</a></p>
<p>N.B.: The radiology teaching file server is accessible on the college/hospital intranet only.</p>
</small>""")
## FILE_LINKS_FORMAT is how each of the links to the listed files will show up.
## {linked_file_url}, {email},{linked_file_name} are fields.
FILE_LINKS_FORMAT = "<p><a href='{linked_file_url}'>{linked_file_url}</a></p>"

#USE_ALTERNATE_SMTP_MAIL_SERVER = False
## Uncomment the following lines if you use the alternate server and set to your smtp servers settings

USE_ALTERNATE_SMTP_MAIL_SERVER = True
ALTERNATE_SMTP_SERVER = 'smtp.gmail.com'
ALTERNATE_SMTP_PORT = 587
LOGIN_REQUIRED = True
TLS_REQUIRED = True
LOGIN_NAME = 'FRIEDAradteaching@gmail.com'
LOGIN_PASSWORD = 'TFSfreedom'# Some GMAIL PASSWORD

if __name__ == '__main__':
    # Try creating directories
    from frieda_file_check import run_command
    for location in (NETWORK_FILESERVER_ROOT, WEB_ROOT_DIR, LOG_LOCATION):
        run_command('sudo mkdir -p %s' % location)
    run_command('sudo chgrp www-data %s' % LOG_LOCATION)
    run_command('sudo chmod 02775 %s' % LOG_LOCATION)
