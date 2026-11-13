import sys
import os
import urllib.parse

# Add root directory to sys.path so app, database, and utils can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    """
    Normalizes WSGI environment for Vercel Serverless Functions.
    Vercel rewrites incoming requests to /api/index.
    The original request path is captured in HTTP_X_MATCHED_PATH (or proxy headers).
    This middleware restores the original PATH_INFO and clears SCRIPT_NAME
    so Flask routes (/admin, /student, /login, /departments, etc.) match directly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = (
            environ.get("HTTP_X_MATCHED_PATH") or
            environ.get("HTTP_X_FORWARDED_URI") or
            environ.get("HTTP_X_ORIGINAL_URI") or
            environ.get("REQUEST_URI")
        )

        if matched:
            path_only = urllib.parse.urlparse(matched).path
            if path_only and path_only not in ("/api/index", "/api/index/"):
                environ["PATH_INFO"] = path_only
            elif environ.get("PATH_INFO") in ("/api/index", "/api/index/", ""):
                environ["PATH_INFO"] = "/"
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index/", ""):
            environ["PATH_INFO"] = "/"

        # Clear SCRIPT_NAME so url_for builds clean URLs without /api/index prefix
        environ["SCRIPT_NAME"] = ""

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
