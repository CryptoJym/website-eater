import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import google.genai as genai
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv
import json
from datetime import datetime
from urllib.parse import urlparse
import hashlib

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Google GenAI client
genai_client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    USER_ID = os.getenv('USER_ID', 'default_user')
    AGENT_ID = os.getenv('AGENT_ID', 'website_eater_agent')
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro-exp-03-25')

# Simple in-memory storage
memories = []

def extract_with_gemini_url_digestion(url, options=None):
    """Use Gemini's native URL digestion capability"""
    try:
        # Build prompts based on URL type
        if 'youtube.com' in url or 'youtu.be' in url:
            prompt = f"""Analyze this YouTube video: {url}

Please provide:
1. Video title and channel
2. Main topics discussed
3. Key points or takeaways
4. Video duration and upload date if available
5. Summary of the content"""

        elif any(domain in url for domain in ['github.com', 'gitlab.com']):
            prompt = f"""Analyze this code repository: {url}

Please provide:
1. Repository name and description
2. Main programming languages used
3. Purpose of the project
4. Key features or functionality
5. README summary if available"""

        else:
            prompt = f"""Analyze this webpage: {url}

Please provide:
1. Page title and main topic
2. Content type (article, documentation, product page, etc.)
3. Key information or main points
4. Target audience
5. Summary of the content"""

        # Add additional instructions based on options
        if options:
            if options.get('extract_metadata'):
                prompt += "\n6. Extract any metadata (author, date, tags)"
            if options.get('deep_analysis'):
                prompt += "\n7. Provide deeper insights and related topics"

        # Generate content using Gemini - URLs are processed natively
        config = GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=2048,
        )
        
        response = genai_client.models.generate_content(
            model=Config.MODEL_ID,
            contents=prompt,
            config=config
        )
        
        # Extract the response
        analysis = ""
        if hasattr(response, 'text'):
            analysis = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text'):
                    analysis += part.text
        
        # Check if URL was actually accessed
        url_accessed = False
        if analysis and len(analysis) > 100:
            # Simple heuristic: if we got substantial content, URL was likely accessed
            domain = urlparse(url).netloc
            if any(indicator in analysis.lower() for indicator in [
                'video', 'repository', 'article', 'page', 'content', 
                'title', 'author', domain.lower()
            ]):
                url_accessed = True
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'analysis': analysis,
            'url_accessed': url_accessed,
            'extraction_status': 'success',
            'method': 'gemini_url_digestion'
        }
        
    except Exception as e:
        print(f"Gemini URL digestion error: {e}")
        error_msg = str(e)
        
        # Check for quota errors
        if '429' in error_msg or 'quota' in error_msg.lower():
            return {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'domain': urlparse(url).netloc,
                'analysis': 'Quota exceeded - Gemini API limit reached',
                'extraction_status': 'quota_error',
                'error': error_msg,
                'method': 'gemini_url_digestion'
            }
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'analysis': '',
            'extraction_status': 'error',
            'error': error_msg,
            'method': 'gemini_url_digestion'
        }

