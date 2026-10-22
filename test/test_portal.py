import pytest

import config.games.duel_linsk_templates
from core import device
from core.matcher import TemplateMatcher
from core.actions import Actions
from core.task import Task
from games.duellinks.portal import Portal

TEMPLATES_PATH = ""

@pytest.fixture
def templateSpec():
    return config.games.duel_linsk_templates.PORTAL_TEMPLATES

@pytest.fixture
def get_device():
    return device.DeviceManager.get()

@pytest.fixture
def matcher(get_device, templateSpec):
    return TemplateMatcher(get_device, templateSpec)

@pytest.fixture
def get_action(get_device, matcher):
    return Actions(get_device, matcher)

@pytest.fixture
def get_task(get_action):
    return Portal(get_action)

@pytest.mark.task
def test_task(get_task):
    task = get_task
    assert  task.run()




