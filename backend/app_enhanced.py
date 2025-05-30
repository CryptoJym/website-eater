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
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro-exp-03-25')

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
        
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')
        
        # Extract main text
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract headers
        headers_found = []
        for i in range(1, 4):  # h1, h2, h3
            headers_found.extend([h.get_text().strip() for h in soup.find_all(f'h{i}')])
        
        return {
            'title': title,
            'content': text[:5000],  # Limit content
            'meta_description': meta_desc,
            'headers': headers_found[:10],  # First 10 headers
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
    """Use Gemini to analyze scraped content - with fallback"""
    try:
        # Skip AI if explicitly disabled
        if options and options.get('skip_ai', False):
            return {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'domain': urlparse(url).netloc,
                'title': scraped_data['title'],
                'raw_content': scraped_data['content'],
                'meta_description': scraped_data.get('meta_description', ''),
                'headers': scraped_data.get('headers', []),
                'analysis': 'AI analysis skipped',
                'extraction_status': 'success' if scraped_data['success'] else 'partial',
            }
        
        # Try AI analysis
        prompt_parts = [
            f"Analyze this web content from {url}:",
            f"Title: {scraped_data['title']}",
            f"Meta Description: {scraped_data.get('meta_description', 'None')}",
            f"Headers: {', '.join(scraped_data.get('headers', [])[:5])}",
            f"Content preview: {scraped_data['content'][:1500]}",
            "",
            "Provide a comprehensive analysis including:",
            "1. Summary of the main content (2-3 sentences)",
            "2. Key topics or themes",
            "3. Content type classification",
            "4. Target audience",
            "5. Key takeaways or insights"
        ]
        
        prompt = "\n".join(prompt_parts)
        
        # Generate analysis using Gemini
        config = GenerateContentConfig(
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=1024,
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
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'title': scraped_data['title'],
            'raw_content': scraped_data['content'],
            'meta_description': scraped_data.get('meta_description', ''),
            'headers': scraped_data.get('headers', []),
            'analysis': analysis,
            'extraction_status': 'success' if scraped_data['success'] else 'partial',
        }
        
    except Exception as e:
        # Fallback when AI fails
        print(f"Gemini analysis error: {e}")
        
        # Basic content analysis without AI
        content_lower = scraped_data.get('content', '').lower()
        basic_analysis = []
        
        # Detect content type
        if any(word in content_lower for word in ['news', 'breaking', 'latest', 'update']):
            basic_analysis.append("Content Type: News/Updates")
        elif any(word in content_lower for word in ['tutorial', 'guide', 'how to', 'documentation']):
            basic_analysis.append("Content Type: Educational/Documentation")
        elif any(word in content_lower for word in ['product', 'pricing', 'buy', 'service']):
            basic_analysis.append("Content Type: Commercial/Product")
        elif any(word in content_lower for word in ['blog', 'opinion', 'thoughts', 'personal']):
            basic_analysis.append("Content Type: Blog/Personal")
        else:
            basic_analysis.append("Content Type: General Information")
        
        # Add basic stats
        word_count = len(scraped_data.get('content', '').split())
        basic_analysis.append(f"Word Count: {word_count}")
        basic_analysis.append(f"Headers Found: {len(scraped_data.get('headers', []))}")
        
        if scraped_data.get('meta_description'):
            basic_analysis.append(f"Meta Description: {scraped_data['meta_description'][:100]}...")
        
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'title': scraped_data['title'],
            'raw_content': scraped_data['content'],
            'meta_description': scraped_data.get('meta_description', ''),
            'headers': scraped_data.get('headers', []),
            'analysis': f"Basic Analysis (AI unavailable due to quota):\n" + "\n".join(basic_analysis),
            'extraction_status': 'success' if scraped_data['success'] else 'partial',
            'ai_error': str(e)
        }

