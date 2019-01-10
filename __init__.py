# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from glob import glob
from subprocess import check_output
from tempfile import mkstemp
from threading import Thread

import os
from os.path import dirname, join

import mycroft
from mycroft import MycroftSkill, intent_file_handler
from mycroft.api import DeviceApi


class SupportSkill(MycroftSkill):
    # TODO: Will need to read from config under KDE, etc.
    log_locations = [
        '/opt/mycroft/*.json',
        '/var/log/mycroft/*.log',
        '/etc/mycroft/*.conf',
        join(dirname(dirname(mycroft.__file__)), 'scripts', 'logs', '*.log')
    ]

    # Service used to temporarilly hold the debugging data (linked to
    # via email)
    host = 'termbin.com'

    def __init__(self):
        MycroftSkill.__init__(self)

    def upload_and_create_url(self, log_str):
        # Send the various log and info files
        # Upload to termbin.com using the nc (netcat) util
        fd, path = mkstemp()
        with open(path, 'w') as f:
            f.write(log_str)
        os.close(fd)
        cmd = 'cat ' + path + ' | nc ' + self.host + ' 9999'
        return check_output(cmd, shell=True).decode().strip('\n\x00')

    def get_device_name(self):
        try:
            return DeviceApi().get()['name']
        except:
            self.log.exception('API Error')
            return ':error:'

    def upload_debug_info(self):
        all_lines = []
        threads = []
        for log_file in sum([glob(pattern) for pattern in self.log_locations], []):
            def do_thing(log_file=log_file):
                with open(log_file) as f:
                    log_lines = f.read().split('\n')
                lines = ['=== ' + log_file + ' ===']
                if len(log_lines) > 100:
                    log_lines = '\n'.join(log_lines[-5000:])
                    print('Uploading ' + log_file + '...')
                    lines.append(self.upload_and_create_url(log_lines))
                else:
                    lines.extend(log_lines)
                lines.append('')
                all_lines.extend(lines)

            t = Thread(target=do_thing)
            t.daemon = True
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        return self.upload_and_create_url('\n'.join(all_lines))

    # "Create a support ticket"
    @intent_file_handler('contact.support.intent')
    def troubleshoot(self):
        # Get a problem description from the user
        user_words = self.get_response('confirm.support', num_retries=0)

        yes_words = self.translate_list('yes')

        # TODO: .strip() shouldn't be needed, translate_list should remove
        #       the '\r' I'm seeing.  Remove after bugfix.
        if (not user_words or not any(
                i.strip() in user_words for i in yes_words
        )):
            self.speak_dialog('cancelled')
            return

        description = self.get_response('ask.description', num_retries=0)
        if description is None:
            self.speak_dialog('cancelled')
            return

        self.speak_dialog('one.moment')

        # Log so that the message will appear in the package of logs sent
        self.log.debug("Troubleshooting Package Description: " +
                       str(description))

        # Upload the logs to the web
        url = self.upload_debug_info()

        # Create the troubleshooting email and send to user
        data = {'url': url, 'device_name': self.get_device_name(),
                'description': description}
        email = '\n'.join(self.translate_template('support.email', data))
        title = self.translate('support.title')
        self.send_email(title, email)
        self.speak_dialog('complete')


def create_skill():
    return SupportSkill()
