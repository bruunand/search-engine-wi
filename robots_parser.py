import re


class RobotsParser:
    AnyUserAgent = '*'

    def __init__(self, robot_text=None):
        self.disallowed_pages = dict()

        if robot_text:
            self.parse(robot_text)

    def parse(self, robot_text):
        lines = robot_text.split('\n')

        current_user_agent = None
        for line in lines:
            # Attempt to match user-agent signature
            agent_match = re.match("User-[aA]gent: (.*)", line)
            if agent_match:
                current_user_agent = agent_match.group(1)

                # Initialize set of disallowed pages for this agent if not previous initialized
                if current_user_agent not in self.disallowed_pages:
                    self.disallowed_pages[current_user_agent] = set()

                continue

            # If no current user agent has been specified, no point in trying to parse disallowed pages
            if not current_user_agent:
                continue

            # Attempt to match disallow signature
            disallow_match = re.match("Disallow: (.*)", line)
            if disallow_match:
                self.disallowed_pages[current_user_agent].add(disallow_match.group(1))

    def can_access(self, page, user_agent=AnyUserAgent):
        if not page:
            page = '/'

        if user_agent in self.disallowed_pages:
            for disallowed_page in self.disallowed_pages[user_agent]:
                # If the disallowed page is empty, all pages can be accessed
                if not disallowed_page:
                    return True

                if page.startswith(disallowed_page):
                    return False
        else:
            if user_agent != self.AnyUserAgent:
                return self.can_access(page)

        return True