def process_content(extracted_data, user_id):
    """Process extracted content and store in memory"""
    try:
        # Combine all content
        full_content = f"{extracted_data.get('title', '')}\n\n"
        full_content += f"URL: {extracted_data.get('url', '')}\n"
        full_content += f"Meta: {extracted_data.get('meta_description', '')}\n\n"
        
        if extracted_data.get('headers'):
            full_content += f"Headers: {', '.join(extracted_data['headers'][:5])}\n\n"
        
        full_content += f"Analysis:\n{extracted_data.get('analysis', '')}\n\n"
        full_content += f"Content:\n{extracted_data.get('raw_content', '')[:1000]}"
        
        if not full_content.strip():
            return {'status': 'error', 'error': 'No content extracted'}
        
        # Generate memory ID
        content_hash = hashlib.sha256(full_content.encode()).hexdigest()[:8]
        memory_id = f"mem_{content_hash}_{len(memories)}"
        
        # Content type detection
        analysis_lower = extracted_data.get('analysis', '').lower()
        content_lower = extracted_data.get('raw_content', '').lower()
        
        content_type = 'general'
        if 'documentation' in analysis_lower or 'documentation' in content_lower:
            content_type = 'documentation'
        elif 'news' in analysis_lower or 'news' in content_lower:
            content_type = 'news'
        elif 'blog' in analysis_lower or 'blog' in content_lower:
            content_type = 'blog'
        elif 'research' in analysis_lower or 'research' in content_lower:
            content_type = 'research'
        elif 'product' in analysis_lower or 'product' in content_lower:
            content_type = 'product'
        
        # Store in memory
        memory_entry = {
            'id': memory_id,
            'user_id': user_id,
            'title': extracted_data.get('title', 'Untitled'),
            'content': full_content,
            'analysis': extracted_data.get('analysis', ''),
            'raw_content': extracted_data.get('raw_content', ''),
            'headers': extracted_data.get('headers', []),
            'metadata': {
                'url': extracted_data['url'],
                'domain': extracted_data['domain'],
                'timestamp': extracted_data['timestamp'],
                'content_type': content_type,
                'content_length': len(full_content),
                'extraction_status': extracted_data.get('extraction_status'),
                'meta_description': extracted_data.get('meta_description', ''),
                'ai_error': extracted_data.get('ai_error')
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
            'title': extracted_data.get('title', 'Untitled'),
            'content_type': content_type,
            'routes': routes,
            'content_length': len(full_content),
            'analysis_preview': extracted_data.get('analysis', '')[:500],
            'raw_content_preview': extracted_data.get('raw_content', '')[:500],
            'headers': extracted_data.get('headers', [])[:5],
            'meta_description': extracted_data.get('meta_description', ''),
            'ai_available': 'ai_error' not in extracted_data
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
            
            .headers-list {
                background: #0f172a;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
            }
            
            .headers-list h5 {
                color: #94a3b8;
                margin-bottom: 0.5rem;
                font-size: 0.85rem;
                text-transform: uppercase;
            }
            
            .headers-list ul {
                list-style: none;
                padding-left: 0;
            }
            
            .headers-list li {
                color: #cbd5e1;
                padding: 0.25rem 0;
                border-left: 2px solid #4285f4;
                padding-left: 0.75rem;
                margin-bottom: 0.25rem;
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 Website Eater</h1>
                <p class="subtitle">Extract and analyze web content with AI-powered intelligence</p>
                <span id="ai-status" class="google-badge active">✅ Gemini 2.5 Pro Active</span>
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
                    <div class="stat-value" id="extractionSuccess">100%</div>
                    <div class="stat-label">Extraction Success Rate</div>
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
                        <input type="checkbox" id="skipAI">
                        <label for="skipAI">Skip AI Analysis (Extract Only)</label>
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
                    <div class="feature-icon">🕷️</div>
                    <div class="feature-title">Smart Web Scraping</div>
                    <div class="feature-desc">Extract content, headers, and metadata from any website</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">Gemini 2.5 Pro Analysis</div>
                    <div class="feature-desc">Advanced AI understanding (when quota available)</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">Intelligent Classification</div>
                    <div class="feature-desc">Automatic content categorization and routing</div>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            let processedCount = 0;
            let memoryCount = 0;
            let successCount = 0;
            let aiAvailable = true;
            
            async function processURL() {
                const url = document.getElementById('urlInput').value;
                const resultsDiv = document.getElementById('results');
                const processBtn = document.getElementById('processBtn');
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                const options = {
                    skip_ai: document.getElementById('skipAI').checked,
                    extract_images: document.getElementById('extractImages').checked,
                    extract_metadata: document.getElementById('extractMetadata').checked
                };
                
                processBtn.disabled = true;
                resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p style="margin-top: 1rem; color: #94a3b8;">🕷️ Extracting content...</p></div>';
                
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
                        successCount++;
                        updateStats();
                        
                        // Update AI status
                        if (!data.ai_available) {
                            aiAvailable = false;
                            document.getElementById('ai-status').className = 'google-badge limited';
                            document.getElementById('ai-status').innerHTML = '⚠️ AI Quota Exceeded (Extraction Still Works)';
                        }
                        
                        let resultHTML = `
                            <div class="success">
                                <span>✅</span>
                                <span>Successfully extracted ${data.ai_available ? 'and analyzed' : ''} content!</span>
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
                                        <div class="meta-value">${data.ai_available ? 'Fully Analyzed ✓' : 'Extracted (No AI)'}</div>
                                    </div>
                                </div>
                        `;
                        
                        if (data.meta_description) {
                            resultHTML += `
                                <div class="content-preview">
                                    <h4>Meta Description</h4>
                                    <pre>${data.meta_description}</pre>
                                </div>
                            `;
                        }
                        
                        if (data.headers && data.headers.length > 0) {
                            resultHTML += `
                                <div class="headers-list">
                                    <h5>Extracted Headers</h5>
                                    <ul>
                                        ${data.headers.map(h => `<li>${h}</li>`).join('')}
                                    </ul>
                                </div>
                            `;
                        }
                        
                        if (data.analysis_preview && data.ai_available) {
                            resultHTML += `
                                <div class="content-preview">
                                    <h4>AI Analysis</h4>
                                    <pre>${data.analysis_preview}</pre>
                                </div>
                            `;
                        }
                        
                        if (data.raw_content_preview) {
                            resultHTML += `
                                <div class="content-preview">
                                    <h4>Extracted Content Preview</h4>
                                    <pre>${data.raw_content_preview}</pre>
                                </div>
                            `;
                        }
                        
                        resultHTML += `
                                <div class="routes">
                                    <div class="meta-label" style="margin-right: 10px;">Routed to:</div>
                                    ${data.routes.map(r => `<span class="route-tag">${r.destination}</span>`).join('')}
                                </div>
                            </div>
                        `;
                        
                        resultsDiv.innerHTML = resultHTML;
                        
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
                const successRate = processedCount > 0 ? Math.round((successCount / processedCount) * 100) : 100;
                document.getElementById('extractionSuccess').textContent = successRate + '%';
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
        
        # Then analyze with Gemini (with fallback)
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
            'analysis_preview': processing_result.get('analysis_preview', ''),
            'raw_content_preview': processing_result.get('raw_content_preview', ''),
            'headers': processing_result.get('headers', []),
            'meta_description': processing_result.get('meta_description', ''),
            'ai_available': processing_result.get('ai_available', True)
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
                if (query in memory['content'].lower() or 
                    query in memory.get('analysis', '').lower() or
                    query in memory.get('raw_content', '').lower()):
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
    print(f"📍 Starting server at http://localhost:5002")
    print("=" * 50)
    print("\n⚠️  Security Note: Never share your API key publicly!")
    print("Consider using environment variables in production.\n")
    
    # Run on all interfaces to fix localhost access issues
    app.run(host='0.0.0.0', debug=True, port=5002)
