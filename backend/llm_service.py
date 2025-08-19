import google.generativeai as genai
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import logging
from pydantic import BaseModel, ConfigDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InsightResponse:
    """Structure for LLM insight responses"""
    takeaways: List[str]
    contradictions: List[str]
    examples: List[str]
    did_you_know: List[str]
    timestamp: str
    processing_time: float

class LLMService:
    """Service for generating insights using Google Gemini 2.5 Flash"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            logger.error("Please ensure your .env file contains GEMINI_API_KEY")
            raise ValueError("GEMINI_API_KEY is required")
            
        logger.info(f"Initializing LLM service with model: {self.model_name}")
        logger.info(f"API key found: {self.api_key[:10]}...")
        
        # Configure Gemini
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
        
        # Response cache for performance optimization
        self.cache: Dict[str, InsightResponse] = {}
        self.cache_expiry = timedelta(hours=1)  # Cache expires after 1 hour
        
    def _generate_cache_key(self, content: str, insight_type: str = "full") -> str:
        """Generate cache key for content"""
        content_hash = hashlib.md5(f"{content}_{insight_type}".encode()).hexdigest()
        return f"insights_{content_hash}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached response is still valid"""
        if cache_key not in self.cache:
            return False
            
        cached_response = self.cache[cache_key]
        cache_time = datetime.fromisoformat(cached_response.timestamp)
        return datetime.now() - cache_time < self.cache_expiry
    
    def _create_insight_prompt(self, content: str) -> str:
        """Create comprehensive prompt for insight generation"""
        return f"""
        Analyze the following document content and provide insights in JSON format with these exact keys:
        
        Content to analyze:
        {content[:8000]}  # Limit content to avoid token limits
        
        Please provide a JSON response with:
        {{
            "takeaways": [3-5 key takeaways from this content],
            "contradictions": [any contradictions, inconsistencies, or conflicting information found],
            "examples": [specific examples, case studies, or illustrations mentioned],
            "did_you_know": [3-4 interesting facts or surprising insights from the content]
        }}
        
        Guidelines:
        - Keep takeaways concise but meaningful (1-2 sentences each)
        - Only include contradictions if they actually exist in the content
        - Examples should be specific and actionable when possible
        - "Did you know" facts should be genuinely interesting or surprising
        - If any category has no relevant content, use an empty array []
        - Ensure all responses are based solely on the provided content
        """
    
    def generate_insights(self, content: str) -> Optional[InsightResponse]:
        """
        Generate comprehensive insights for document content
        
        Args:
            content: Text content from PDF document
            
        Returns:
            InsightResponse object with categorized insights or None if error
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for insight generation")
            return None
            
        start_time = time.time()
        cache_key = self._generate_cache_key(content)
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached insights for key: {cache_key}")
            return self.cache[cache_key]
        
        try:
            # Generate insights using Gemini
            prompt = self._create_insight_prompt(content)
            logger.info("Sending request to Gemini API...")
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.error("Empty response from Gemini API")
                return None
            
            logger.info("Received response from Gemini API")
            
            # Parse JSON response
            try:
                # Clean up response text (remove markdown code blocks if present)
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                insights_data = json.loads(response_text)
                
                # Validate required keys
                required_keys = ['takeaways', 'contradictions', 'examples', 'did_you_know']
                for key in required_keys:
                    if key not in insights_data:
                        insights_data[key] = []
                
                # Create response object
                processing_time = time.time() - start_time
                insight_response = InsightResponse(
                    takeaways=insights_data['takeaways'],
                    contradictions=insights_data['contradictions'],
                    examples=insights_data['examples'],
                    did_you_know=insights_data['did_you_know'],
                    timestamp=datetime.now().isoformat(),
                    processing_time=processing_time
                )
                
                # Cache the response
                self.cache[cache_key] = insight_response
                
                logger.info(f"Generated insights in {processing_time:.2f}s")
                return insight_response
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return None
    
    def generate_takeaways(self, content: str) -> List[str]:
        """Generate only takeaways for faster response"""
        insights = self.generate_insights(content)
        return insights.takeaways if insights else []
    
    def generate_contradictions(self, content: str) -> List[str]:
        """Generate only contradictions for faster response"""
        insights = self.generate_insights(content)
        return insights.contradictions if insights else []
    
    def generate_examples(self, content: str) -> List[str]:
        """Generate only examples for faster response"""
        insights = self.generate_insights(content)
        return insights.examples if insights else []
    
    def generate_facts(self, content: str) -> List[str]:
        """Generate only 'did you know' facts for faster response"""
        insights = self.generate_insights(content)
        return insights.did_you_know if insights else []
    
    def generate_summary(self, content: str, mode: str = "document") -> Optional[str]:
        """
        Generate a summary of the given content
        
        Args:
            content: Text content to summarize
            mode: Either "selection" or "document" to adjust summary style
            
        Returns:
            Generated summary text or None if failed
        """
        start_time = time.time()
        
        # Create cache key for summary
        cache_key = self._generate_cache_key(content, f"summary_{mode}")
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached summary for {mode} mode")
            cached_response = self.cache[cache_key]
            return cached_response.takeaways[0] if cached_response.takeaways else None
        
        try:
            # Create prompt based on mode
            if mode == "selection":
                prompt = f"""
                Provide a concise summary of the following selected text. Focus on the main points and key information in 2-3 sentences.
                
                Selected text:
                {content[:4000]}
                
                Please provide a clear, concise summary that captures the essential information from this selection.
                """
            else:  # document mode
                prompt = f"""
                Provide a comprehensive summary of the following document content. Include the main topics, key findings, and important conclusions in 4-6 sentences.
                
                Document content:
                {content[:8000]}
                
                Please provide a well-structured summary that covers the document's main themes and important information.
                """
            
            logger.info(f"Generating {mode} summary with Gemini...")
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for summary")
                return None
            
            summary_text = response.text.strip()
            
            # Cache the summary (store in takeaways field for consistency)
            processing_time = time.time() - start_time
            cached_summary = InsightResponse(
                takeaways=[summary_text],
                contradictions=[],
                examples=[],
                did_you_know=[],
                timestamp=datetime.now().isoformat(),
                processing_time=processing_time
            )
            self.cache[cache_key] = cached_summary
            
            logger.info(f"Generated {mode} summary in {processing_time:.2f}s")
            return summary_text
            
        except Exception as e:
            logger.error(f"Failed to generate {mode} summary: {e}")
            return None
    
    def clear_cache(self):
        """Clear the insights cache"""
        self.cache.clear()
        logger.info("Insights cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys())
        }

# Global service instance
llm_service = None

def get_llm_service():
    """Get or create LLM service instance"""
    global llm_service
    if llm_service is None:
        try:
            llm_service = LLMService()
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            return None
    return llm_service