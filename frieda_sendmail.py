#!/usr/bin/python

import frieda_settings as settings

import smtplib
import logging
import time
import commands
import os


if __name__ == '__main__':
    LOG_FILENAME = os.path.join(settings.LOG_LOCATION, settings.LOG_FILE)
    logging.basicConfig(filename=LOG_FILENAME, level=setttings.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s: %(message)s")
    raiseExceptions = False


def is_valid_email(email_str):
    try:
        from django.core.validators import email_re
        return email_re.match(email_str)
    except ImportError:
        logging.warning("Django not installed; email validation not performed")
        return True

class SMTPEmail(object):
    def __init__(self, recipients=None, subject="",
                 body="", fromaddr=settings.DEFAULT_FROMADDR,
                 html_email=True):
        '''pass recipients as a list of string email addresses, then subj, then body'''
        if recipients == None:
            recipients = []
        if (type(recipients) == str):
            recipients = [recipients]
        self.recipients = recipients
        self.html_email = html_email
        self.to_part = ""
        self.toaddr = ""
        for toaddr in recipients:
            self.to_part += "To: %s\r\n" % (toaddr)
            self.toaddr = toaddr
        self.fromaddr = fromaddr
        self.subject = "Subject: %s\r\n\r\n" % (str(subject))
        self.orig_subject =subject
        self.body = body

    def set_body(self, body=""):
        self.body = body

    def prepend_body(self, body_prepend=""):
        self.body = body_prepend + "\n" + self.body

    def append_body(self, body_append=""):
        self.body = self.body + "\n" + body_append

    def set_subject(self, subject=""):
        if subject[0:9] == "Subject: ":
            subject = subject[9:]
        self.subject = "Subject: %s\r\n\r\n" % subject
        self.orig_subject =subject

    def add_recipients(self, recipients=None):
        if recipients == None:
            pass
        elif (type(recipients) == str):
            recipients = [recipients,]

        for r in recipients:
            if is_valid_email(r):
                self.to_part += "To: %s\r\n" % (r,)
                self.recipients.append(r)
                self.toaddr = r
    def msg_str(self):
        if self.html_email:
            html_str = ("MIME-Version: 1.0\n"
                        'Content-Type: text/html; charset = "iso-8859-1"\n'
                        'Content-Tranfer-Encoding: quoted-printable\n')
            return self.to_part + html_str + self.subject + self.body
        else:
            return self.to_part  + self.subject + self.body

    def print_email(self,):
        logging.debug("print_email():\n%r" %self.msg_str())
        print self.msg_str()

    def __repr__(self, ):
        return self.msg_str()


class EmailSet(object):
    def __init__(self):
        self.email_set = []
        self.verbose = True

    def cur_email(self):
        if len(self.email_set) > 0:
            return self.email_set[-1]
        else:
            return None

    def add_email_by_args(self, *args,**kw_args):
        self.email_set.append(SMTPEmail(*args, **kw_args))

    def add_smtp_email(self, email):
        if type(email)==SMTPEmail:
            self.email_set.append(email)
        else:
            raise TypeError("Email to append to EmailSet not a SMTPEmail")

    def send_emails(self):
        if len(self.email_set) == 0:
            logging.debug("No emails to send")
            return True
        else:
            for email in self.email_set:
                logging.info("Sending email to %r" % email.recipients)
                logging.debug(" ")
                logging.debug("""echo "%s" | mail %s -s "%s" -a "MIME-Version: 1.0" -a "Content-Type: text/html; charset = iso-8859-1" -a "Content-Transfer-Encoding" """ % (
                        email.body, email.toaddr, email.orig_subject))
                logging.debug(" ")
                statusoutput = commands.getstatusoutput("""echo "%s" | mail %s -s "%s" -a "MIME-Version: 1.0" -a "Content-Type: text/html; charset = iso-8859-1" -a "Content-Transfer-Encoding" -a "From: %s" """ % (
                        email.body, email.toaddr, email.orig_subject, email.fromaddr))
                if statusoutput[0] == 0:
                    logging.info("Sent email to %r" % email.recipients)
                else:
                    logging.error("Didn't send? %r" % statusoutput)
                

    def alt_initialize_server(self):
        try:
            logging.debug("Connecting to server")
            self.server = smtplib.SMTP(settings.ALTERNATE_SMTP_SERVER, settings.ALTERNATE_SMTP_PORT)
            
            logging.debug("Connected to server")
            self.server.set_debuglevel(self.verbose)
            if hasattr(settings, 'TLS_REQUIRED') and settings.TLS_REQUIRED:
                self.server.starttls()
            self.server.ehlo()
            if hasattr(settings, 'LOGIN_NAME') and hasattr(settings, 'LOGIN_PASSWORD'):
                self.server.login(settings.LOGIN_NAME, settings.LOGIN_PASSWORD)
        except Exception as inst:
            logging.error("Initialization failed: %r" % inst)

    def alt_send_one_email(self, email):
        try:
            logging.debug("Sending email to %r" % email.recipients)
            response_dict = self.server.sendmail(email.fromaddr, email.recipients, email.msg_str())
            logging.info("Sent email to %r" % email.recipients)
            if self.verbose:
                email.print_email()
            return True
        except:
            logging.error("Email sending failed")
            return False

    def alt_reset_server(self):
        try:
            self.server.rset()
            self.server.quit()
        except:
            logging.error("Resetting and quitting server Failed")
        finally:
            self.alt_initialize_server()

    def alt_send_emails(self):
        if len(self.email_set) == 0:
            logging.debug("No emails to send")
            return True
        try:
            self.alt_initialize_server()
            for email in self.email_set:
                sent = self.alt_send_one_email(email)
                if not sent:
                    time.sleep(15)
                    self.alt_reset_server()
                    time.sleep(15)
                    logging.debug("Second Attempt")
                    sent = self.alt_send_one_email(email)
                    if not sent:
                        time.sleep(15)
                        self.alt_reset_server()
                        time.sleep(15)
                        logging.debug("Third Attempt")
                        sent = self.alt_send_one_email(email)
                        if not sent:
                            logging.error("Email Sending Failed on Three Attempts")
                            logging.error("From: %s, Recipients: %r" % (email.fromaddr, email.recipients))
                            logging.error("%s" % email.msg_str() )
                            logging.error("%r" % ( type(inst) ) )

        except Exception as inst:
            logging.error("%r" % inst)
        finally:
            logging.debug("Reseting and Quitting Server")
            self.server.rset()
            self.server.quit()
            logging.debug("Successfully Quit Server")
        return True
