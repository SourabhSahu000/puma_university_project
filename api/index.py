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
    Normalizes PATH_INFO for Vercel Serverless environment.
    Vercel rewrites incoming requests to /api/index?__vercel_path=$1.
    This middleware restores the original PATH_INFO and cleans QUERY_STRING
    so Flask routes match perfectly across all GET, POST, and dynamic paths.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get("HTTP_X_DEBUG") == "1":
            import json
            safe_env = {k: str(v) for k, v in environ.items() if isinstance(v, (str, int, bool))}
            body = json.dumps(safe_env, indent=2).encode("utf-8")
            start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
            return [body]

        parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
        target_path = None

        # 1. Check if __vercel_path was captured by vercel.json rewrite
        if "__vercel_path" in parsed:
            raw_path = parsed.pop("__vercel_path")[0] if parsed.get("__vercel_path") else ""
            if raw_path:
                target_path = raw_path if raw_path.startswith("/") else "/" + raw_path
            else:
                target_path = "/"
            # Clean internal param from query string
            filtered = [(k, v) for k, vs in parsed.items() for v in vs]
            environ["QUERY_STRING"] = urllib.parse.urlencode(filtered)

        # 2. Check standard proxy headers if __vercel_path is not present
        if not target_path:
            for hdr in ("HTTP_X_FORWARDED_URI", "HTTP_X_ORIGINAL_URI", "REQUEST_URI"):
                val = environ.get(hdr)
                if val:
                    target_path = urllib.parse.urlparse(val).path
                    break

        # 3. Check HTTP_X_MATCHED_PATH (only if not literal /api/index)
        if not target_path:
            matched_path = environ.get("HTTP_X_MATCHED_PATH")
            if matched_path and not matched_path.startswith("/api/index"):
                target_path = matched_path

        # 4. Fallback to existing PATH_INFO
        if not target_path:
            path_info = environ.get("PATH_INFO", "")
            if path_info in ("/api/index", "/api/index/", ""):
                target_path = "/"
            elif path_info.startswith("/api/index/"):
                sub = path_info[len("/api/index"):]
                target_path = sub if sub else "/"
            else:
                target_path = path_info

        if target_path:
            environ["PATH_INFO"] = target_path

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