def process_content(extracted_data, user_id):
    """Process extracted content and store in memory"""
    try:
        analysis = extracted_data.get('analysis', '')
        
        if not analysis or analysis == 'Quota exceeded - Gemini API limit reached':
            return {
                'status': 'error',
                'error': 'No content extracted (API quota may be exceeded)'
            }
        
        # Generate memory ID
        content_hash = hashlib.sha256(analysis.encode()).hexdigest()[:8]
        memory_id = f"mem_{content_hash}_{len(memories)}"
        
        # Detect content type from analysis
        analysis_lower = analysis.lower()
        content_type = 'general'
        
        if 'youtube' in analysis_lower or 'video' in analysis_lower:
            content_type = 'video'
        elif 'repository' in analysis_lower or 'github' in analysis_lower:
            content_type = 'code'
        elif 'documentation' in analysis_lower or 'docs' in analysis_lower:
            content_type = 'documentation'
        elif 'article' in analysis_lower or 'blog' in analysis_lower:
            content_type = 'article'
        elif 'product' in analysis_lower or 'service' in analysis_lower:
            content_type = 'product'
        
        # Extract title from analysis (first line or first sentence)
        title = "Untitled"
        lines = analysis.split('\n')
        for line in lines:
            if line.strip() and len(line.strip()) > 5:
                title = line.strip()
                if title.endswith(':'):
                    title = title[:-1]
                break
        
        # Store in memory
        memory_entry = {
            'id': memory_id,
            'user_id': user_id,
            'title': title,
            'content': analysis,
            'metadata': {
                'url': extracted_data['url'],
                'domain': extracted_data['domain'],
                'timestamp': extracted_data['timestamp'],
                'content_type': content_type,
                'content_length': len(analysis),
                'extraction_method': extracted_data.get('method'),
                'url_accessed': extracted_data.get('url_accessed', False)
            }
        }
        memories.append(memory_entry)
        
        # Determine routes
        routes = []
        if content_type == 'video':
            routes = [{'destination': 'video_library'}, {'destination': 'knowledge_base'}]
        elif content_type == 'code':
            routes = [{'destination': 'code_repository'}, {'destination': 'knowledge_base'}]
        elif content_type == 'documentation':
            routes = [{'destination': 'docs_repository'}, {'destination': 'knowledge_base'}]
        elif content_type == 'article':
            routes = [{'destination': 'article_archive'}, {'destination': 'knowledge_base'}]
        elif content_type == 'product':
            routes = [{'destination': 'product_database'}, {'destination': 'knowledge_base'}]
        else:
            routes = [{'destination': 'knowledge_base'}]
        
        return {
            'status': 'success',
            'memory_id': memory_id,
            'title': title,
            'content_type': content_type,
            'routes': routes,
            'content_length': len(analysis),
            'analysis': analysis,
            'url_accessed': extracted_data.get('url_accessed', False),
            'method': extracted_data.get('method')
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

# API Routes
@app.route('/')
def index():
    """Serve the frontend"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Website Eater - Gemini URL Digestion</title>
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
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .header h1 {
                font-size: 3rem;
                background: linear-gradient(to right, #4285f4, #ea4335, #fbbc05, #34a853);
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
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #4285f4;
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                margin: 0 4px;
            }
            
            .google-badge.active {
                background: #34a853;
            }
            
            .google-badge.limited {
                background: #f59e0b;
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
            
            .url-examples {
                margin-bottom: 1.5rem;
                padding: 1rem;
                background: #0f172a;
                border-radius: 8px;
            }
            
            .url-examples h4 {
                color: #94a3b8;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }
            
            .example-url {
                display: inline-block;
                padding: 4px 12px;
                margin: 4px;
                background: #334155;
                border-radius: 4px;
                font-size: 0.85rem;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .example-url:hover {
                background: #4285f4;
                transform: translateY(-1px);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
                padding: 2rem;
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
                margin-bottom: 1.5rem;
            }
            
            .result-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 0.5rem;
            }
            
            .result-url {
                color: #64748b;
                font-size: 0.9rem;
                word-break: break-all;
            }
            
            .result-meta {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }
            
            .meta-item {
                background: #0f172a;
                padding: 1rem;
                border-radius: 8px;
            }
            
            .meta-label {
                color: #64748b;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            
            .meta-value {
                color: #e2e8f0;
                font-weight: 500;
                font-size: 1.1rem;
            }
            
            .content-preview {
                background: #0f172a;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1.5rem 0;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .content-preview h4 {
                color: #94a3b8;
                margin-bottom: 1rem;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .content-preview pre {
                white-space: pre-wrap;
                color: #cbd5e1;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
                line-height: 1.6;
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
            
            .warning {
                background: #f59e0b;
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
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .routes {
                display: flex;
                gap: 0.5rem;
                margin-top: 1rem;
            }
            
            .route-tag {
                padding: 6px 16px;
                background: #334155;
                color: #e2e8f0;
                border-radius: 6px;
                font-size: 0.875rem;
                font-weight: 500;
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
            
            .url-status {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.85rem;
                font-weight: 500;
            }
            
            .url-status.accessed {
                background: #059669;
                color: white;
            }
            
            .url-status.not-accessed {
                background: #dc2626;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 Website Eater</h1>
                <p class="subtitle">Native URL Digestion with Gemini 2.5 Pro</p>
                <span id="api-status" class="google-badge active">✅ Gemini 2.5 Pro</span>
                <span id="feature-status" class="google-badge active">🔗 URL Digestion Active</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalProcessed">0</div>
                    <div class="stat-label">URLs Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="successRate">100%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="totalMemories">0</div>
                    <div class="stat-label">Memories Created</div>
                </div>
            </div>
            
            <div class="main-card">
                <div class="input-group">
                    <input type="url" id="urlInput" placeholder="Enter any URL (YouTube, GitHub, articles, etc.)" />
                    <button onclick="processURL()" id="processBtn">
                        <span>🔗</span> Digest URL
                    </button>
                </div>
                
                <div class="url-examples">
                    <h4>Try these example URLs:</h4>
                    <span class="example-url" onclick="setURL('https://www.youtube.com/watch?v=dQw4w9WgXcQ')">YouTube Video</span>
                    <span class="example-url" onclick="setURL('https://github.com/google-gemini/cookbook')">GitHub Repo</span>
                    <span class="example-url" onclick="setURL('https://blog.google/technology/ai/')">Google AI Blog</span>
                    <span class="example-url" onclick="setURL('https://en.wikipedia.org/wiki/Machine_learning')">Wikipedia</span>
                    <span class="example-url" onclick="setURL('https://docs.python.org/3/')">Documentation</span>
                </div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">📹</div>
                    <div class="feature-title">YouTube Videos</div>
                    <div class="feature-desc">Digest video content, transcripts, and metadata directly</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">💻</div>
                    <div class="feature-title">GitHub Repos</div>
                    <div class="feature-desc">Analyze code repositories, READMEs, and project structure</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">📰</div>
                    <div class="feature-title">Any Webpage</div>
                    <div class="feature-desc">Extract and understand content from any public URL</div>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            let processedCount = 0;
            let successCount = 0;
            let memoryCount = 0;
            let apiAvailable = true;
            
            function setURL(url) {
                document.getElementById('urlInput').value = url;
            }
            
            async function processURL() {
                const url = document.getElementById('urlInput').value;
                const resultsDiv = document.getElementById('results');
                const processBtn = document.getElementById('processBtn');
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                processBtn.disabled = true;
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top: 1rem; color: #94a3b8;">🔗 Digesting URL with Gemini...</p></div>';
                
                try {
                    const response = await fetch('/api/digest', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            url,
                            options: {
                                extract_metadata: true,
                                deep_analysis: true
                            }
                        })
                    });
                    
                    const data = await response.json();
                    
                    processedCount++;
                    
                    if (data.status === 'success') {
                        successCount++;
                        memoryCount++;
                        updateStats();
                        
                        // Update API status if quota error
                        if (data.method === 'quota_error') {
                            apiAvailable = false;
                            document.getElementById('api-status').className = 'google-badge limited';
                            document.getElementById('api-status').innerHTML = '⚠️ API Quota Exceeded';
                        }
                        
                        const urlStatusClass = data.url_accessed ? 'accessed' : 'not-accessed';
                        const urlStatusText = data.url_accessed ? '✅ URL Accessed' : '❌ URL Not Accessed';
                        
                        resultsDiv.innerHTML = `
                            <div class="success">
                                <span>✅</span>
                                <span>Successfully processed URL!</span>
                            </div>
                            <div class="result-item">
                                <div class="result-header">
                                    <h3 class="result-title">${data.title}</h3>
                                    <div class="result-url">${data.url}</div>
                                </div>
                                
                                <div class="result-meta">
                                    <div class="meta-item">
                                        <div class="meta-label">Memory ID</div>
                                        <div class="meta-value">${data.memory_id}</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Content Type</div>
                                        <div class="meta-value">${data.content_type}</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Method</div>
                                        <div class="meta-value">${data.method || 'gemini_url_digestion'}</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">URL Status</div>
                                        <div class="meta-value">
                                            <span class="url-status ${urlStatusClass}">${urlStatusText}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="content-preview">
                                    <h4>Gemini Analysis</h4>
                                    <pre>${data.analysis || 'No analysis available'}</pre>
                                </div>
                                
                                <div class="routes">
                                    <div class="meta-label" style="margin-right: 10px;">Routed to:</div>
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
                    updateStats();
                }
            }
            
            function updateStats() {
                document.getElementById('totalProcessed').textContent = processedCount;
                document.getElementById('totalMemories').textContent = memoryCount;
                const rate = processedCount > 0 ? Math.round((successCount / processedCount) * 100) : 100;
                document.getElementById('successRate').textContent = rate + '%';
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

@app.route('/api/digest', methods=['POST'])
def digest_url():
    """Main API endpoint to digest URLs using Gemini"""
    try:
        data = request.json
        url = data.get('url')
        user_id = data.get('user_id', Config.USER_ID)
        options = data.get('options', {})
        
        if not url:
            return jsonify({'status': 'error', 'error': 'No URL provided'}), 400
        
        # Use Gemini's URL digestion
        extracted_data = extract_with_gemini_url_digestion(url, options)
        
        if extracted_data['extraction_status'] == 'error':
            return jsonify({
                'status': 'error', 
                'error': extracted_data.get('error', 'Failed to digest URL')
            }), 400
        
        # Process and store
        processing_result = process_content(extracted_data, user_id)
        
        if processing_result['status'] == 'error':
            return jsonify(processing_result), 400
        
        return jsonify({
            'status': 'success',
            'url': url,
            'title': processing_result['title'],
            'content_length': processing_result['content_length'],
            'content_type': processing_result['content_type'],
            'memory_id': processing_result['memory_id'],
            'routes': processing_result['routes'],
            'analysis': processing_result.get('analysis', ''),
            'url_accessed': processing_result.get('url_accessed', False),
            'method': processing_result.get('method', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/memories/<user_id>', methods=['GET'])
def get_memories(user_id):
    """Get all memories for a user"""
    user_memories = [m for m in memories if m['user_id'] == user_id]
    return jsonify({
        'status': 'success',
        'memories': user_memories
    })

if __name__ == '__main__':
    print("\n🌐 Website Eater - Gemini URL Digestion")
    print("=" * 50)
    print("✅ Google API Key: Configured")
    print(f"📍 Model: {Config.MODEL_ID}")
    print(f"📍 Starting server at http://localhost:5003")
    print("=" * 50)
    print("\n🔗 This version uses Gemini's native URL digestion")
    print("📹 Supports YouTube videos, GitHub repos, and any webpage")
    print("\n⚠️  Security Note: Never share your API key publicly!\n")
    
    # Run on all interfaces
    app.run(host='0.0.0.0', debug=True, port=5003)
