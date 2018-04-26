from test.integrationtests.skills.skill_tester import SkillTest

import mock

@mock.patch('mycroft.skills.core.DeviceApi.send_email')
@mock.patch('skill-support__init__.check_output')
def test_runner(skill, example, emitter, loader, m1, m2):
    def side_effect(title, body, skill):
        print("Sending e-mail")

    m2.side_effect = side_effect
    m1.return_value = "Test"
    return SkillTest(skill, example, emitter).run(loader)
