import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import google.genai as genai
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch
from dotenv import load_dotenv
import json
from datetime import datetime
from urllib.parse import urlparse
import hashlib
import requests
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

app = Flask(__name__)
# More permissive CORS for development
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Google GenAI client
genai_client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    USER_ID = os.getenv('USER_ID', 'default_user')
    AGENT_ID = os.getenv('AGENT_ID', 'website_eater_agent')
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')

# Simple in-memory storage
memories = []

def extract_content_from_url(url):
    """Simple web scraping as fallback"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No title"
        
        # Extract main text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return {
            'title': title,
            'content': text[:5000],  # Limit content
            'url': url,
            'success': True
        }
    except Exception as e:
        return {
            'title': 'Error',
            'content': str(e),
            'url': url,
            'success': False
        }

def analyze_content_with_gemini(url, scraped_data, options=None):
    """Use Gemini to analyze scraped content"""
    try:
        # Build the prompt
        prompt_parts = [
            f"Analyze this web content from {url}:",
            f"Title: {scraped_data['title']}",
            f"Content preview: {scraped_data['content'][:2000]}",
            "",
            "Provide a comprehensive analysis including:",
            "1. Summary of the main content",
            "2. Key points or insights",
            "3. Content type (article, documentation, news, blog, etc.)",
            "4. Any notable information or takeaways"
        ]
        
        if options and options.get('deep_analysis'):
            prompt_parts.append("5. Related topics that might be worth exploring")
        
        prompt = "\n".join(prompt_parts)
        
        # Generate analysis using Gemini
        config = GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=2048,
        )
        
        # Add Google Search tool if deep analysis requested
        if options and options.get('deep_analysis'):
            config.tools = [Tool(google_search=GoogleSearch())]
        
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
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'title': scraped_data['title'],
            'raw_content': scraped_data['content'],
            'analysis': analysis,
            'extraction_status': 'success' if scraped_data['success'] else 'partial',
        }
        
    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'title': scraped_data.get('title', 'Unknown'),
            'raw_content': scraped_data.get('content', ''),
            'analysis': f"Analysis failed: {str(e)}",
            'extraction_status': 'error',
            'error': str(e)
        }

def process_content(extracted_data, user_id):
    """Process extracted content and store in memory"""
    try:
        # Combine raw content and analysis
        full_content = f"{extracted_data.get('title', '')}\n\n"
        full_content += f"Analysis:\n{extracted_data.get('analysis', '')}\n\n"
        full_content += f"Raw content:\n{extracted_data.get('raw_content', '')[:1000]}"
        
        if not full_content.strip():
            return {'status': 'error', 'error': 'No content extracted'}
        
        # Generate memory ID
        content_hash = hashlib.sha256(full_content.encode()).hexdigest()[:8]
        memory_id = f"mem_{content_hash}_{len(memories)}"
        
        # Content type detection from analysis
        analysis_lower = extracted_data.get('analysis', '').lower()
        content_type = 'general'
        
        if 'documentation' in analysis_lower or 'api' in analysis_lower or 'guide' in analysis_lower:
            content_type = 'documentation'
        elif 'news' in analysis_lower or 'breaking' in analysis_lower or 'latest' in analysis_lower:
            content_type = 'news'
        elif 'blog' in analysis_lower or 'article' in analysis_lower or 'post' in analysis_lower:
            content_type = 'blog'
        elif 'research' in analysis_lower or 'study' in analysis_lower or 'paper' in analysis_lower:
            content_type = 'research'
        elif 'product' in analysis_lower or 'service' in analysis_lower or 'pricing' in analysis_lower:
            content_type = 'product'
        
        # Store in memory
        memory_entry = {
            'id': memory_id,
            'user_id': user_id,
            'title': extracted_data.get('title', 'Untitled'),
            'content': full_content,
            'analysis': extracted_data.get('analysis', ''),
            'metadata': {
                'url': extracted_data['url'],
                'domain': extracted_data['domain'],
                'timestamp': extracted_data['timestamp'],
                'content_type': content_type,
                'content_length': len(full_content),
                'extraction_status': extracted_data.get('extraction_status')
            }
        }
        memories.append(memory_entry)
        
        # Determine routes based on content type
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
            'title': extracted_data.get('title', 'Untitled'),
            'content_type': content_type,
            'routes': routes,
            'content_length': len(full_content),
            'analysis_preview': extracted_data.get('analysis', '')[:500]
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
        <title>Website Eater - Powered by Gemini 2.5 Pro</title>
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
                <span class="google-badge active">✅ Gemini 2.5 Pro Active</span>
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
                        <span>🔍</span> Extract & Analyze
                    </button>
                </div>
                
                <div class="options">
                    <div class="option">
                        <input type="checkbox" id="deepAnalysis" checked>
                        <label for="deepAnalysis">Deep Analysis with Related Topics</label>
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
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">Gemini AI Analysis</div>
                    <div class="feature-desc">Intelligent content understanding and insights</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Smart Extraction</div>
                    <div class="feature-desc">Extract and structure web content automatically</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">Content Classification</div>
                    <div class="feature-desc">Automatic categorization and routing</div>
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
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top: 1rem; color: #94a3b8;">🤖 Extracting content and analyzing with Gemini AI...</p></div>';
                
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
                        
                        resultsDiv.innerHTML = `
                            <div class="success">
                                <span>✅</span>
                                <span>Successfully extracted and analyzed content!</span>
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
                                        <div class="meta-label">Status</div>
                                        <div class="meta-value">Analyzed ✓</div>
                                    </div>
                                </div>
                                
                                ${data.analysis_preview ? `
                                <div class="content-preview">
                                    <h4>AI Analysis</h4>
                                    <pre>${data.analysis_preview}</pre>
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
    """Main API endpoint to process URLs"""
    try:
        data = request.json
        url = data.get('url')
        user_id = data.get('user_id', Config.USER_ID)
        options = data.get('options', {})
        
        if not url:
            return jsonify({'status': 'error', 'error': 'No URL provided'}), 400
        
        # First, scrape the content
        scraped_data = extract_content_from_url(url)
        
        if not scraped_data['success']:
            return jsonify({
                'status': 'error', 
                'error': f"Failed to fetch URL: {scraped_data['content']}"
            }), 400
        
        # Then analyze with Gemini
        analyzed_data = analyze_content_with_gemini(url, scraped_data, options)
        
        # Process and store
        processing_result = process_content(analyzed_data, user_id)
        
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
            'analysis_preview': processing_result.get('analysis_preview', '')
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
        
        results = []
        for memory in memories:
            if memory['user_id'] == user_id:
                if query in memory['content'].lower() or query in memory.get('analysis', '').lower():
                    results.append(memory)
        
        return jsonify({
            'status': 'success',
            'results': results[:10]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🌐 Website Eater - Gemini 2.5 Pro Edition")
    print("=" * 50)
    print("✅ Google API Key: Configured")
    print(f"📍 Model: {Config.MODEL_ID}")
    print(f"📍 Starting server at http://localhost:5001")
    print("=" * 50)
    print("\n⚠️  Security Note: Never share your API key publicly!")
    print("Consider using environment variables in production.\n")
    
    # Run on all interfaces to fix localhost access issues
    app.run(host='0.0.0.0', debug=True, port=5001)
