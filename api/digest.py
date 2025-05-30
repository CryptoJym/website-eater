# Example Vercel Serverless Function (LIMITED - for demo only)
# This won't maintain memory between requests!

from http.server import BaseHTTPRequestHandler
import json
import os
import google.genai as genai

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # This would work for individual requests
        # but can't store memories between calls
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        # Each request is isolated - no shared memory!
        api_key = os.environ.get('GOOGLE_API_KEY')
        
        # Process would work, but results aren't saved
        # This is the limitation of serverless
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': 'Serverless functions cannot maintain memory state'
        }).encode())
        return
