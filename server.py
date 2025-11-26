from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class ReadingHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Try to parse as JSON for pretty printing
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"[{self.path}] Received reading:")
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                print(f"[{self.path}] Received raw reading:")
                print(post_data.decode('utf-8'))
            
            print("-" * 50)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('localhost', 3000), ReadingHandler)
    print("🔌 Smart meter receiver server started on http://localhost:3000")
    print("📡 Ready to receive readings...")
    print("💡 Health check available at http://localhost:3000/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
