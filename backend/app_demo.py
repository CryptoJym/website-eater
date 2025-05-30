import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import json
from datetime import datetime
from urllib.parse import urlparse
import hashlib

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    MEM0_API_KEY = os.getenv('MEM0_API_KEY')
    USER_ID = os.getenv('USER_ID', 'default_user')
    AGENT_ID = os.getenv('AGENT_ID', 'website_eater_agent')
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

# Demo mode flag
DEMO_MODE = Config.GOOGLE_API_KEY == 'demo_key_for_demonstration'

# Simple in-memory storage for demo
demo_memories = []

def extract_content_with_gemini_demo(url, options=None):
    """Demo version that simulates URL extraction"""
    return {
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'domain': urlparse(url).netloc,
        'content': f"This is demo content extracted from {url}. In production, Google's URL Context tool would extract real content here.",
        'extraction_status': 'success',
        'demo': True
    }

def process_with_agent_demo(extracted_data, user_id):
    """Demo version of agent processing"""
    content_hash = hashlib.sha256(extracted_data['content'].encode()).hexdigest()[:8]
    memory_id = f"mem_{content_hash}"
    
    # Store in demo memory
    demo_memories.append({
        'id': memory_id,
        'user_id': user_id,
        'content': extracted_data['content'],
        'metadata': {
            'url': extracted_data['url'],
            'domain': extracted_data['domain'],
            'timestamp': extracted_data['timestamp'],
            'content_type': 'demo'
        }
    })
    
    return {
        'memory_id': memory_id,
        'content_type': 'demo',
        'routes': [
            {'destination': 'knowledge_base'},
            {'destination': 'demo_storage'}
        ]
    }

