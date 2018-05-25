from test.integrationtests.skills.skill_tester import SkillTest

import mock

@mock.patch('mycroft.skills.core.DeviceApi.send_email')
def test_runner(skill, example, emitter, loader, m1):
    def side_effect(title, body, skill):
        print("Sending e-mail")

    m1.side_effect = side_effect
    s = [s for s in loader.skills if s and s.root_dir == skill][0]
    with mock.patch(s.__module__ + '.check_output') as m2:
        m2.return_value = b'Test'
        return SkillTest(skill, example, emitter).run(loader)
