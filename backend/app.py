import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from mem0 import Memory
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

# Initialize mem0
memory = Memory()

# Configuration
class Config:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    MEM0_API_KEY = os.getenv('MEM0_API_KEY')
    USER_ID = os.getenv('USER_ID', 'default_user')
    AGENT_ID = os.getenv('AGENT_ID', 'website_eater_agent')
    MODEL_ID = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-05-20')

# Import the agent
from agent import WebsiteEaterAgent

# Initialize agent
agent_config = {
    'genai_client': genai_client,
    'model_id': Config.MODEL_ID
}
agent = WebsiteEaterAgent(agent_config)

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
        
        prompt_parts.append("Provide a comprehensive summary including title, main content, key points, and any relevant metadata.")
        prompt = " ".join(prompt_parts)
        
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
        if hasattr(response.candidates[0], 'url_context_metadata'):
            url_metadata = response.candidates[0].url_context_metadata
        
        # Parse the response to extract structured data
        return {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'domain': urlparse(url).netloc,
            'content': content,
            'url_metadata': url_metadata,
            'extraction_status': 'success'
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
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 14px;
                margin-bottom: 30px;
            }
            .google-badge {
                display: inline-block;
                background: #4285f4;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-left: 10px;
            }
            .input-group {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            input[type="url"] {
                flex: 1;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                padding: 12px 24px;
                background: #4285f4;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background: #3367d6;
            }
            .options {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            .option {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            #results {
                margin-top: 30px;
            }
            .result-item {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                border-left: 4px solid #4285f4;
            }
            .loading {
                text-align: center;
                color: #666;
            }
            .error {
                color: #dc3545;
                padding: 10px;
                background: #f8d7da;
                border-radius: 5px;
            }
            .success {
                color: #155724;
                padding: 10px;
                background: #d4edda;
                border-radius: 5px;
            }
            .metadata {
                margin-top: 10px;
                padding: 10px;
                background: #e9ecef;
                border-radius: 5px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌐 Website Eater <span class="google-badge">Powered by Gemini</span></h1>
            <p class="subtitle">Using Google's URL Context tool to extract and analyze web content with AI memory</p>
            
            <div class="input-group">
                <input type="url" id="urlInput" placeholder="https://example.com" />
                <button onclick="processURL()">Extract Content</button>
            </div>
            
            <div class="options">
                <label class="option">
                    <input type="checkbox" id="deepAnalysis" checked>
                    Deep Analysis (with Google Search)
                </label>
                <label class="option">
                    <input type="checkbox" id="extractImages">
                    Extract Images Info
                </label>
                <label class="option">
                    <input type="checkbox" id="extractMetadata" checked>
                    Extract Metadata
                </label>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            async function processURL() {
                const url = document.getElementById('urlInput').value;
                const resultsDiv = document.getElementById('results');
                
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                const options = {
                    deep_analysis: document.getElementById('deepAnalysis').checked,
                    extract_images: document.getElementById('extractImages').checked,
                    extract_metadata: document.getElementById('extractMetadata').checked
                };
                
                resultsDiv.innerHTML = '<div class="loading">🔍 Using Gemini to extract content...</div>';
                
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
                        resultsDiv.innerHTML = `
                            <div class="success">✅ Successfully extracted content!</div>
                            <div class="result-item">
                                <h3>${data.title || 'Extracted Content'}</h3>
                                <p><strong>URL:</strong> ${data.url}</p>
                                <p><strong>Memory ID:</strong> ${data.memory_id}</p>
                                <p><strong>Content Length:</strong> ${data.content_length} characters</p>
                                <p><strong>Content Type:</strong> ${data.content_type}</p>
                                <p><strong>Routes:</strong> ${data.routes.map(r => r.destination).join(', ')}</p>
                                ${data.url_retrieval_status ? `
                                    <div class="metadata">
                                        <strong>Extraction Status:</strong> ${data.url_retrieval_status}
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    } else {
                        resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            // Allow Enter key to submit
            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') processURL();
            });
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
        
        # Process with agent
        processing_result = agent.process(extracted_data, user_id)
        
        # Extract title from content (Gemini should provide this in the response)
        title = "Untitled"
        if extracted_data['content']:
            # Simple title extraction from first line or heading
            lines = extracted_data['content'].split('\n')
            for line in lines:
                if line.strip():
                    title = line.strip()[:100]  # First non-empty line as title
                    break
        
        return jsonify({
            'status': 'success',
            'url': url,
            'title': title,
            'content_length': len(extracted_data['content']),
            'content_type': processing_result.get('content_type', 'general'),
            'memory_id': processing_result.get('memory_id'),
            'routes': processing_result.get('routes', []),
            'related_memories': processing_result.get('related_memories', []),
            'url_retrieval_status': extracted_data.get('url_metadata', {}).get('url_retrieval_status') if extracted_data.get('url_metadata') else None
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/memories/<user_id>', methods=['GET'])
def get_memories(user_id):
    """Get all memories for a user"""
    try:
        memories = memory.get_all(user_id=user_id)
        return jsonify({
            'status': 'success',
            'memories': memories
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_memories():
    """Search memories"""
    try:
        data = request.json
        query = data.get('query')
        user_id = data.get('user_id', Config.USER_ID)
        
        results = memory.search(query=query, user_id=user_id, limit=10)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_process():
    """Process multiple URLs in batch"""
    try:
        data = request.json
        urls = data.get('urls', [])
        user_id = data.get('user_id', Config.USER_ID)
        options = data.get('options', {})
        
        if not urls:
            return jsonify({'status': 'error', 'error': 'No URLs provided'}), 400
        
        # Limit to 20 URLs per batch (Gemini's limit)
        if len(urls) > 20:
            return jsonify({
                'status': 'error', 
                'error': 'Maximum 20 URLs per batch (Gemini API limit)'
            }), 400
        
        results = []
        for url in urls:
            try:
                extracted_data = extract_content_with_gemini(url, options)
                processing_result = agent.process(extracted_data, user_id)
                results.append({
                    'url': url,
                    'status': 'success',
                    'memory_id': processing_result.get('memory_id')
                })
            except Exception as e:
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
