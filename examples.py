"""
Example usage of the Website Eater API
"""
import requests
import json
from typing import Dict, List, Any

class WebsiteEaterClient:
    def __init__(self, base_url: str = "http://localhost:5000", user_id: str = "default_user"):
        self.base_url = base_url
        self.user_id = user_id
        self.session = requests.Session()
    
    def process_url(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a URL and store in memory"""
        payload = {
            "url": url,
            "user_id": self.user_id
        }
        
        if options:
            payload["options"] = options
        
        response = self.session.post(
            f"{self.base_url}/api/process",
            json=payload
        )
        
        return response.json()
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through stored memories"""
        response = self.session.post(
            f"{self.base_url}/api/search",
            json={
                "query": query,
                "user_id": self.user_id,
                "limit": limit
            }
        )
        
        data = response.json()
        return data.get("results", []) if data.get("status") == "success" else []
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all memories for the user"""
        response = self.session.get(
            f"{self.base_url}/api/memories/{self.user_id}"
        )
        
        data = response.json()
        return data.get("memories", []) if data.get("status") == "success" else []
    
    def batch_process_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple URLs"""
        results = []
        
        for url in urls:
            print(f"Processing: {url}")
            result = self.process_url(url)
            results.append(result)
            
            if result.get("status") == "success":
                print(f"✅ Success: {result.get('title')}")
            else:
                print(f"❌ Failed: {result.get('error')}")
        
        return results


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = WebsiteEaterClient()
    
    # Example 1: Process a single URL
    print("Example 1: Processing a single URL")
    print("-" * 40)
    
    result = client.process_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
    
    if result.get("status") == "success":
        print(f"Title: {result.get('title')}")
        print(f"Content Length: {result.get('content_length')} characters")
        print(f"Content Type: {result.get('content_type', 'general')}")
        print(f"Memory ID: {result.get('memory_id')}")
        print(f"Routes: {[r['destination'] for r in result.get('routes', [])]}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\n")
    
    # Example 2: Batch process multiple URLs
    print("Example 2: Batch processing")
    print("-" * 40)
    
    urls = [
        "https://openai.com/research/gpt-4",
        "https://github.com/anthropics/anthropic-sdk-python",
        "https://docs.python.org/3/tutorial/index.html"
    ]
    
    batch_results = client.batch_process_urls(urls)
    
    print("\n")
    
    # Example 3: Search memories
    print("Example 3: Searching memories")
    print("-" * 40)
    
    search_results = client.search_memories("artificial intelligence", limit=5)
    
    for i, memory in enumerate(search_results, 1):
        print(f"{i}. {memory.get('content', '')[:100]}...")
    
    print("\n")
    
    # Example 4: Advanced usage with options
    print("Example 4: Advanced processing with options")
    print("-" * 40)
    
    options = {
        "deep_analysis": True,
        "extract_images": True,
        "follow_links": False
    }
    
    advanced_result = client.process_url(
        "https://www.nature.com/articles/s41586-021-03819-2",
        options=options
    )
    
    if advanced_result.get("status") == "success":
        print(f"Processed with advanced options: {advanced_result.get('title')}")
        
        # Access metadata if available
        metadata = advanced_result.get("metadata", {})
        if metadata:
            print(f"Authors: {metadata.get('authors', 'N/A')}")
            print(f"Keywords: {metadata.get('keywords', [])}")
    
    print("\n")
    
    # Example 5: Get all memories and analyze
    print("Example 5: Memory analysis")
    print("-" * 40)
    
    all_memories = client.get_all_memories()
    print(f"Total memories stored: {len(all_memories)}")
    
    # Analyze content types
    content_types = {}
    for memory in all_memories:
        ct = memory.get("metadata", {}).get("content_type", "general")
        content_types[ct] = content_types.get(ct, 0) + 1
    
    print("Content type distribution:")
    for ct, count in content_types.items():
        print(f"  {ct}: {count}")
