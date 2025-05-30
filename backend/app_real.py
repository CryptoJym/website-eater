import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from google import genai
from google.genai.types import Tool, GenerateContentConfig
from dotenv import load_dotenv
import json
from datetime import datetime
from urllib.parse import urlparse
import hashlib

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Google GenAI client
genai_client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    USER_ID = os.getenv('USER_ID', 'default_user')
    AGENT_ID = os.getenv('AGENT_ID', 'website_eater_agent')
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

# Simple in-memory storage
memories = []

def extract_content_with_gemini(url, options=None):
    """Use Google's URL Context tool to extract content from a URL"""
    try:
        # Create the URL context tool
        tools = [Tool(url_context={})]
        
        # Add Google Search if deep analysis is requested
        if options and options.get('deep_analysis'):
            tools.append(Tool(google_search={}))
        
        # Build the prompt based on options
        prompt_parts = [f"Extract and analyze the content from this URL: {url}"]
        
        if options:
            if options.get('extract_images'):
                prompt_parts.append("Include information about any images found.")
            if options.get('extract_metadata'):
                prompt_parts.append("Extract all metadata including author, publish date, and keywords.")
        
        prompt_parts.extend([
            "Provide a comprehensive analysis including:",
            "1. Title of the page",
            "2. Main content summary",
            "3. Key points or insights",
            "4. Content type (article, documentation, news, blog, etc.)",
            "5. Any relevant metadata"
        ])
        prompt = "\n".join(prompt_parts)
        
        # Generate content using Gemini
        response = genai_client.models.generate_content(
            model=Config.MODEL_ID,
            contents=prompt,
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
        )
        
        # Extract the response
        content = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                content += part.text
        
        # Get URL metadata
        url_metadata = None
        retrieval_status = "success"
        if hasattr(response.candidates[0], 'url_context_metadata'):
            url_metadata = response.candidates[0].url_context_metadata
            # Check retrieval status
            if url_metadata and hasattr(url_metadata, 'url_metadata'):
                for url_info in url_metadata.url_metadata:
                    if hasattr(url_info, 'url_retrieval_status'):
                        retrieval_status = str(url_info.url_retrieval_status)
                        break
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'content': content,
            'url_metadata': url_metadata,
            'extraction_status': 'success',
            'retrieval_status': retrieval_status
        }
        
    except Exception as e:
        print(f"Gemini extraction error: {e}")
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'content': '',
            'extraction_status': 'error',
            'error': str(e)
        }

