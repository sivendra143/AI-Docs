# cgi.py - Minimal shim for Python 3.13 compatibility
class FieldStorage:
    def __init__(self, *args, **kwargs):
        self.filename = None
        self.file = None
        self.value = None
        self.type = None
        self.type_options = {}
        self.disposition = None
        self.disposition_options = {}
        self.headers = {}

    def getvalue(self, key, default=None):
        return getattr(self, key, default)

    def getfirst(self, key, default=None):
        return getattr(self, key, default)

def parse(fp=None, environ=None, keep_blank_values=0, strict_parsing=0):
    return {}

def parse_qs(qs, keep_blank_values=0, strict_parsing=0):
    from urllib.parse import parse_qs as _parse_qs
    return _parse_qs(qs, keep_blank_values, strict_parsing)

def parse_qsl(qs, keep_blank_values=0, strict_parsing=0):
    from urllib.parse import parse_qsl as _parse_qsl
    return _parse_qsl(qs, keep_blank_values, strict_parsing)

def escape(s, quote=None):
    import html
    return html.escape(s, quote=quote)

# Add any other cgi module functions that might be needed
print_environ = lambda: None
print_form = lambda x: None
print_directory = lambda: None
print_environ_usage = lambda: None
