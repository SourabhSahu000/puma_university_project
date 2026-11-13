import sys
import os
import urllib.parse
import json

# Add root directory to sys.path so app, database, and utils can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    """
    Normalizes PATH_INFO for Vercel Serverless environment.
    Any request rewritten to /api/index or /api/index/<path> has
    the /api/index prefix cleanly stripped so Flask routes match directly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Debug inspection endpoint: /__env
        req_uri = environ.get("REQUEST_URI", "")
        raw_path_info = environ.get("PATH_INFO", "")
        matched_hdr = environ.get("HTTP_X_MATCHED_PATH", "")

        if "/__env" in req_uri or "/__env" in raw_path_info or "/__env" in matched_hdr:
            safe_env = {k: str(v) for k, v in sorted(environ.items()) if isinstance(v, (str, int, bool, list, dict))}
            body = json.dumps(safe_env, indent=2).encode("utf-8")
            start_response("200 OK", [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(body)))
            ])
            return [body]

        # 1. Determine raw candidate path from proxy headers or PATH_INFO
        raw_path = None
        for hdr in ("HTTP_X_FORWARDED_URI", "HTTP_X_ORIGINAL_URI", "REQUEST_URI", "HTTP_X_MATCHED_PATH"):
            val = environ.get(hdr)
            if val and val not in ("/api/index", "/api/index/"):
                raw_path = val
                break

        if not raw_path:
            raw_path = environ.get("PATH_INFO") or "/"

        # Extract path component if query parameters are included
        candidate = urllib.parse.urlparse(raw_path).path

        # 2. Strip /api/index prefix if present
        if candidate.startswith("/api/index"):
            remainder = candidate[len("/api/index"):]
            if remainder and remainder != "/":
                clean_path = "/" + remainder.lstrip("/")
            else:
                clean_path = "/"
        elif candidate:
            clean_path = candidate
        else:
            clean_path = "/"

        environ["PATH_INFO"] = clean_path

        def debug_start_response(status, response_headers, exc_info=None):
            response_headers.append(("X-Debug-Orig-PathInfo", str(raw_path_info)))
            response_headers.append(("X-Debug-MatchedPath", str(matched_hdr)))
            response_headers.append(("X-Debug-RawPath", str(raw_path)))
            response_headers.append(("X-Debug-Candidate", str(candidate)))
            response_headers.append(("X-Debug-CleanPath", str(clean_path)))
            return start_response(status, response_headers, exc_info)

        return self.wsgi_app(environ, debug_start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