# API Routes
@app.route('/')
def index():
    """Serve the frontend"""
    demo_banner = """
    <div style="background: #ff9800; color: white; padding: 10px; text-align: center; margin-bottom: 20px;">
        🎮 DEMO MODE - Using simulated data. Configure your Google API key to use real URL extraction.
    </div>
    """ if DEMO_MODE else ""
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Website Eater - Powered by Google's URL Context</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                min-height: 100vh;
            }
            
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .header h1 {
                font-size: 3rem;
                background: linear-gradient(to right, #4285f4, #34a853);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            
            .subtitle {
                color: #94a3b8;
                font-size: 1.1rem;
                margin-bottom: 1rem;
            }
            
            .google-badge {
                display: inline-block;
                background: #4285f4;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            
            .main-card {
                background: #1e293b;
                border-radius: 16px;
                padding: 2rem;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                margin-bottom: 2rem;
            }
            
            .input-group {
                display: flex;
                gap: 12px;
                margin-bottom: 1.5rem;
            }
            
            input[type="url"] {
                flex: 1;
                padding: 14px 20px;
                background: #0f172a;
                border: 2px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 16px;
                transition: all 0.3s;
            }
            
            input[type="url"]:focus {
                outline: none;
                border-color: #4285f4;
                box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
            }
            
            button {
                padding: 14px 28px;
                background: #4285f4;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            button:hover {
                background: #3367d6;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
            }
            
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .options {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-bottom: 1.5rem;
            }
            
            .option {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px;
                background: #0f172a;
                border-radius: 8px;
                transition: background 0.2s;
            }
            
            .option:hover {
                background: #1a2332;
            }
            
            .option input[type="checkbox"] {
                width: 20px;
                height: 20px;
                cursor: pointer;
                accent-color: #4285f4;
            }
            
            .option label {
                cursor: pointer;
                flex: 1;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: #1e293b;
                padding: 1.5rem;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #334155;
            }
            
            .stat-value {
                font-size: 2.5rem;
                font-weight: bold;
                background: linear-gradient(to right, #4285f4, #34a853);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .stat-label {
                color: #94a3b8;
                margin-top: 0.5rem;
                font-size: 0.9rem;
            }
            
            #results {
                margin-top: 2rem;
            }
            
            .result-item {
                background: #1e293b;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1rem;
                border-left: 4px solid #4285f4;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .result-header {
                display: flex;
                justify-content: space-between;
                align-items: start;
                margin-bottom: 1rem;
            }
            
            .result-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #f1f5f9;
            }
            
            .result-meta {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }
            
            .meta-item {
                background: #0f172a;
                padding: 0.75rem;
                border-radius: 6px;
            }
            
            .meta-label {
                color: #64748b;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .meta-value {
                color: #e2e8f0;
                font-weight: 500;
                margin-top: 0.25rem;
            }
            
            .loading {
                text-align: center;
                padding: 3rem;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 3px solid #334155;
                border-top-color: #4285f4;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .error {
                background: #dc2626;
                color: white;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            
            .success {
                background: #16a34a;
                color: white;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            
            .routes {
                display: flex;
                gap: 0.5rem;
                margin-top: 1rem;
            }
            
            .route-tag {
                padding: 4px 12px;
                background: #334155;
                color: #e2e8f0;
                border-radius: 4px;
                font-size: 0.875rem;
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .feature {
                background: #1e293b;
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid #334155;
                transition: all 0.3s;
            }
            
            .feature:hover {
                border-color: #4285f4;
                transform: translateY(-2px);
            }
            
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 1rem;
            }
            
            .feature-title {
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #f1f5f9;
            }
            
            .feature-desc {
                color: #94a3b8;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        ''' + demo_banner + '''
        <div class="container">
            <div class="header">
                <h1>🌐 Website Eater</h1>
                <p class="subtitle">Extract and analyze web content with AI-powered intelligence</p>
                <span class="google-badge">Powered by Google's URL Context Tool</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalProcessed">0</div>
                    <div class="stat-label">Pages Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalMemories">0</div>
                    <div class="stat-label">Memories Created</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="quotaUsed">0</div>
                    <div class="stat-label">API Quota Used</div>
                </div>
            </div>
            
            <div class="main-card">
                <div class="input-group">
                    <input type="url" id="urlInput" placeholder="https://example.com" />
                    <button onclick="processURL()" id="processBtn">
                        <span>🔍</span> Extract Content
                    </button>
                </div>
                
                <div class="options">
                    <div class="option">
                        <input type="checkbox" id="deepAnalysis" checked>
                        <label for="deepAnalysis">Deep Analysis (with Google Search)</label>
                    </div>
                    <div class="option">
                        <input type="checkbox" id="extractImages">
                        <label for="extractImages">Extract Images Info</label>
                    </div>
                    <div class="option">
                        <input type="checkbox" id="extractMetadata" checked>
                        <label for="extractMetadata">Extract Metadata</label>
                    </div>
                </div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🚀</div>
                    <div class="feature-title">20 URLs per Request</div>
                    <div class="feature-desc">Process multiple pages in a single API call</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Google Search Integration</div>
                    <div class="feature-desc">Combine with search for comprehensive analysis</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">AI Memory</div>
                    <div class="feature-desc">Store and retrieve content with mem0</div>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            let processedCount = 0;
            let memoryCount = 0;
            
            async function processURL() {
                const url = document.getElementById('urlInput').value;
                const resultsDiv = document.getElementById('results');
                const processBtn = document.getElementById('processBtn');
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                const options = {
                    deep_analysis: document.getElementById('deepAnalysis').checked,
                    extract_images: document.getElementById('extractImages').checked,
                    extract_metadata: document.getElementById('extractMetadata').checked
                };
                
                processBtn.disabled = true;
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top: 1rem; color: #94a3b8;">Using Gemini to extract content...</p></div>';
                
                try {
                    const response = await fetch('/api/process', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url, options })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        processedCount++;
                        memoryCount++;
                        updateStats();
                        
                        resultsDiv.innerHTML = `
                            <div class="success">✅ Successfully extracted content!</div>
                            <div class="result-item">
                                <div class="result-header">
                                    <h3 class="result-title">${data.title || 'Extracted Content'}</h3>
                                </div>
                                <div class="result-meta">
                                    <div class="meta-item">
                                        <div class="meta-label">URL</div>
                                        <div class="meta-value">${data.url}</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Memory ID</div>
                                        <div class="meta-value">${data.memory_id}</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Content Length</div>
                                        <div class="meta-value">${data.content_length} chars</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Content Type</div>
                                        <div class="meta-value">${data.content_type}</div>
                                    </div>
                                </div>
                                <div class="routes">
                                    ${data.routes.map(r => `<span class="route-tag">${r.destination}</span>`).join('')}
                                </div>
                            </div>
                        `;
                        
                        // Clear input
                        document.getElementById('urlInput').value = '';
                    } else {
                        resultsDiv.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                } finally {
                    processBtn.disabled = false;
                }
            }
            
            function updateStats() {
                document.getElementById('totalProcessed').textContent = processedCount;
                document.getElementById('totalMemories').textContent = memoryCount;
                document.getElementById('quotaUsed').textContent = processedCount;
            }
            
            // Allow Enter key to submit
            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') processURL();
            });
            
            // Initialize stats
            updateStats();
        </script>
    </body>
    </html>
    ''')

@app.route('/api/process', methods=['POST'])
def process_url():
    """Main API endpoint to process URLs"""
    try:
        data = request.json
        url = data.get('url')
        user_id = data.get('user_id', Config.USER_ID)
        options = data.get('options', {})
        
        if not url:
            return jsonify({'status': 'error', 'error': 'No URL provided'}), 400
        
        # Extract content (demo mode)
        extracted_data = extract_content_with_gemini_demo(url, options)
        
        # Process with agent (demo mode)
        processing_result = process_with_agent_demo(extracted_data, user_id)
        
        return jsonify({
            'status': 'success',
            'url': url,
            'title': f"Content from {urlparse(url).netloc}",
            'content_length': len(extracted_data['content']),
            'content_type': processing_result.get('content_type', 'demo'),
            'memory_id': processing_result.get('memory_id'),
            'routes': processing_result.get('routes', []),
            'demo': True
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/memories/<user_id>', methods=['GET'])
def get_memories(user_id):
    """Get all memories for a user"""
    user_memories = [m for m in demo_memories if m['user_id'] == user_id]
    return jsonify({
        'status': 'success',
        'memories': user_memories
    })

@app.route('/api/search', methods=['POST'])
def search_memories():
    """Search memories"""
    try:
        data = request.json
        query = data.get('query', '').lower()
        user_id = data.get('user_id', Config.USER_ID)
        
        # Simple search in demo memories
        results = []
        for memory in demo_memories:
            if memory['user_id'] == user_id and query in memory['content'].lower():
                results.append(memory)
        
        return jsonify({
            'status': 'success',
            'results': results[:10]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Website Eater - Demo Mode")
    print("=" * 50)
    if DEMO_MODE:
        print("⚠️  Running in DEMO MODE - Configure your Google API key for real functionality")
    else:
        print("✅ Google API key configured")
    print(f"📍 Starting server at http://localhost:5000")
    print("=" * 50 + "\n")
    
    app.run(debug=True, port=5000)
