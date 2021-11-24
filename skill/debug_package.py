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
import shutil
from glob import glob
from os import chdir
from os.path import dirname, isfile, join
from tempfile import mkdtemp, mkstemp
from zipfile import ZIP_DEFLATED, ZipFile

import mycroft
from mycroft.util import LOG

# TODO: Will need to read from config under KDE, etc.
# TODO: Needs to handle XDG paths
log_locations = [
    "/opt/mycroft/*.json",
    "/var/log/mycroft/*.log",
    "/etc/mycroft/*.conf",
    join(dirname(dirname(mycroft.__file__)), "scripts", "logs", "*.log"),
]
log_types = ["audio", "bus", "enclosure", "skills", "update", "voice"]


def get_log_files():
    log_files = sum([glob(pattern) for pattern in log_locations], [])
    for i in log_locations:
        for log_type in log_types:
            fn = i.replace("*", log_type)
            if fn in log_files:
                continue
            if isfile(fn):
                log_files.append(fn)
    return log_files


def create_debug_package(extra_files=None):
    fd, name = mkstemp(suffix=".zip")
    tmp_folder = mkdtemp()
    zip_files = []
    for file in get_log_files() + (extra_files or []):
        tar_name = file.strip("/").replace("/", ".")
        tmp_file = join(tmp_folder, tar_name)
        shutil.copy(file, tmp_file)
        zip_files.append(tar_name)

    chdir(tmp_folder)
    try:
        with ZipFile(name, "w", ZIP_DEFLATED) as zf:
            for fn in zip_files:
                zf.write(fn)
    except OSError as e:
        LOG.warning("Failed to create debug package: {}".format(e))
        return None
    return name
