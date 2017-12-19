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
from subprocess import check_output

from mycroft import MycroftSkill, intent_file_handler
from mycroft.api import DeviceApi


class SupportSkill(MycroftSkill):
    # TODO: Will need to read from config under KDE, etc.
    log_locations = ['/opt/mycroft/*.json', '/var/log/mycroft-*.log',
                     '/etc/mycroft/*.conf']

    # Service used to temporarilly hold the debugging data (linked to
    # via email)
    host = 'termbin.com'

    def __init__(self):
        MycroftSkill.__init__(self)

    def upload_and_create_url(self):
        # Send the various log and info files
        logs = " ".join(self.log_locations)
        # Upload to termbin.com using the nc (netcat) util
        return check_output('tail -vn +1 ' + logs + ' | nc ' + self.host +
                            ' 9999', shell=True).decode()

    def get_device_name(self):
        try:
            return DeviceApi().get()['name']
        except:
            self.log.exception('API Error')
            return ':error:'

    # "You're not working!"
    @intent_file_handler('maybe.troubleshoot.intent')
    def maybe_troubleshoot(self):
        should_troubleshoot = self.get_response('ask.troubleshoot')
        yes_words = self.translate_list('yes')

        # TODO: .strip() shouldn't be needed, translate_list should remove
        #       the '\r' I'm seeing.  Remove after bugfix.
        if (should_troubleshoot and
                any(i.strip() in should_troubleshoot for i in yes_words)):
            self.troubleshoot()
        else:
            self.speak_dialog('cancelled')

    # "Create a support ticket"
    @intent_file_handler('troubleshoot.intent')
    def troubleshoot(self):
        # Get a problem description from the user
        description = self.get_response('ask.description')
        if description is None:
            self.speak_dialog('cancelled')
            return

        # Log so that the message will appear in the package of logs sent
        self.log.debug("Troubleshooting Package Description: "+str(description))
        
        # Upload the logs to the web
        url = self.upload_and_create_url()

        # Create the troubleshooting email and send to user
        data = {'url': url, 'device_name': self.get_device_name(),
                'description': description}
        email = '\n'.join(self.translate_template('support.email', data))
        title = self.translate('support.title')
        self.send_email(title, email)

        self.speak_dialog('troubleshoot')

    # "Email me debug info"
    @intent_file_handler('send.debug.info.intent')
    def send_debug_info(self):
        # Upload the logs to the web
        url = self.upload_and_create_url()

        # Create the debug email and send to user
        data = {'url': url, 'device_name': self.get_device_name()}
        email = '\n'.join(self.translate_template('debug.email', data))
        title = self.translate('debug.title')
        self.send_email(title, email)

        token = (url.replace('http://', '').replace(self.host, '').strip('/').
                    .strip(u"\u0000").strip())
        verbal_str = (self.host.replace('.', ' dot ') +
                      ' slash ' +
                      ', '.join(token))
        self.speak_dialog('uploaded', {'url': verbal_str})


def create_skill():
    return SupportSkill()
