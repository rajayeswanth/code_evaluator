"""
Vector service for course material suggestions using FAISS.
Provides personalized suggestions based on evaluation feedback.
"""

import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional
import faiss
from django.conf import settings
from sentence_transformers import SentenceTransformer
from cache_utils import cache_llm_response

logger = logging.getLogger(__name__)

class VectorService:
    """FAISS-based vector service for course material suggestions"""
    
    def __init__(self):
        self.index = None
        self.metadata = None
        self.embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.load_vector_database()
    
    def load_vector_database(self):
        """Load FAISS index and metadata"""
        try:
            # Load FAISS index
            self.index = faiss.read_index("fye_files.index")
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load metadata
            with open("fye_files_metadata.json", "r") as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded metadata with {len(self.metadata)} entries")
            
        except Exception as e:
            logger.error(f"Failed to load vector database: {str(e)}")
            self.index = None
            self.metadata = None
    
    def is_available(self) -> bool:
        """Check if vector database is available"""
        return self.index is not None and self.metadata is not None
    
    def get_materials_by_topics(self, topics: List[str], top_k_per_topic: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get course materials for specific topics.
        
        Args:
            topics: List of topics to search for
            top_k_per_topic: Number of materials per topic
            
        Returns:
            Dictionary mapping topics to lists of materials
        """
        if not self.is_available():
            return {}
        
        try:
            results = {}
            
            for topic in topics:
                # Get embedding for topic
                topic_embedding = self._get_embedding(topic)
                if topic_embedding is None:
                    continue
                
                # Search FAISS index
                query_vector = np.array([topic_embedding], dtype=np.float32)
                distances, indices = self.index.search(query_vector, top_k_per_topic)
                
                # Get materials for this topic
                topic_materials = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.metadata):
                        material = self.metadata[idx]
                        topic_materials.append({
                            'file': material.get('file', 'unknown'),
                            'text': material.get('content', ''),
                            'relevance_score': float(1.0 - distances[0][i])  # Convert distance to similarity
                        })
                
                results[topic] = topic_materials
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting materials by topics: {str(e)}")
            return {}
    
    def get_suggestions_for_feedback(self, feedback: str, max_suggestions: int = 3) -> List[str]:
        """
        Get course material suggestions based on evaluation feedback.
        
        Args:
            feedback: Evaluation feedback text
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggestion strings
        """
        if not self.is_available():
            return []
        
        try:
            # Extract topics from feedback
            topics = self._extract_topics_from_feedback(feedback)
            if not topics:
                return []
            
            # Get materials for topics
            materials = self.get_materials_by_topics(topics, top_k_per_topic=1)
            
            # Generate suggestions using LLM with context
            suggestions = self._generate_suggestions_with_llm(topics, materials, max_suggestions)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []
    
    # @cache_llm_response(cache_alias="llm_cache", timeout=3600)
    def _generate_suggestions_with_llm(self, topics: List[str], materials: Dict[str, List[Dict[str, Any]]], max_suggestions: int) -> List[str]:
        """Generate personalized suggestions using LLM with vector search context"""
        try:
            # Import here to avoid circular imports
            from evaluator_service.openai_service import openai_service
            
            # Prepare context for LLM
            context_parts = []
            for topic in topics[:max_suggestions]:
                if topic in materials and materials[topic]:
                    material = materials[topic][0]  # Get top material
                    filename = material.get('file', 'course_material')
                    content_preview = material.get('text', '')[:300]  # First 300 chars
                    context_parts.append(f"Topic: {topic}\nFile: {filename}\nContent: {content_preview}...")
            
            if not context_parts:
                return []
            
            context = "\n\n".join(context_parts)
            
            prompt = f"""
You are a helpful programming instructor. Based on the student's specific feedback and available course materials, generate personalized, actionable suggestions.

Available materials:
{context}

Generate exactly {len(context_parts)} personalized suggestions, one for each topic. Each suggestion should be:
- Specific to the topic and material
- Actionable and practical
- Reference the specific file
- Give brief, helpful advice

Format each suggestion as: "for [topic] → refer [filename] - [personalized advice]"

Examples:
- "for variables → refer variables_tutorial.pdf - practice variable declaration and scope rules"
- "for arrays → refer arrays_guide.pdf - focus on array indexing and manipulation"
- "for functions → refer functions_basics.pdf - review function parameters and return values"

Make each suggestion unique and relevant to the specific topic and material.
"""
            
            response = openai_service.create_chat_completion([
                {"role": "system", "content": "You are a programming instructor. Generate personalized, actionable suggestions referencing course materials."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                # Parse the response into individual suggestions
                suggestions = []
                lines = response.strip().split('\n')
                for line in lines:
                    if line.strip() and '→' in line:
                        suggestions.append(line.strip())
                
                return suggestions[:max_suggestions]
            
            # Fallback if LLM fails
            fallback_suggestions = []
            for topic in topics[:max_suggestions]:
                if topic in materials and materials[topic]:
                    material = materials[topic][0]
                    filename = material.get('file', 'course_material')
                    fallback_suggestions.append(f"for {topic} → refer {filename}")
            
            return fallback_suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions with LLM: {str(e)}")
            # Fallback to simple suggestions
            fallback_suggestions = []
            for topic in topics[:max_suggestions]:
                if topic in materials and materials[topic]:
                    material = materials[topic][0]
                    filename = material.get('file', 'course_material')
                    fallback_suggestions.append(f"for {topic} → refer {filename}")
            return fallback_suggestions
    
    # @cache_llm_response(cache_alias="llm_cache", timeout=3600)
    def _extract_topics_from_feedback(self, feedback: str) -> List[str]:
        """Extract personalized topics from feedback using LLM"""
        try:
            # Import here to avoid circular imports
            from evaluator_service.openai_service import openai_service
            
            prompt = f"""
Extract exactly 3 programming topics from this evaluation feedback.

Feedback: {feedback}

Extract ONLY 3 specific programming topics that this student needs help with.
Focus on the most relevant topics mentioned in the feedback.

Examples of topics: variables, arrays, loops, functions, conditionals, input, output, calculations, error_handling, file_io, classes, methods, recursion, data_structures

Respond with ONLY a JSON array of exactly 3 topic names, like:
["variables", "arrays", "functions"]

Make the topics specific to what's mentioned in the feedback.
"""
            
            response = openai_service.create_chat_completion([
                {"role": "system", "content": "You are a topic extractor. Extract exactly 3 programming topics from feedback."},
                {"role": "user", "content": prompt}
            ])
            
            if response:
                # Parse JSON response
                topics = json.loads(response.strip())
                if isinstance(topics, list):
                    # Ensure exactly 3 topics
                    while len(topics) < 3:
                        topics.append(topics[0] if topics else "basics")
                    return topics[:3]  # Return exactly 3
            
            # Fallback to simple keyword extraction
            return self._fallback_topic_extraction(feedback)
            
        except Exception as e:
            logger.error(f"Error extracting topics with LLM: {str(e)}")
            return self._fallback_topic_extraction(feedback)
    
    def _fallback_topic_extraction(self, feedback: str) -> List[str]:
        """Fallback topic extraction using keywords"""
        keywords = []
        
        # Common programming topics
        topic_keywords = {
            'variables': ['variable', 'declaration', 'assignment', 'scope'],
            'arrays': ['array', 'list', 'index', 'element'],
            'loops': ['loop', 'iteration', 'for', 'while'],
            'functions': ['function', 'method', 'call', 'parameter'],
            'conditionals': ['if', 'else', 'conditional', 'decision'],
            'input': ['input', 'read', 'user'],
            'output': ['output', 'print', 'display'],
            'calculations': ['calculation', 'math', 'arithmetic', 'compute'],
            'error_handling': ['error', 'exception', 'try', 'catch'],
            'file_io': ['file', 'read', 'write', 'open'],
            'classes': ['class', 'object', 'instance'],
            'methods': ['method', 'function', 'call'],
            'recursion': ['recursion', 'recursive', 'base case'],
            'data_structures': ['stack', 'queue', 'linked list', 'tree']
        }
        
        feedback_lower = feedback.lower()
        for topic, words in topic_keywords.items():
            if any(word in feedback_lower for word in words):
                keywords.append(topic)
        
        # Ensure we have exactly 3 topics
        while len(keywords) < 3:
            keywords.append('basics')
        
        return keywords[:3]
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using sentence-transformers"""
        try:
            return self.embedding_model.encode(text)
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            return None

# Global instance
vector_service = VectorService() 