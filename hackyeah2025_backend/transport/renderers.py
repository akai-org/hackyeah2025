"""
Custom renderers for transport app
"""
from rest_framework.renderers import JSONRenderer


class UnicodeJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that ensures Unicode characters (like Polish letters)
    are displayed properly instead of being escaped.
    """
    charset = 'utf-8'
    ensure_ascii = False

