import requests
from unittest import TestCase

from webcrawler.parser.robots_parser import RobotsParser

parser = RobotsParser(requests.get('https://www.facebook.com/robots.txt').text)


class AnyBotAccessTest(TestCase):
    def test_disallowed_root(self):
        self.assertFalse(parser.can_access(''))

    def test_disallowed_slash(self):
        self.assertFalse(parser.can_access(''))


class GoogleBotAccessTest(TestCase):
    AgentName = 'Googlebot'

    def test_allowed(self):
        self.assertTrue(parser.can_access('/safetycheck/', self.AgentName))

    def test_disallowed(self):
        self.assertFalse(parser.can_access('/ajax/', self.AgentName))
