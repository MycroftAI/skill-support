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

from tempfile import mkstemp

from mycroft import MycroftSkill, intent_handler

from .skill.audio_recorder import ThreadedRecorder
from .skill.debug_package import create_debug_package
from .skill.device_id import get_device_name
from .skill.upload import upload_debug_package


class SupportSkill(MycroftSkill):

    # "Create a support ticket"
    @intent_handler("contact.support.intent")
    def troubleshoot(self):
        # Get a problem description from the user
        user_words = self.get_response("confirm.support", num_retries=0)

        yes_words = self.translate_list("yes")

        # TODO: .strip() shouldn't be needed, translate_list should remove
        #       the '\r' I'm seeing.  Remove after bugfix.
        if not user_words or not any(i.strip() in user_words for i in yes_words):
            self.speak_dialog("cancelled")
            return

        sample_rate = self.config_core["listener"]["sample_rate"]
        recorder = ThreadedRecorder(rate=sample_rate)
        description = self.get_response("ask.description", num_retries=0)
        recorder.stop()

        if description is None:
            self.speak_dialog("cancelled")
            return

        _, audio_file = mkstemp(suffix=".wav")
        recorder.save(audio_file)

        self.speak_dialog("one.moment")

        # Log so that the message will appear in the package of logs sent
        self.log.debug("Troubleshooting Package Description: " + str(description))

        # Compile debug package
        debug_package = create_debug_package([audio_file])
        # Upload the logs to the web
        url = upload_debug_package(debug_package)
        if not url:
            self.speak_dialog("upload.failed")
            return  # Something failed creating package. More info in logs

        # Create the troubleshooting email and send to user
        data = {
            "url": url,
            "device_name": get_device_name(),
            "description": description,
        }
        email = "\n".join(self.translate_template("support.email", data))
        title = self.translate("support.title")
        self.send_email(title, email)
        self.speak_dialog("complete")


def create_skill():
    return SupportSkill()
