#!/usr/bin/env python3
"""
Website Eater CLI - Command line interface for the Google URL Context-powered Website Eater
"""
import argparse
import json
import sys
import requests
from typing import Optional

class WebsiteEaterClient:
    def __init__(self, base_url: str = "http://localhost:5000", user_id: str = "default_user"):
        self.base_url = base_url
        self.user_id = user_id
        self.session = requests.Session()
    
    def process_url(self, url: str, options: dict = None) -> dict:
        """Process a URL using Google's URL Context tool"""
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
    
    def batch_process(self, urls: list) -> dict:
        """Process multiple URLs (max 20 due to Gemini limit)"""
        response = self.session.post(
            f"{self.base_url}/api/batch",
            json={
                "urls": urls,
                "user_id": self.user_id
            }
        )
        
        return response.json()
    
    def search_memories(self, query: str, limit: int = 10) -> list:
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
    
    def get_all_memories(self) -> list:
        """Get all memories for the user"""
        response = self.session.get(
            f"{self.base_url}/api/memories/{self.user_id}"
        )
        
        data = response.json()
        return data.get("memories", []) if data.get("status") == "success" else []

def main():
    parser = argparse.ArgumentParser(
        description='Website Eater CLI - AI-powered web content extraction using Google URL Context',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single URL
  website-eater process https://example.com

  # Process with options
  website-eater process https://example.com --deep-analysis --extract-images

  # Search memories
  website-eater search "machine learning"

  # Process multiple URLs from file (max 20)
  website-eater batch urls.txt

  # Get memory statistics
  website-eater stats

Note: This tool uses Google's URL Context API which has a limit of 20 URLs per request.
Daily quotas: 1500 requests/day via API, 100 requests/day in Google AI Studio.
        """
    )
    
    parser.add_argument('--api-url', default='http://localhost:5000',
                        help='API base URL (default: http://localhost:5000)')
    parser.add_argument('--user-id', default='default_user',
                        help='User ID for memory storage')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process a URL')
    process_parser.add_argument('url', help='URL to process')
    process_parser.add_argument('--deep-analysis', action='store_true',
                                help='Enable deep analysis with Google Search')
    process_parser.add_argument('--extract-images', action='store_true',
                                help='Extract images information')
    process_parser.add_argument('--extract-metadata', action='store_true',
                                help='Extract metadata (default: true)', default=True)
    process_parser.add_argument('--json', action='store_true',
                                help='Output raw JSON response')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search memories')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10,
                               help='Maximum results (default: 10)')
    search_parser.add_argument('--json', action='store_true',
                               help='Output raw JSON response')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process URLs from file (max 20)')
    batch_parser.add_argument('file', help='File containing URLs (one per line)')
    batch_parser.add_argument('--output', help='Output results to file')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show memory statistics')
    stats_parser.add_argument('--json', action='store_true',
                              help='Output raw JSON response')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all memories')
    list_parser.add_argument('--limit', type=int, default=20,
                             help='Maximum results (default: 20)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize client
    client = WebsiteEaterClient(base_url=args.api_url, user_id=args.user_id)
    
    try:
        if args.command == 'process':
            process_url_command(client, args)
        elif args.command == 'search':
            search_memories_command(client, args)
        elif args.command == 'batch':
            batch_process_command(client, args)
        elif args.command == 'stats':
            show_stats_command(client, args)
        elif args.command == 'list':
            list_memories_command(client, args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def process_url_command(client: WebsiteEaterClient, args):
    """Process a single URL"""
    options = {
        'deep_analysis': args.deep_analysis,
        'extract_images': args.extract_images,
        'extract_metadata': args.extract_metadata
    }
    
    print(f"🔍 Processing with Google URL Context: {args.url}")
    result = client.process_url(args.url, options)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get('status') == 'success':
            print(f"✅ Success!")
            print(f"Title: {result.get('title', 'Untitled')}")
            print(f"Content Type: {result.get('content_type', 'general')}")
            print(f"Content Length: {result.get('content_length')} characters")
            print(f"Memory ID: {result.get('memory_id')}")
            print(f"Routes: {', '.join(r['destination'] for r in result.get('routes', []))}")
            
            if result.get('url_retrieval_status'):
                print(f"Extraction Status: {result['url_retrieval_status']}")
            
            # Show related memories if any
            related = result.get('related_memories', [])
            if related:
                print(f"\nRelated memories found: {len(related)}")
        else:
            print(f"❌ Failed: {result.get('error')}")

def search_memories_command(client: WebsiteEaterClient, args):
    """Search through memories"""
    print(f"🔍 Searching for: {args.query}")
    results = client.search_memories(args.query, limit=args.limit)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if results:
            print(f"\nFound {len(results)} results:\n")
            for i, memory in enumerate(results, 1):
                content = memory.get('content', '')
                preview = content[:150] + '...' if len(content) > 150 else content
                print(f"{i}. {preview}")
                print(f"   ID: {memory.get('id', 'N/A')}")
                print()
        else:
            print("No results found.")

def batch_process_command(client: WebsiteEaterClient, args):
    """Process multiple URLs from file"""
    try:
        with open(args.file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
    
    if len(urls) > 20:
        print(f"Warning: Gemini URL Context tool has a limit of 20 URLs per request.")
        print(f"Processing first 20 URLs out of {len(urls)}")
        urls = urls[:20]
    
    print(f"🔍 Processing {len(urls)} URLs using Google URL Context")
    result = client.batch_process(urls)
    
    if result.get('status') == 'success':
        results = result.get('results', [])
        
        for i, res in enumerate(results, 1):
            if res['status'] == 'success':
                print(f"✅ [{i}/{len(results)}] {res['url']}")
            else:
                print(f"❌ [{i}/{len(results)}] {res['url']}: {res.get('error')}")
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        
        # Summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"\nSummary: {success_count}/{len(results)} URLs processed successfully")
    else:
        print(f"❌ Batch processing failed: {result.get('error')}")

def show_stats_command(client: WebsiteEaterClient, args):
    """Show memory statistics"""
    memories = client.get_all_memories()
    
    if args.json:
        stats = {
            'total_memories': len(memories),
            'content_types': {},
            'domains': {}
        }
        
        for memory in memories:
            metadata = memory.get('metadata', {})
            
            # Count content types
            ct = metadata.get('content_type', 'general')
            stats['content_types'][ct] = stats['content_types'].get(ct, 0) + 1
            
            # Count domains
            domain = metadata.get('domain', 'unknown')
            stats['domains'][domain] = stats['domains'].get(domain, 0) + 1
        
        print(json.dumps(stats, indent=2))
    else:
        print("📊 Memory Statistics")
        print("=" * 40)
        print(f"Total memories: {len(memories)}")
        
        # Content type analysis
        content_types = {}
        domains = {}
        
        for memory in memories:
            metadata = memory.get('metadata', {})
            
            ct = metadata.get('content_type', 'general')
            content_types[ct] = content_types.get(ct, 0) + 1
            
            domain = metadata.get('domain', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1
        
        print("\n📑 Content Types:")
        for ct, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ct}: {count}")
        
        print("\n🌐 Top Domains:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {domain}: {count}")

def list_memories_command(client: WebsiteEaterClient, args):
    """List all memories"""
    memories = client.get_all_memories()
    
    if not memories:
        print("No memories found.")
        return
    
    # Limit results
    memories = memories[:args.limit]
    
    print(f"📚 Showing {len(memories)} memories:\n")
    
    for i, memory in enumerate(memories, 1):
        metadata = memory.get('metadata', {})
        content = memory.get('content', '')
        
        print(f"{i}. {metadata.get('title', 'Untitled')}")
        print(f"   URL: {metadata.get('url', 'N/A')}")
        print(f"   Type: {metadata.get('content_type', 'general')}")
        print(f"   Date: {metadata.get('timestamp', 'N/A')}")
        print(f"   Preview: {content[:100]}...")
        print()

if __name__ == '__main__':
    main()
