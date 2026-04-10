from django.core.serializers.json import DjangoJSONEncoder


class ParserError(Exception):
    def __str__(self):
        if not self.args:
            return self.__class__.__name__
        return "{}: {}".format(self.__class__.__name__, self.args[0])


class WooeyJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, ParserError):
            return str(o)
        return super().default(o)