def process_content(extracted_data, user_id):
    """Process extracted content and store in memory"""
    try:
        content = extracted_data.get('content', '')
        if not content:
            return {'status': 'error', 'error': 'No content extracted'}
        
        # Generate memory ID
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        memory_id = f"mem_{content_hash}_{len(memories)}"
        
        # Simple content type detection
        content_lower = content.lower()
        content_type = 'general'
        if any(word in content_lower for word in ['research', 'study', 'paper', 'journal']):
            content_type = 'research'
        elif any(word in content_lower for word in ['news', 'breaking', 'latest', 'update']):
            content_type = 'news'
        elif any(word in content_lower for word in ['documentation', 'api', 'guide', 'tutorial']):
            content_type = 'documentation'
        elif any(word in content_lower for word in ['blog', 'post', 'article', 'opinion']):
            content_type = 'blog'
        elif any(word in content_lower for word in ['product', 'pricing', 'service', 'feature']):
            content_type = 'product'
        
        # Extract title from content
        title = "Untitled"
        lines = content.split('\n')
        for line in lines:
            if line.strip() and ('title' in line.lower() or len(line.strip()) < 100):
                if ':' in line:
                    title = line.split(':', 1)[1].strip()
                else:
                    title = line.strip()
                if title and len(title) > 5:
                    break
        
        # Store in memory
        memory_entry = {
            'id': memory_id,
            'user_id': user_id,
            'title': title,
            'content': content,
            'metadata': {
                'url': extracted_data['url'],
                'domain': extracted_data['domain'],
                'timestamp': extracted_data['timestamp'],
                'content_type': content_type,
                'content_length': len(content),
                'extraction_status': extracted_data.get('extraction_status'),
                'retrieval_status': extracted_data.get('retrieval_status')
            }
        }
        memories.append(memory_entry)
        
        # Determine routes
        routes = []
        if content_type == 'research':
            routes = [{'destination': 'research_database'}, {'destination': 'knowledge_base'}]
        elif content_type == 'news':
            routes = [{'destination': 'news_feed'}, {'destination': 'knowledge_base'}]
        elif content_type == 'documentation':
            routes = [{'destination': 'docs_repository'}, {'destination': 'knowledge_base'}]
        elif content_type == 'blog':
            routes = [{'destination': 'blog_archive'}, {'destination': 'knowledge_base'}]
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
            'content_length': len(content)
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
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: #4285f4;
                color: white;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            
            .google-badge.active {
                background: #34a853;
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
                max-height: 300px;
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 Website Eater</h1>
                <p class="subtitle">Extract and analyze web content with AI-powered intelligence</p>
                <span class="google-badge active">✅ Google URL Context Active</span>
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
                    <div class="stat-value" id="quotaRemaining">1500</div>
                    <div class="stat-label">Daily Quota Remaining</div>
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
                    <div class="feature-title">Smart Content Analysis</div>
                    <div class="feature-desc">AI-powered extraction and classification</div>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            let processedCount = 0;
            let memoryCount = 0;
            let quotaUsed = 0;
            
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
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top: 1rem; color: #94a3b8;">🌐 Using Google URL Context to extract content...</p></div>';
                
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
                        quotaUsed++;
                        updateStats();
                        
                        // Get content preview
                        let contentPreview = data.content_preview || '';
                        if (contentPreview.length > 500) {
                            contentPreview = contentPreview.substring(0, 500) + '...';
                        }
                        
                        resultsDiv.innerHTML = `
                            <div class="success">
                                <span>✅</span>
                                <span>Successfully extracted content using Google URL Context!</span>
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
                                        <div class="meta-label">Content Length</div>
                                        <div class="meta-value">${data.content_length.toLocaleString()} chars</div>
                                    </div>
                                    <div class="meta-item">
                                        <div class="meta-label">Retrieval Status</div>
                                        <div class="meta-value">${data.retrieval_status || 'Success'}</div>
                                    </div>
                                </div>
                                
                                ${contentPreview ? `
                                <div class="content-preview">
                                    <h4>Content Preview</h4>
                                    <pre>${contentPreview}</pre>
                                </div>
                                ` : ''}
                                
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
                }
            }
            
            function updateStats() {
                document.getElementById('totalProcessed').textContent = processedCount;
                document.getElementById('totalMemories').textContent = memoryCount;
                document.getElementById('quotaRemaining').textContent = 1500 - quotaUsed;
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
    """Main API endpoint to process URLs using Gemini's URL Context tool"""
    try:
        data = request.json
        url = data.get('url')
        user_id = data.get('user_id', Config.USER_ID)
        options = data.get('options', {})
        
        if not url:
            return jsonify({'status': 'error', 'error': 'No URL provided'}), 400
        
        # Extract content using Gemini's URL Context tool
        extracted_data = extract_content_with_gemini(url, options)
        
        if extracted_data['extraction_status'] == 'error':
            return jsonify({
                'status': 'error', 
                'error': extracted_data.get('error', 'Failed to extract content')
            }), 400
        
        # Process and store content
        processing_result = process_content(extracted_data, user_id)
        
        if processing_result['status'] == 'error':
            return jsonify(processing_result), 400
        
        # Get content preview
        content_preview = extracted_data['content'][:500] if extracted_data['content'] else ''
        
        return jsonify({
            'status': 'success',
            'url': url,
            'title': processing_result['title'],
            'content_length': processing_result['content_length'],
            'content_type': processing_result['content_type'],
            'memory_id': processing_result['memory_id'],
            'routes': processing_result['routes'],
            'retrieval_status': extracted_data.get('retrieval_status'),
            'content_preview': content_preview
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

@app.route('/api/search', methods=['POST'])
def search_memories():
    """Search memories"""
    try:
        data = request.json
        query = data.get('query', '').lower()
        user_id = data.get('user_id', Config.USER_ID)
        
        # Simple search in memories
        results = []
        for memory in memories:
            if memory['user_id'] == user_id and query in memory['content'].lower():
                results.append(memory)
        
        return jsonify({
            'status': 'success',
            'results': results[:10]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Website Eater - Google URL Context Edition")
    print("=" * 50)
    print("✅ Google API Key: Configured")
    print(f"📍 Model: {Config.MODEL_ID}")
    print(f"📍 Starting server at http://localhost:5000")
    print("=" * 50)
    print("\n⚠️  Security Note: Never share your API key publicly!")
    print("Consider using environment variables in production.\n")
    
    app.run(debug=True, port=5000)
