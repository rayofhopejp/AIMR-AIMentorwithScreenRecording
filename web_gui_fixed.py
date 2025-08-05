import threading
import time
import boto3
import pyautogui
import io
import base64
import pygame
import tempfile
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

class WebGUI:
    def __init__(self):
        self.monitoring = False
        self.bedrock_client = None
        self.polly_client = None
        self.interval = 1
        
        try:
            pygame.mixer.init()
        except:
            pass
    
    def start_monitoring(self, config):
        try:
            session = boto3.Session(
                aws_access_key_id=config['accessKey'],
                aws_secret_access_key=config['secretKey'],
                region_name=config['region']
            )
            
            self.bedrock_client = session.client('bedrock-runtime')
            self.polly_client = session.client('polly')
            self.interval = int(config['interval'])
            
            self.monitoring = True
            threading.Thread(target=self.monitor_loop, daemon=True).start()
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_monitoring(self):
        self.monitoring = False
        return {"success": True}
    
    def monitor_loop(self):
        interval = self.interval
        
        while self.monitoring:
            try:
                screenshot = pyautogui.screenshot()
                buffer = io.BytesIO()
                screenshot.save(buffer, format='PNG')
                img_data = base64.b64encode(buffer.getvalue()).decode()
                
                response = self.bedrock_client.invoke_model(
                    modelId='us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 100,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "あなたはAWSのシニアソリューションアーキテクトです。部下の作業している画面が転送されてきます。画面を見て50文字以内で親しみやすい日本語アドバイスをください。"},
                                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}}
                            ]
                        }]
                    })
                )
                
                result = json.loads(response['body'].read())
                advice = result['content'][0]['text']
                
                audio_response = self.polly_client.synthesize_speech(
                    Text=advice, OutputFormat='mp3', VoiceId='Takumi', LanguageCode='ja-JP'
                )
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    f.write(audio_response['AudioStream'].read())
                    audio_file = f.name
                
                if pygame.mixer.get_init():
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                
                os.unlink(audio_file)
                
                for _ in range(interval):
                    if not self.monitoring:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"エラー: {e}")
                time.sleep(5)
    
    def get_html(self):
        return '''<!DOCTYPE html>
<html>
<head>
    <title>AI画面監視エージェント</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; margin: 40px; background: #f5f5f5; }
        .container { max-width: 500px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .buttons { text-align: center; margin: 20px 0; }
        button { padding: 10px 20px; margin: 0 10px; border: none; border-radius: 5px; font-size: 14px; cursor: pointer; }
        .start { background: #4CAF50; color: white; }
        .stop { background: #f44336; color: white; }
        .status { text-align: center; font-size: 18px; font-weight: bold; color: #2196F3; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI画面監視エージェント</h1>
        
        <div class="form-group">
            <label>AWS Access Key ID:</label>
            <input type="text" id="accessKey" placeholder="AKIA...">
        </div>
        
        <div class="form-group">
            <label>AWS Secret Access Key:</label>
            <input type="password" id="secretKey" placeholder="秘密キー">
        </div>
        
        <div class="form-group">
            <label>AWS Region:</label>
            <input type="text" id="region" value="us-east-1">
        </div>
        
        <div class="form-group">
            <label>監視間隔（秒）:</label>
            <input type="number" id="interval" value="60" min="30" max="1800">
        </div>
        
        <div class="buttons">
            <button class="start" onclick="startMonitoring()">監視開始</button>
            <button class="stop" onclick="stopMonitoring()">監視停止</button>
        </div>
        
        <div class="status" id="status">停止中</div>
    </div>

    <script>
        function startMonitoring() {
            const data = {
                action: 'start',
                accessKey: document.getElementById('accessKey').value,
                secretKey: document.getElementById('secretKey').value,
                region: document.getElementById('region').value,
                interval: document.getElementById('interval').value
            };
            
            fetch('/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(response => response.json())
              .then(result => {
                  if (result.success) {
                      document.getElementById('status').textContent = '監視中...';
                  } else {
                      alert('エラー: ' + result.error);
                  }
              });
        }
        
        function stopMonitoring() {
            fetch('/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'stop'})
            }).then(() => {
                document.getElementById('status').textContent = '停止中';
            });
        }
        
        setInterval(() => {
            fetch('/status').then(r => r.json()).then(data => {
                document.getElementById('status').textContent = data.status;
            });
        }, 1000);
    </script>
</body>
</html>'''

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, gui_instance, *args, **kwargs):
        self.gui = gui_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.gui.get_html().encode('utf-8'))
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = "監視中..." if self.gui.monitoring else "停止中"
            self.wfile.write(json.dumps({"status": status}).encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/control':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if data['action'] == 'start':
                result = self.gui.start_monitoring(data)
            else:
                result = self.gui.stop_monitoring()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def run_server():
    gui = WebGUI()
    
    def handler(*args, **kwargs):
        RequestHandler(gui, *args, **kwargs)
    
    server = HTTPServer(('localhost', 8080), handler)
    print("サーバー起動: http://localhost:8080")
    webbrowser.open('http://localhost:8080')
    server.serve_forever()

if __name__ == "__main__":
    run_server()
