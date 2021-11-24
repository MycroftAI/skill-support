# Copyright 2021 Mycroft AI Inc.
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

import requests

from mycroft.util import LOG


def upload_file(filename):
    with open(filename, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": f})
    if r.status_code != 200:
        LOG.warning("Failed to post logs: {}".format(r.text))
        return ""
    return r.text.strip()

def upload_debug_package(package):
    if not package:
        return None
    url = upload_file(package)
    if not url:
        return None
    return url
