import sys
import os

# Add root directory to sys.path so app, database, and utils can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    """
    Normalizes PATH_INFO for Vercel Serverless environment.
    When Vercel uses rewrites, the original user-requested path is passed in
    HTTP_X_MATCHED_PATH (e.g. '/', '/login', '/admin') while PATH_INFO is
    rewritten to '/api/index'. This middleware restores PATH_INFO so Flask
    matches the exact user-requested route.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        path_info = environ.get("PATH_INFO", "")

        if matched_path and not matched_path.startswith("/api/index"):
            environ["PATH_INFO"] = matched_path
        elif path_info in ("/api/index", "/api/index/"):
            environ["PATH_INFO"] = "/"
        elif path_info.startswith("/api/index/"):
            sub_path = path_info[len("/api/index"):]
            environ["PATH_INFO"] = sub_path if sub_path else "/"

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
