from google import genai as google_genai
import json
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import logging
from pydantic import BaseModel, ConfigDict

# Google Cloud imports for service account authentication
try:
    from google.ai import generativelanguage as glm
    from google.auth import default
    from google.auth.transport.grpc import secure_authorized_channel
    import grpc
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    glm = None

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
    """Service for generating insights using Google Gemini 2.5 Flash with dual authentication support"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.gcp_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        # Initialize authentication mode
        self.auth_mode = None
        self.model = None
        self.client = None
        self.gcp_client = None
        
        self._initialize_model()
        
        # Response cache for performance optimization
        self.cache: Dict[str, InsightResponse] = {}
        self.cache_expiry = timedelta(hours=1)  # Cache expires after 1 hour
        
    def _initialize_model(self):
        """Initialize the model based on available credentials"""
        
        # Try GCP service account first (evaluator mode)
        if self.gcp_credentials and os.path.exists(self.gcp_credentials) and GCP_AVAILABLE:
            try:
                logger.info("Attempting GCP service account authentication...")
                self._initialize_gcp_mode()
                return
            except Exception as e:
                logger.warning(f"GCP authentication failed: {e}")
                logger.info("Falling back to API key mode...")
        
        # Fall back to API key mode (student/local mode)
        if self.api_key:
            try:
                logger.info("Using API key authentication...")
                self._initialize_api_key_mode()
                return
            except Exception as e:
                logger.error(f"API key authentication failed: {e}")
                raise
        
        # No valid credentials found
        logger.error("No valid credentials found")
        logger.error("Please provide either GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS")
        raise ValueError("No valid authentication credentials found")
    
    def _initialize_gcp_mode(self):
        """Initialize GCP service account mode"""
        if not GCP_AVAILABLE:
            raise ImportError("Google Cloud dependencies not available")
            
        # Set up GCP authentication
        credentials, project = default()
        
        # Create secure channel
        channel = secure_authorized_channel(credentials, None, 'generativelanguage.googleapis.com:443')
        
        # Initialize the GenerativeService client
        self.gcp_client = glm.GenerativeServiceClient(transport=grpc.secure_channel(
            'generativelanguage.googleapis.com:443', grpc.ssl_channel_credentials()))
        
        self.auth_mode = "gcp"
        logger.info(f"GCP mode initialized successfully with model: {self.model_name}")
        logger.info(f"Using credentials: {self.gcp_credentials}")
    
    def _initialize_api_key_mode(self):
        """Initialize API key mode"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for API key mode")

        logger.info(f"Initializing LLM service with model: {self.model_name}")
        logger.info(f"API key found: {self.api_key[:10]}...")

        self.client = google_genai.Client(api_key=self.api_key)
        self.auth_mode = "api_key"
        logger.info("API key mode initialized successfully")
        
    def _generate_content(self, prompt: str) -> Optional[str]:
        """Generate content using the Interactions API."""
        try:
            if self.auth_mode == "api_key":
                interaction = self.client.interactions.create(
                    model=self.model_name,
                    input=prompt,
                )
                return interaction.output_text if interaction else None
                
            elif self.auth_mode == "gcp":
                # Use GCP GenerativeService client
                request = glm.GenerateContentRequest(
                    model=f"models/{self.model_name}",
                    contents=[glm.Content(
                        parts=[glm.Part(text=prompt)]
                    )]
                )
                
                response = self.gcp_client.generate_content(request=request)
                
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        return candidate.content.parts[0].text
                
                logger.warning("No valid response from GCP GenerativeService")
                return None
                
            else:
                logger.error(f"Unknown authentication mode: {self.auth_mode}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating content in {self.auth_mode} mode: {e}")
            return None
    
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
        truncated_content = content[:8000]
        return f"""
        Analyze the following document content and provide insights in JSON format with these exact keys:
        
        Content to analyze:
        {truncated_content}
        
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
        - Return ONLY valid JSON, no markdown code fences or extra text
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
            # Generate insights using the appropriate authentication mode
            prompt = self._create_insight_prompt(content)
            logger.info(f"Sending request to Gemini API using {self.auth_mode} mode...")
            
            response_text = self._generate_content(prompt)
            
            if not response_text:
                logger.error("Empty response from Gemini API")
                return None
            
            logger.info("Received response from Gemini API")
            
            # Parse JSON response
            try:
                # Clean up response text (remove markdown code blocks if present)
                clean_response = response_text.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                
                insights_data = json.loads(clean_response)
                
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
                logger.error(f"Raw response: {response_text}")
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
            
            logger.info(f"Generating {mode} summary with Gemini using {self.auth_mode} mode...")
            
            # Generate response
            response_text = self._generate_content(prompt)
            
            if not response_text:
                logger.warning("Empty response from Gemini for summary")
                return None
            
            summary_text = response_text.strip()
            
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
    
    def get_auth_info(self) -> Dict[str, Any]:
        """Get authentication mode and status information"""
        return {
            "auth_mode": self.auth_mode,
            "model_name": self.model_name,
            "gcp_available": GCP_AVAILABLE,
            "has_api_key": bool(self.api_key),
            "has_gcp_credentials": bool(self.gcp_credentials and os.path.exists(self.gcp_credentials) if self.gcp_credentials else False)
        }
    
    def clear_cache(self):
        """Clear the insights cache"""
        self.cache.clear()
        logger.info("Insights cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "cache_keys": list(self.cache.keys()),
            "auth_info": self.get_auth_info()
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