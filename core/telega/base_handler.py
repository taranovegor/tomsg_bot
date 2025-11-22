class BaseHandler:
    def __init__(self, parser, analytics):
        self.parser = parser
        self.analytics = analytics

    async def process_url(self, url: str, events):
        entity = self.parser.parse(url)
        # events.add("page_view", page_location=url)
        return entity
