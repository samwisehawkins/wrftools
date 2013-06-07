#
# Modified by Sam Hawkins from the original by Vinay Sajip
#
# Copyright 2001-2002 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# This file is part of the Python logging distribution. See
# http://www.red-dove.com/python_logging.html
#
"""Test harness for the logging module. Tests BufferingSMTPHandler, an alternative implementation
of SMTPHandler.
 
Copyright (C) 2001-2002 Vinay Sajip. All Rights Reserved.
"""
import string, logging, logging.handlers
from subprocess import Popen, PIPE
from email.mime.text import MIMEText

TO       = ['sam.hawkins@vattenfall.com']
SUBJECT  = 'Test Logging email from Python logging module (buffering)'
SENDMAIL = "/usr/sbin/sendmail"
 
class BufferingSendmailHandler(logging.handlers.BufferingHandler):

    def __init__(self, toaddrs, subject, capacity):
        logging.handlers.BufferingHandler.__init__(self, capacity)
        self.toaddrs = toaddrs
        self.subject = subject
        #self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
        
    def flush(self):
        if len(self.buffer) > 0:
            #try:
            records = map(self.format, self.buffer)
            body    = "\n".join(records)
            
            msg = MIMEText(body)
            msg['Subject'] = self.subject
            msg['From']    = 'slha@hydra.vattenfall.se'
            msg['To']      = self.toaddrs
            
            p = Popen([SENDMAIL, "-t"],bufsize=0, stdin=PIPE)
            p.communicate(msg.as_string())
            
            #except:
            #    print "error during email logging"
        self.buffer = []


def test():
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(BufferingSendmailHandler(TO, "new test", 50))
    for i in xrange(10):
        logger.info("New Info index = %d", i)
    #logging.shutdown()
 
if __name__ == "__main__":
    test()
