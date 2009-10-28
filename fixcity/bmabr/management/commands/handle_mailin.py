# based on email2trac.py, which is Copyright (C) 2002 under the GPL v2 or later

from datetime import datetime
from optparse import make_option
from stat import S_IRWXU, S_IRWXG, S_IRWXO
import email.Header
import mimetypes
import os
import re
import string
import sys
import traceback
import unicodedata

from django.contrib.auth.models import User
from django.contrib.gis.geos.point import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from fixcity.bmabr import models
from fixcity.bmabr import views


class EmailParser(object):
    env = None
    comment = '> '
    msg = None
    
    def __init__(self, parameters):

        # Save parameters
        #
        self.parameters = parameters

        # Some useful mail constants
        #
        self.author = None
        self.email_addr = None
        self.email_from = None
        self.id = None

        # XXX Cull stuff that just stores a value, we should just
        # store all the parameters instead.
        self.DRY_RUN = parameters['dry_run']

        if parameters.has_key('umask'):
            os.umask(int(parameters['umask'], 8))

        if parameters.has_key('debug'):
            self.DEBUG = int(parameters['debug'])
        else:
            self.DEBUG = 0

        if parameters.has_key('spam_level'):
            self.SPAM_LEVEL = int(parameters['spam_level'])
        else:
            self.SPAM_LEVEL = 0

        if parameters.has_key('spam_header'):
            self.SPAM_HEADER = parameters['spam_header']
        else:
            self.SPAM_HEADER = 'X-Spam-Score'

        if parameters.has_key('email_quote'):
            self.EMAIL_QUOTE = str(parameters['email_quote'])
        else:
            self.EMAIL_QUOTE = '> '

        if parameters.has_key('email_header'):
            self.EMAIL_HEADER = int(parameters['email_header'])
        else:
            self.EMAIL_HEADER = 0

        if parameters.has_key('reply_all'):
            self.REPLY_ALL = int(parameters['reply_all'])
        else:
            self.REPLY_ALL = 0

        if parameters.has_key('rack_update'):
            self.RACK_UPDATE = int(parameters['rack_update'])
        else:
            self.RACK_UPDATE = 0

        if parameters.has_key('drop_spam'):
            self.DROP_SPAM = int(parameters['drop_spam'])
        else:
            self.DROP_SPAM = 0

        if parameters.has_key('drop_alternative_html_version'):
            self.DROP_ALTERNATIVE_HTML_VERSION = int(parameters['drop_alternative_html_version'])
        else:
            self.DROP_ALTERNATIVE_HTML_VERSION = 0

        if parameters.has_key('strip_signature'):
            self.STRIP_SIGNATURE = int(parameters['strip_signature'])
        else:
            self.STRIP_SIGNATURE = 0

        if parameters.has_key('strip_quotes'):
            self.STRIP_QUOTES = int(parameters['strip_quotes'])
        else:
            self.STRIP_QUOTES = 0

        if parameters.has_key('binhex'):
            self.BINHEX = parameters['binhex']
        else:
            self.BINHEX = 'warn'

        if parameters.has_key('applesingle'):
            self.APPLESINGLE = parameters['applesingle']
        else:
            self.APPLESINGLE = 'warn'

        if parameters.has_key('appledouble'):
            self.APPLEDOUBLE = parameters['appledouble']
        else:
            self.APPLEDOUBLE = 'warn'

        if parameters.has_key('python_egg_cache'):
            self.python_egg_cache = str(parameters['python_egg_cache'])
            os.environ['PYTHON_EGG_CACHE'] = self.python_egg_cache

        # Use OS independend functions
        #
        self.TMPDIR = os.path.normcase('/tmp')
        if parameters.has_key('tmpdir'):
            self.TMPDIR = os.path.normcase(str(parameters['tmpdir']))


        self.MAX_ATTACHMENT_SIZE = int(parameters.get('max-attachment-size', -1))

    def spam(self, message):
        """
        # X-Spam-Score: *** (3.255) BAYES_50,DNS_FROM_AHBL_RHSBL,HTML_
        # Note if Spam_level then '*' are included
        """
        spam = False
        if message.has_key(self.SPAM_HEADER):
            spam_l = string.split(message[self.SPAM_HEADER])

            try:
                number = spam_l[0].count('*')
            except IndexError, detail:
                number = 0

            if number >= self.SPAM_LEVEL:
                spam = True

        # treat virus mails as spam
        #
        elif message.has_key('X-Virus-found'):
            spam = True

        # How to handle SPAM messages
        #
        if self.DROP_SPAM and spam:
            if self.DEBUG > 2 :
                print 'This message is a SPAM. Automatic rack insertion refused (SPAM level > %d' % self.SPAM_LEVEL

            return 'drop'

        elif spam:

            return 'Spam'

        else:

            return False

    def email_header_acl(self, keyword, header_field, default):
        """
        This function wil check if the email address is allowed or denied
        to send mail to the rack list
    """
        try:
            mail_addresses = self.parameters[keyword]

            # Check if we have an empty string
            #
            if not mail_addresses:
                return default

        except KeyError, detail:
            if self.DEBUG > 2 :
                print 'TD: %s not defined, all messages are allowed.' %(keyword)

            return default

        mail_addresses = string.split(mail_addresses, ',')

        for entry in mail_addresses:
            entry = entry.strip()
            TO_RE = re.compile(entry, re.VERBOSE|re.IGNORECASE)
            result =  TO_RE.search(header_field)
            if result:
                return True

        return False

    def email_to_unicode(self, message_str):
        """
        Email has 7 bit ASCII code, convert it to unicode with the charset
that is encoded in 7-bit ASCII code and encode it as utf-8.
        """
        results =  email.Header.decode_header(message_str)
        str = None
        for text,format in results:
            if format:
                try:
                    temp = unicode(text, format)
                except UnicodeError, detail:
                    # This always works
                    #
                    temp = unicode(text, 'iso-8859-15')
                except LookupError, detail:
                    #text = 'ERROR: Could not find charset: %s, please install' %format
                    #temp = unicode(text, 'iso-8859-15')
                    temp = message_str

            else:
                temp = string.strip(text)
                temp = unicode(text, 'iso-8859-15')

            if str:
                str = '%s %s' %(str, temp)
            else:
                str = '%s' %temp

        #str = str.encode('utf-8')
        return str

    def debug_body(self, message_body, tempfile=False):
        if tempfile:
            import tempfile
            body_file = tempfile.mktemp('.handle_mailin')
        else:
            body_file = os.path.join(self.TMPDIR, 'body.txt')

        print 'TD: writing body (%s)' % body_file
        fx = open(body_file, 'wb')
        if not message_body:
            message_body = '(None)'

        message_body = message_body.encode('utf-8')
        #message_body = unicode(message_body, 'iso-8859-15')

        fx.write(message_body)
        fx.close()
        try:
            os.chmod(body_file,S_IRWXU|S_IRWXG|S_IRWXO)
        except OSError:
            pass

    def debug_attachments(self, message_parts):
        n = 0
        for part in message_parts:
            # Skip inline text parts
            if not isinstance(part, tuple):
                continue

            (original, filename, part) = part

            n = n + 1
            print 'TD: part%d: Content-Type: %s' % (n, part.get_content_type())
            print 'TD: part%d: filename: %s' % (n, part.get_filename())

            part_file = os.path.join(self.TMPDIR, filename)
            #part_file = '/var/tmp/part%d' % n
            print 'TD: writing part%d (%s)' % (n,part_file)
            fx = open(part_file, 'wb')
            text = part.get_payload(decode=1)
            if not text:
                text = '(None)'
            fx.write(text)
            fx.close()
            try:
                os.chmod(part_file,S_IRWXU|S_IRWXG|S_IRWXO)
            except OSError:
                pass


    def get_sender_info(self):
        """
        Get the default author name and email address from the message
        """
        message = self.msg
        self.email_to = self.email_to_unicode(message['to'])
        self.to_name, self.to_email_addr = email.Utils.parseaddr (self.email_to)

        self.email_from = self.email_to_unicode(message['from'])
        self.author, self.email_addr  = email.Utils.parseaddr(self.email_from)

        # Trac can not handle author's name that contains spaces
        # XXX do we care about author's name for fixcity? prob not.
        self.author = self.email_addr



    def save_email_for_debug(self, message, tempfile=False):
        if tempfile:
            import tempfile
            msg_file = tempfile.mktemp('.email2trac')
        else:
            #msg_file = '/var/tmp/msg.txt'
            msg_file = os.path.join(self.TMPDIR, 'msg.txt')

        print 'TD: saving email to %s' % msg_file
        fx = open(msg_file, 'wb')
        fx.write('%s' % message)
        fx.close()
        try:
            os.chmod(msg_file,S_IRWXU|S_IRWXG|S_IRWXO)
        except OSError:
            pass


    def new_rack(self, title, address, spam):
        """
        Create a new rack
        """
        msg = self.msg
        if self.DEBUG:
            print "TD: new_rack"

        message_parts = self.get_message_parts()
        message_parts = self.unique_attachment_names(message_parts)

        # XXX handle multiple location results
        try:
            lat, lon = views._geocode(address)[0][1]
        except IndexError:
            raise ValueError("Could not geocode address %r" % address)
        point = str(Point(lon, lat, srid=views.SRID))
        communityboard = views._get_communityboard_id(lon, lat)
        
        description = self.body_text(message_parts)
        attachments = self.attachments(message_parts)
            
        data = dict(title=title,
                    description=description,
                    date=datetime.now(),
                    location=point,
                    address=address,
                    communityboard=communityboard,
                    email=self.email_addr)

        users = User.objects.filter(email=self.email_addr).all()
        if len(users) == 1:
            data['user'] = users[0].username
        else:
            # No user with that email address; or too many.
            pass

        rackform = models.RackForm(data, attachments)

        if rackform.is_valid():
            if self.DRY_RUN and self.DEBUG:
                print "TD: would save rack here"
            else:
                rack = rackform.save()
                self.id = rack.id
        elif rackform.errors and self.DEBUG:
            print "TD: errors %s" % rackform.errors



    def parse(self, fp):
        self.msg = email.message_from_file(fp)
        if not self.msg:
            if self.DEBUG:
                print "TD: This is not a valid email message format"
            return

        # Work around lack of header folding in Python; see http://bugs.python.org/issue4696
        self.msg.replace_header('Subject', self.msg['Subject'].replace('\r', '').replace('\n', ''))

        if self.DEBUG > 1:        # save the entire e-mail message text
            message_parts = self.get_message_parts()
            message_parts = self.unique_attachment_names(message_parts)
            self.save_email_for_debug(self.msg, True)
            body_text = self.body_text(message_parts)
            self.debug_body(body_text, True)
            self.debug_attachments(message_parts)

        self.get_sender_info()

        if not self.email_header_acl('white_list', self.email_addr, True):
            if self.DEBUG > 1 :
                print 'Message rejected : %s not in white list' %(self.email_addr)
            return False

        if self.email_header_acl('black_list', self.email_addr, False):
            if self.DEBUG > 1 :
                print 'Message rejected : %s in black list' %(self.email_addr)
            return False

        if not self.email_header_acl('recipient_list', self.to_email_addr, True):
            if self.DEBUG > 1 :
                print 'Message rejected : %s not in recipient list' %(self.to_email_addr)
            return False

        # If drop the message
        #
        if self.spam(self.msg) == 'drop':
            return False

        elif self.spam(self.msg) == 'spam':
            spam_msg = True
        else:
            spam_msg = False

        if not self.msg['Subject']:
            return False
        else:
            subject  = self.email_to_unicode(self.msg['Subject'])


        subject_re = re.compile(r'(?P<title>[^\@]*)\s+(?P<address>@.*)')
        subject_match = subject_re.search(subject)
        if subject_match:
            title = subject_match.group('title').strip()
            address = subject_match.group('address').lstrip('@').strip()
            self.new_rack(title, address, spam_msg)
        else:
            raise ValueError(
                "Could not parse title and location from subject %r" % subject)


    def strip_signature(self, text):
        """
        Strip signature from message, inspired by Mailman software
        """
        body = []
        for line in text.splitlines():
            if line == '-- ':
                break
            body.append(line)

        return ('\n'.join(body))

    def strip_quotes(self, text):
        """
        Strip quotes from message by Nicolas Mendoza
        """
        body = []
        for line in text.splitlines():
            if line.startswith(self.EMAIL_QUOTE):
                continue
            body.append(line)

        return ('\n'.join(body))


    def get_message_parts(self):
        """
        parses the email message and returns a list of body parts and attachments
        body parts are returned as strings, attachments are returned as tuples of (filename, Message object)
        """
        msg = self.msg
        message_parts = []

        # This is used to figure out when we are inside an AppleDouble container
        # AppleDouble containers consists of two parts: Mac-specific file data, and platform-independent data
        # We strip away Mac-specific stuff
        appledouble_parts = []

        ALTERNATIVE_MULTIPART = False

        for part in msg.walk():
            if self.DEBUG:
                print 'TD: Message part: Main-Type: %s' % part.get_content_maintype()
                print 'TD: Message part: Content-Type: %s' % part.get_content_type()


            # Check whether we just finished processing an AppleDouble container
            if part not in appledouble_parts:
                appledouble_parts = []

            ## Check content type
            #
            if part.get_content_type() == 'application/mac-binhex40':
                #
                # Special handling for BinHex attachments. Options are drop (leave out with no warning), warn (and leave out), and keep
                #
                if self.BINHEX == 'warn':
                    message_parts.append("'''A BinHex attachment named '%s' was ignored (use MIME encoding instead).'''" % part.get_filename())
                    continue
                elif self.BINHEX == 'drop':
                    continue

            elif part.get_content_type() == 'application/applefile':
                #
                # Special handling for the Mac-specific part of AppleDouble/AppleSingle attachments. Options are strip (leave out with no warning), warn (and leave out), and keep
                #

                if part in appledouble_parts:
                    if self.APPLEDOUBLE == 'warn':
                        message_parts.append("'''The resource fork of an attachment named '%s' was removed.'''" % part.get_filename())
                        continue
                    elif self.APPLEDOUBLE == 'strip':
                        continue
                else:
                    if self.APPLESINGLE == 'warn':
                        message_parts.append("'''An AppleSingle attachment named '%s' was ignored (use MIME encoding instead).'''" % part.get_filename())
                        continue
                    elif self.APPLESINGLE == 'drop':
                        continue

            elif part.get_content_type() == 'multipart/appledouble':
                #
                # If we entering an AppleDouble container, set up appledouble_parts so that we know what to do with its subparts
                #
                appledouble_parts = part.get_payload()
                continue

            elif part.get_content_type() == 'multipart/alternative':
                ALTERNATIVE_MULTIPART = True
                continue

            # Skip multipart containers
            #
            if part.get_content_maintype() == 'multipart':
                if self.DEBUG:
                    print "TD: Skipping multipart container"
                continue

            # Check if this is an inline part. It's inline if there is co Cont-Disp header, or if there is one and it says "inline"
            inline = self.inline_part(part)

            # Drop HTML message
            if ALTERNATIVE_MULTIPART and self.DROP_ALTERNATIVE_HTML_VERSION:
                if part.get_content_type() == 'text/html':
                    if self.DEBUG:
                        print "TD: Skipping alternative HTML message"

                    ALTERNATIVE_MULTIPART = False
                    continue

            # Inline text parts are where the body is
            if part.get_content_type() == 'text/plain' and inline:
                if self.DEBUG:
                    print 'TD:               Inline body part'

                # Try to decode, if fails then do not decode
                #
                body_text = part.get_payload(decode=1)
                if not body_text:
                    body_text = part.get_payload(decode=0)

                format = email.Utils.collapse_rfc2231_value(part.get_param('Format', 'fixed')).lower()
                delsp = email.Utils.collapse_rfc2231_value(part.get_param('DelSp', 'no')).lower()

                if self.STRIP_SIGNATURE:
                    body_text = self.strip_signature(body_text)

                if self.STRIP_QUOTES:
                    body_text = self.strip_quotes(body_text)

                # Get contents charset (iso-8859-15 if not defined in mail headers)
                #
                charset = part.get_content_charset()
                if not charset:
                    charset = 'iso-8859-15'

                try:
                    ubody_text = unicode(body_text, charset)

                except UnicodeError, detail:
                    ubody_text = unicode(body_text, 'iso-8859-15')

                except LookupError, detail:
                    ubody_text = 'ERROR: Could not find charset: %s, please install' %(charset)

                message_parts.append('%s' %ubody_text)
            else:
                if self.DEBUG:
                    print 'TD:               Filename: %s' % part.get_filename()

                message_parts.append((part.get_filename(), part))
        return message_parts

    def unique_attachment_names(self, message_parts):
        renamed_parts = []
        attachment_names = set()
        for part in message_parts:

            # If not an attachment, leave it alone
            if not isinstance(part, tuple):
                renamed_parts.append(part)
                continue

            (filename, part) = part
            # Decode the filename
            if filename:
                filename = self.email_to_unicode(filename)
            # If no name, use a default one
            else:
                filename = 'untitled-part'

                # Guess the extension from the content type, use non strict mode
                # some additional non-standard but commonly used MIME types
                # are also recognized
                #
                ext = mimetypes.guess_extension(part.get_content_type(), False)
                if not ext:
                    ext = '.bin'

                filename = '%s%s' % (filename, ext)

            # Discard relative paths in attachment names
            filename = filename.replace('\\', '/').replace(':', '/')
            filename = os.path.basename(filename)

            # We try to normalize the filename to utf-8 NFC if we can.
            # Files uploaded from OS X might be in NFD.
            # Check python version and then try it
            #
            if sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3):
                try:
                    filename = unicodedata.normalize('NFC', unicode(filename, 'utf-8')).encode('utf-8')
                except TypeError:
                    pass

            # Make the filename unique for this rack
            num = 0
            unique_filename = filename
            filename, ext = os.path.splitext(filename)

            while unique_filename in attachment_names:
                num += 1
                unique_filename = "%s-%s%s" % (filename, num, ext)

            if self.DEBUG:
                print 'TD: Attachment with filename %s will be saved as %s' % (filename, unique_filename)

            attachment_names.add(unique_filename)

            renamed_parts.append((filename, unique_filename, part))

        return renamed_parts

    def inline_part(self, part):
        return part.get_param('inline', None, 'Content-Disposition') == '' or not part.has_key('Content-Disposition')



    def body_text(self, message_parts):
        body_text = []

        for part in message_parts:
            # Plain text part, append it
            if not isinstance(part, tuple):
                body_text.extend(part.strip().splitlines())
                body_text.append("")
                continue

        body_text = '\r\n'.join(body_text)
        return body_text


    def attachments(self, message_parts):
        """save an attachment as a single photo
        """
        # Get Maxium attachment size
        #
        max_size = self.MAX_ATTACHMENT_SIZE
        status   = ''
        results = {}
        
        for part in message_parts:
            # Skip text body parts
            if not isinstance(part, tuple):
                continue

            (original, filename, part) = part
            text = part.get_payload(decode=1)
            if not text:
                continue
            file_size = len(text)

            # Check if the attachment size is allowed
            #
            if (max_size != -1) and (file_size > max_size):
                status = '%s\nFile %s is larger then allowed attachment size (%d > %d)\n\n' \
                        %(status, original, file_size, max_size)
                continue

            results[u'photo'] = SimpleUploadedFile.from_dict(
                {'filename': filename, 'content': text,
                 'content-type': 'image/jpeg'})
            # XXX what to do if there's more than one attachment?
            # we just ignore 'em.
            break
        return results




class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--dry-run', action="store_true",
                    help="Don't save any data.", dest="dry_run"),
        make_option('--debug', type="int", default=0,
                    help="Add some verbosity and save any problematic data."),
        make_option('--egg-cache', action="store", dest="python_egg_cache",
                    help="Cache for python eggs to make pkg_resources happy"),
        make_option('--strip-signature', action="store_true", default=True,
                    help="Remove signatures from incoming mail"),
        make_option('--max-attachment-size', type="int",
                    help="Max size of uploaded files."),

    )

    def handle(self, *args, **options):
        parser = EmailParser(options)
        did_stdin = False
        for filename in args:
            if filename == '-':
                if did_stdin:
                    continue
                thisfile = sys.stdin
                did_stdin = True
            else:
                thisfile = open(filename)
            try:
                parser.parse(thisfile)
            except Exception, error:
                traceback.print_exc()
                if parser.msg:
                    parser.save_email_for_debug(parser.msg, True)

                sys.exit(1)