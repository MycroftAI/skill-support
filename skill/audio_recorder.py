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


import wave
from threading import Event, Thread

import pyaudio


class AudioRecorder:
    def __init__(self, **params):
        params.setdefault("format", pyaudio.paInt16)
        params.setdefault("channels", 1)
        params.setdefault("rate", 16000)
        params.setdefault("frames_per_buffer", 1024)
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(input=True, **params)
        self.params = params
        self.frames = []

    def update(self):
        self.frames.append(self.stream.read(self.params["frames_per_buffer"]))

    def stop(self):
        if not self.stream.is_stopped():
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()

    def save(self, filename):
        self.stop()
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(self.params["channels"])
            wf.setsampwidth(self.audio.get_sample_size(self.params["format"]))
            wf.setframerate(self.params["rate"])
            wf.writeframes(b"".join(self.frames))


class ThreadedRecorder(Thread, AudioRecorder):
    def __init__(self, daemon=False, **params):
        Thread.__init__(self, daemon=daemon)
        AudioRecorder.__init__(self, **params)
        self.stop_event = Event()
        self.start()

    def run(self):
        while not self.stop_event.is_set():
            self.update()

    def stop(self):
        if self.is_alive():
            self.stop_event.set()
            self.join()
            AudioRecorder.stop(self)
