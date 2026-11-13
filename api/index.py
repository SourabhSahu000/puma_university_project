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
    Vercel rewrites incoming requests to /api/index?__vercel_path=$1.
    This middleware:
      1. Extracts __vercel_path from QUERY_STRING to restore PATH_INFO
      2. Removes __vercel_path from QUERY_STRING so application request.args are pristine
      3. Resets SCRIPT_NAME to '' so url_for builds clean, canonical application URLs
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")
        parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)

        target_path = None
        if "__vercel_path" in parsed:
            raw_vals = parsed.pop("__vercel_path")
            raw_path = raw_vals[0] if raw_vals else ""
            if raw_path:
                target_path = raw_path if raw_path.startswith("/") else "/" + raw_path
            else:
                target_path = "/"

            # Clean internal routing param from query string
            filtered_query = [(k, v) for k, vs in parsed.items() for v in vs]
            environ["QUERY_STRING"] = urllib.parse.urlencode(filtered_query)

        if not target_path:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index", "/api/index/", ""):
                target_path = "/"
            elif path_info.startswith("/api/index/"):
                sub = path_info[len("/api/index"):]
                target_path = sub if sub else "/"
            else:
                target_path = path_info

        environ["PATH_INFO"] = target_path
        environ["SCRIPT_NAME"] = ""

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
