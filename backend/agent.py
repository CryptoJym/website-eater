"""
Advanced agent processor with mem0 integration and content routing
Adapted for Google's URL Context tool
"""
import os
from typing import Dict, List, Any
from datetime import datetime
import json
from mem0 import Memory
import hashlib
import re

class WebsiteEaterAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory = Memory()
        self.genai_client = config.get('genai_client')
        self.model_id = config.get('model_id', 'gemini-2.5-flash-preview-05-20')
        
        # Content type handlers
        self.content_handlers = {
            'research': self.handle_research_content,
            'news': self.handle_news_content,
            'documentation': self.handle_documentation_content,
            'blog': self.handle_blog_content,
            'product': self.handle_product_content,
            'general': self.handle_general_content
        }
        
        # Routing rules
        self.routing_rules = {
            'research': {
                'keywords': ['research', 'study', 'paper', 'journal', 'findings', 'methodology', 'academic'],
                'destinations': ['research_database', 'knowledge_base']
            },
            'news': {
                'keywords': ['news', 'breaking', 'latest', 'update', 'announcement', 'report'],
                'destinations': ['news_feed', 'knowledge_base']
            },
            'documentation': {
                'keywords': ['documentation', 'api', 'guide', 'tutorial', 'reference', 'docs', 'sdk'],
                'destinations': ['docs_repository', 'knowledge_base']
            },
            'blog': {
                'keywords': ['blog', 'post', 'article', 'opinion', 'thoughts', 'review'],
                'destinations': ['blog_archive', 'knowledge_base']
            },
            'product': {
                'keywords': ['product', 'feature', 'pricing', 'service', 'solution', 'platform'],
                'destinations': ['product_database', 'knowledge_base']
            }
        }
    
    def identify_content_type(self, content: Dict[str, Any]) -> str:
        """Identify the type of content based on text analysis"""
        text = content.get('content', '').lower()
        
        scores = {}
        for content_type, rules in self.routing_rules.items():
            score = 0
            for keyword in rules['keywords']:
                if keyword in text:
                    score += text.count(keyword)
            scores[content_type] = score
        
        # Return the content type with highest score, or 'general' if no matches
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'general'
    
    def generate_content_hash(self, content: str) -> str:
        """Generate a hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def extract_metadata_from_content(self, content: str) -> Dict[str, Any]:
        """Extract metadata from Gemini's response"""
        metadata = {}
        
        # Try to extract title
        title_match = re.search(r'(?:Title|Título|Heading):\s*(.+)', content, re.IGNORECASE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Try to extract author
        author_match = re.search(r'(?:Author|Autor|By):\s*(.+)', content, re.IGNORECASE)
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        # Try to extract date
        date_match = re.search(r'(?:Date|Published|Fecha):\s*(.+)', content, re.IGNORECASE)
        if date_match:
            metadata['publish_date'] = date_match.group(1).strip()
        
        # Extract keywords (look for comma-separated lists after Keywords:)
        keywords_match = re.search(r'(?:Keywords|Tags):\s*(.+)', content, re.IGNORECASE)
        if keywords_match:
            keywords = [k.strip() for k in keywords_match.group(1).split(',')]
            metadata['keywords'] = keywords
        
        return metadata
    
    def process(self, extracted_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Main processing pipeline for Gemini-extracted content"""
        try:
            # Extract content
            content = extracted_data.get('content', '')
            if not content:
                return {
                    'status': 'error',
                    'error': 'No content extracted'
                }
            
            # Create metadata
            metadata = {
                'url': extracted_data.get('url'),
                'domain': extracted_data.get('domain'),
                'timestamp': extracted_data.get('timestamp'),
                'content_hash': self.generate_content_hash(content),
                'content_length': len(content),
                'extraction_status': extracted_data.get('extraction_status')
            }
            
            # Extract additional metadata from content
            extracted_metadata = self.extract_metadata_from_content(content)
            metadata.update(extracted_metadata)
            
            # Add URL metadata if available
            if extracted_data.get('url_metadata'):
                metadata['url_metadata'] = extracted_data['url_metadata']
            
            # Identify content type
            content_type = self.identify_content_type(extracted_data)
            metadata['content_type'] = content_type
            
            # Check for duplicates
            existing_memories = self.memory.search(
                query=metadata['content_hash'],
                user_id=user_id,
                limit=1
            )
            
            if existing_memories and len(existing_memories) > 0:
                return {
                    'status': 'duplicate',
                    'existing_memory_id': existing_memories[0].get('id'),
                    'message': 'Content already processed'
                }
            
            # Store main memory entry
            memory_message = self.create_memory_message(content, metadata, content_type)
            memory_result = self.memory.add(
                messages=[memory_message],
                user_id=user_id,
                metadata=metadata
            )
            
            # Process with content-specific handler
            handler = self.content_handlers.get(content_type, self.handle_general_content)
            handler_result = handler(extracted_data, metadata, user_id)
            
            # Determine routing
            routes = self.determine_routes(content_type, metadata, handler_result)
            
            # Find related content
            related_memories = self.find_related_content(extracted_data, user_id)
            
            return {
                'status': 'success',
                'memory_id': memory_result,
                'content_type': content_type,
                'metadata': metadata,
                'handler_result': handler_result,
                'routes': routes,
                'related_memories': related_memories
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def create_memory_message(self, content: str, metadata: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """Create a structured memory message"""
        content_preview = content[:1000]
        
        message_content = f"""
        Webpage Processed: {metadata.get('title', 'Untitled')}
        URL: {metadata['url']}
        Type: {content_type}
        Domain: {metadata['domain']}
        
        Content Summary:
        {content_preview}...
        
        Metadata: {json.dumps({k: v for k, v in metadata.items() if k not in ['content_hash', 'url_metadata']}, indent=2)}
        """
        
        return {
            "role": "user",
            "content": message_content
        }
    
    def determine_routes(self, content_type: str, metadata: Dict[str, Any], handler_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine where to route the content"""
        routes = []
        
        # Get destinations from routing rules
        destinations = self.routing_rules.get(content_type, {}).get('destinations', ['knowledge_base'])
        
        for destination in destinations:
            route = {
                'destination': destination,
                'content_type': content_type,
                'metadata': metadata,
                'priority': handler_result.get('priority', 'normal'),
                'actions': handler_result.get('suggested_actions', [])
            }
            routes.append(route)
        
        return routes
    
    def find_related_content(self, extracted_data: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Find related content in memory"""
        # Search by domain
        domain_results = self.memory.search(
            query=extracted_data.get('domain', ''),
            user_id=user_id,
            limit=3
        )
        
        # Search by extracted keywords if available
        keyword_results = []
        content = extracted_data.get('content', '')
        if content:
            # Extract a meaningful phrase from content for search
            words = content.split()[:10]  # First 10 words
            search_phrase = ' '.join(words)
            keyword_results = self.memory.search(
                query=search_phrase,
                user_id=user_id,
                limit=3
            )
        
        # Combine and deduplicate
        all_results = domain_results + keyword_results
        seen_ids = set()
        unique_results = []
        
        for result in all_results:
            if result.get('id') not in seen_ids:
                seen_ids.add(result.get('id'))
                unique_results.append(result)
        
        return unique_results[:5]  # Return top 5 related memories
    
    # Content-specific handlers
    def handle_research_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle research/academic content"""
        return {
            'handler': 'research',
            'priority': 'high',
            'suggested_actions': [
                'extract_citations',
                'identify_key_findings',
                'create_summary',
                'link_to_authors'
            ],
            'additional_metadata': {
                'requires_peer_review': True,
                'citation_format': 'academic'
            }
        }
    
    def handle_news_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle news content"""
        return {
            'handler': 'news',
            'priority': 'time_sensitive',
            'suggested_actions': [
                'extract_key_facts',
                'identify_sources',
                'check_credibility',
                'create_timeline'
            ],
            'additional_metadata': {
                'freshness_score': self.calculate_freshness(metadata.get('publish_date')),
                'requires_fact_check': True
            }
        }
    
    def handle_documentation_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle documentation content"""
        return {
            'handler': 'documentation',
            'priority': 'normal',
            'suggested_actions': [
                'extract_code_samples',
                'identify_api_endpoints',
                'create_quick_reference',
                'version_tracking'
            ],
            'additional_metadata': {
                'technical_level': 'intermediate',
                'requires_updates': True
            }
        }
    
    def handle_blog_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle blog content"""
        return {
            'handler': 'blog',
            'priority': 'normal',
            'suggested_actions': [
                'extract_main_points',
                'identify_author_perspective',
                'find_related_posts',
                'sentiment_analysis'
            ],
            'additional_metadata': {
                'content_style': 'opinion',
                'engagement_metrics': True
            }
        }
    
    def handle_product_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle product-related content"""
        return {
            'handler': 'product',
            'priority': 'normal',
            'suggested_actions': [
                'extract_features',
                'identify_pricing',
                'competitive_analysis',
                'user_reviews_summary'
            ],
            'additional_metadata': {
                'commercial_intent': True,
                'requires_comparison': True
            }
        }
    
    def handle_general_content(self, extracted_data: Dict[str, Any], metadata: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general/uncategorized content"""
        return {
            'handler': 'general',
            'priority': 'normal',
            'suggested_actions': [
                'basic_summary',
                'keyword_extraction',
                'entity_recognition'
            ],
            'additional_metadata': {
                'requires_classification': True
            }
        }
    
    def calculate_freshness(self, publish_date: str) -> float:
        """Calculate content freshness score"""
        if not publish_date:
            return 0.5
        
        try:
            # Try to parse the date string
            from dateutil import parser
            published = parser.parse(publish_date)
            now = datetime.now(published.tzinfo)
            days_old = (now - published).days
            
            if days_old < 1:
                return 1.0
            elif days_old < 7:
                return 0.8
            elif days_old < 30:
                return 0.6
            elif days_old < 365:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5
