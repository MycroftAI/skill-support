from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler


class SupportSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler(IntentBuilder().require('Support'))
    def handle_support(self, message):
        self.speak_dialog('support')


def create_skill():
    return SupportSkill()

