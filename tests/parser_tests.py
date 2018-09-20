import requests
from unittest import TestCase

from webcrawler.parser.robots_parser import RobotsParser

parser = RobotsParser(requests.get('https://www.facebook.com/robots.txt').text)


class AnyBotAccessTest(TestCase):
    def test(self):
        self.assertFalse(parser.can_access('/'))
        self.assertFalse(parser.can_access(''))


class GoogleBotAccessTest(TestCase):
    AgentName = 'Googlebot'

    def test(self):
        self.assertTrue(parser.can_access('/safetycheck/', self.AgentName))
        self.assertFalse(parser.can_access('/ajax/', self.AgentName))
