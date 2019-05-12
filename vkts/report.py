#! /usr/bin/env python3

"""Module for creating and sending program performance report
in .txt and .html formats"""

from vkts.usrdata import UsrData
import time, os, smtplib, json
from email.mime.text import MIMEText
from email.header    import Header
# TODO: Сохранять текст сообщений email, которые не удалось отправить

class Report():
    def __init__(self, report_type, html_only=True):
        self.type = report_type
        self.short_name = time.strftime("%F-%H%M%S")
        self.name = 'reports/' + self.type + '/' + self.short_name + '.html'
        self.text = 'Report is saved in ' + self.name + '\n\n'
        self.html = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n' \
                    + '<Html>\n' \
                    + '<Head>\n' \
                    + '<Title>' + self.name + '</Title>\n' \
                    + '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n' \
                    + '</Head>\n' \
                    + '<Body topmargin="0" leftmargin="0" rightmargin="0" bottommargin="0" marginheight="0" marginwidth="0">\n'
        self.html_only = html_only
        self.empty = True

    def add_line(self, line):
        if not self.html_only:
            self.text += line + '\n'
        self.html += line + '<br>' + '\n'
        self.empty = False

    def add_str(self, s):
        if not self.html_only:
            self.text += s
        self.html += s
        self.empty = False

    def add_vk_link(self, addr, name):
        if not self.html_only:
            self.text += '[https://vk.com/' + addr + '] ' + name + '\n'
        self.html += '<a href=https://vk.com/' + addr + '>' + name + '</a><br>' + '\n'
        self.empty = False

    def conclude(self):
        self.html += '</Body>\n</Html>\n'

    def broadcast(self):

        # Get account data
        _, ac_obj = UsrData().get_active_obj('acc', 'email')
        sender, pswd = ac_obj['uname'], ac_obj['password']

        # Read emails of recipients
        recipients = UsrData().get('adm', 'bc_emails')
        if not recipients:
            print('No monitoring groups (try command monitor_add)')
            sys.exit()

        # Create message
        msg = MIMEText(self.text, 'plain', 'utf-8')
        msg['Subject'] = Header('Report ' + self.short_name, 'utf-8')
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        s = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        #s.set_debuglevel(1)
        try:
            s.starttls()
            s.login(sender, pswd)
            s.sendmail(msg['From'], recipients, msg.as_string())
        finally:
            #print(msg)
            s.quit()

    def dump(self):
        print(self.text)
        if not os.path.isdir('reports/'):
            os.mkdir('reports/')
        if not os.path.isdir('reports/' + self.type):
            os.mkdir('reports/' + self.type)
        with open(self.name, 'w') as f:
            f.write(self.html)

    def is_empty(self):
        return self.empty

