#!/usr/bin/python

import frieda_settings as settings

import smtplib
import logging
import time
import commands

from django.core.validators import email_re

if __name__ == '__main__':
    LOG_FILENAME = '/var/log/tfs/email.log'
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    raiseExceptions = False


def is_valid_email(email_str):
    return email_re.match(email_str)


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

    def alt_send_emails(self):
        if len(self.email_set) == 0:
            logging.debug("No emails to send")
            return True
        else:
            logging.debug("Connecting to server")
            try:
                server = smtplib.SMTP(settings.ALTERNATE_SMTP_SERVER, settings.ALTERNATE_SMTP_PORT)
                logging.debug("Connected to server")
                server.set_debuglevel(self.verbose)
                server.ehlo()
                for email in self.email_set:
                    try:
                        logging.debug("Sending email to %r" % email.recipients)
                        response_dict = server.sendmail(email.fromaddr, email.recipients, email.msg_str())
                        try:
                            logging.debug('%r' % response_dict)
                        except:
                            pass
                        logging.info("Sent email to %r" % email.recipients)
                        if self.verbose:
                            email.print_email()
                    except Exception as inst:
                        try:
                            logging.error('RD: %r' % response_dict)
                        except:
                            pass
                        logging.error("Email Sending Failed")
                        logging.error("From: %s, Recipients: %r" % (email.fromaddr, email.recipients))
                        logging.error("%s" % email.msg_str() )
                        logging.error("%r" % ( type(inst) ) )
                        try:
                            logging.error("%s" % inst)
                        except:
                            pass
                        try:
                            logging.info("Second Attempt to send to %r" % email.recipients)
                            try:
                                server.rset()
                            except:
                                pass
                            try:
                                server.quit()
                            except:
                                pass
                            time.sleep(15)
                            server2 = smtplib.SMTP(settings.ALTERNATE_SMTP_SERVER, settings.ALTERNATE_SMTP_PORT)
                            server2.set_debuglevel(self.verbose)
                            server2.ehlo()
                            logging.info("Sending ... to %r" % email.recipients)
                            response_dict = server2.sendmail(email.fromaddr, email.recipients, email.msg_str())
                            logging.info("Sent email to %r (2nd Attempt)" % email.recipients)
                        except Exception as inst:
                            try:
                                logging.error('RD: %r' % response_dict)
                            except:
                                pass
                            logging.error("Second Attempt Email Sending Failed")
                            logging.error("From: %s, Recipients: %r" % (email.fromaddr, email.recipients))
                            logging.error("%s" % email.msg_str() )
                            logging.error("%r" % ( type(inst) ) )
                            try:
                                logging.error("%s" % inst)
                            except:
                                pass
                            try:
                                logging.info("Third Attempt to send to %r" % email.recipients)
                                try:
                                    server2.rset()
                                    server2.quit()
                                except:
                                    pass
                                time.sleep(75)
                                server3 = smtplib.SMTP(settings.ALTERNATE_SMTP_SERVER, settings.ALTERNATE_SMTP_PORT)
                                server3.set_debuglevel(self.verbose)
                                server3.ehlo()
                                logging.info("Sending ... to %r" % email.recipients)
                                response_dict = server.sendmail(email.fromaddr, email.recipients, email.msg_str())
                                logging.info("Sent email to %r (3rd Attempt)" % email.recipients)
                            except Exception as inst:
                                try:
                                    logging.error('RD: %r' % response_dict)
                                except:
                                    pass
                                logging.error("Email Sending Failed")
                                logging.error("From: %s, Recipients: %r" % (email.fromaddr, email.recipients))
                                logging.error("%s" % email.msg_str() )
                                logging.error("%r" % ( type(inst) ) )
                                try:
                                    logging.error("%s" % inst)
                                except:
                                    pass

            except:
                logging.debug("Can't connect to server")
            finally:
                logging.debug("Reseting and Quitting Server")
                server.rset()
                server.quit()
                logging.debug("Successfully Quit Server")
            return True
