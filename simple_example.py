"""
Simple example of using Google's URL Context tool directly
This demonstrates the core functionality without the full Website Eater system
"""

import os
from google import genai
from google.genai.types import Tool, GenerateContentConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

def extract_content_from_url(url: str, use_search: bool = False):
    """
    Extract content from a URL using Google's URL Context tool
    
    Args:
        url: The URL to extract content from
        use_search: Whether to also use Google Search for additional context
    """
    
    # Set up tools
    tools = [Tool(url_context={})]
    
    if use_search:
        tools.append(Tool(google_search={}))
    
    # Create the prompt
    prompt = f"""
    Extract and analyze the content from this URL: {url}
    
    Please provide:
    1. Title of the page
    2. Main topic/theme
    3. Key points or summary
    4. Any important metadata (author, date, etc.)
    5. Content type (article, documentation, product page, etc.)
    """
    
    try:
        # Generate content using Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
        )
        
        # Extract the response text
        result_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                result_text += part.text
        
        # Check if URL was successfully retrieved
        url_metadata = None
        if hasattr(response.candidates[0], 'url_context_metadata'):
            url_metadata = response.candidates[0].url_context_metadata
            print("\n📊 URL Retrieval Metadata:")
            for url_info in url_metadata.url_metadata:
                print(f"  - URL: {url_info.retrieved_url}")
                print(f"    Status: {url_info.url_retrieval_status}")
        
        return result_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def compare_urls(url1: str, url2: str):
    """
    Compare content from two URLs
    """
    prompt = f"""
    Compare the content from these two URLs:
    URL 1: {url1}
    URL 2: {url2}
    
    Please provide:
    1. Main similarities between the content
    2. Key differences
    3. Which source seems more comprehensive or authoritative
    4. Any contradicting information between them
    """
    
    tools = [Tool(url_context={})]
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
        )
        
        result_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                result_text += part.text
        
        return result_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def extract_with_search_context(topic: str, url: str = None):
    """
    Use Google Search + URL Context for comprehensive analysis
    """
    if url:
        prompt = f"""
        Research the topic "{topic}" and analyze this specific URL: {url}
        
        Use Google Search to find additional context about {topic}, then analyze 
        how the content at {url} relates to the broader topic.
        
        Provide:
        1. Overview of the topic from search results
        2. How the specific URL's content fits into the broader context
        3. Any unique insights from the URL not found in general search
        4. Recommendations for further reading
        """
    else:
        prompt = f"""
        Research the topic "{topic}" using Google Search.
        
        Find the most relevant and authoritative sources, then provide:
        1. Comprehensive overview of the topic
        2. Key sources found
        3. Latest developments or news
        4. Different perspectives or viewpoints
        """
    
    tools = [Tool(url_context={}), Tool(google_search={})]
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
            )
        )
        
        result_text = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                result_text += part.text
        
        return result_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Example usage
if __name__ == "__main__":
    print("🌐 Google URL Context Tool Examples\n")
    
    # Example 1: Extract content from a single URL
    print("=" * 50)
    print("Example 1: Extract content from a URL")
    print("=" * 50)
    
    url = "https://blog.google/technology/ai/google-gemini-update-december-2024/"
    print(f"\nExtracting content from: {url}\n")
    
    content = extract_content_from_url(url)
    if content:
        print(content)
    
    # Example 2: Compare two URLs
    print("\n" + "=" * 50)
    print("Example 2: Compare content from two URLs")
    print("=" * 50)
    
    url1 = "https://openai.com/research/gpt-4"
    url2 = "https://blog.google/technology/ai/google-gemini-ai/"
    
    print(f"\nComparing:")
    print(f"  URL 1: {url1}")
    print(f"  URL 2: {url2}\n")
    
    comparison = compare_urls(url1, url2)
    if comparison:
        print(comparison)
    
    # Example 3: Research with Search + URL Context
    print("\n" + "=" * 50)
    print("Example 3: Research with Google Search + URL Context")
    print("=" * 50)
    
    topic = "large language models"
    research = extract_with_search_context(topic)
    if research:
        print(f"\nResearch on '{topic}':\n")
        print(research)
