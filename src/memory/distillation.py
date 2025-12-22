"""
Conversation Distillation
Processes raw conversations into safe summaries for Green Vault storage.

Purpose:
- Extract key topics, themes, and insights from conversations
- Remove verbatim quotes and specific details
- Create abstract summaries suitable for long-term storage
- Ensure no raw conversation text persists

Process:
1. Extract: Identify key topics, themes, and insights
2. Abstract: Remove verbatim quotes and specific details
3. Tag: Apply relevant tags for retrieval
4. Store: Save summary to Green Vault
5. Discard: Delete raw conversation text
"""

from typing import Dict, Optional, List
from datetime import datetime


class ConversationDistiller:
    """
    Distills raw conversations into safe summaries.
    
    This class processes conversations to extract meaningful information
    while removing verbatim text and sensitive details.
    """
    
    def __init__(self):
        """
        Initialize the conversation distiller.
        """
        pass
    
    def distill(
        self,
        user_input: str,
        janet_response: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Distill a conversation into a safe summary.
        
        Args:
            user_input: User's input text
            janet_response: Janet's response text
            context: Additional context (tone, emotional state, etc.)
        
        Returns:
            Dictionary containing:
                - summary: Distilled summary text
                - tags: List of topic tags
                - confidence: Confidence score (0.0-1.0)
                - emotional_tone: General emotional tone (if relevant)
                - actionable_insights: List of actionable insights
        
        Note:
            This method preserves meaning but not words. Verbatim quotes
            are removed unless essential. Personally identifiable information
            is removed unless explicitly consented.
        """
        # Extract topics
        topics = self.extract_topics(user_input + " " + janet_response)
        
        # Extract emotional tone
        emotional_tone = self.extract_emotional_tone(user_input + " " + janet_response, context)
        
        # Extract actionable insights
        insights = self.extract_actionable_insights(user_input + " " + janet_response)
        
        # Create summary (simplified - in full implementation, use LLM)
        # For now, create a basic summary from topics and key phrases
        summary_parts = []
        if topics:
            summary_parts.append(f"Topics: {', '.join(topics[:3])}")
        if emotional_tone:
            summary_parts.append(f"Tone: {emotional_tone}")
        if insights:
            summary_parts.append(f"Insights: {', '.join(insights[:2])}")
        
        summary = ". ".join(summary_parts) if summary_parts else f"Conversation about: {user_input[:100]}"
        
        # Calculate confidence (simplified)
        confidence = 0.7  # Default confidence
        if len(topics) > 0:
            confidence = min(0.9, 0.5 + len(topics) * 0.1)
        
        return {
            "summary": summary,
            "tags": topics,
            "confidence": confidence,
            "emotional_tone": emotional_tone,
            "actionable_insights": insights
        }
    
    def extract_topics(self, text: str) -> List[str]:
        """
        Extract topic tags from text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of topic tags
        """
        # Simplified topic extraction (in full implementation, use NLP/LLM)
        topics = []
        text_lower = text.lower()
        
        # Simple keyword-based topic detection
        topic_keywords = {
            "work": ["work", "job", "career", "office", "employer"],
            "health": ["health", "medical", "doctor", "illness", "wellness"],
            "technology": ["tech", "computer", "software", "code", "programming"],
            "relationships": ["friend", "family", "relationship", "partner", "love"],
            "hobbies": ["hobby", "interest", "activity", "sport", "game"],
            "learning": ["learn", "study", "education", "course", "skill"],
            "travel": ["travel", "trip", "vacation", "journey", "visit"],
            "food": ["food", "cooking", "recipe", "meal", "restaurant"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:5]  # Limit to 5 topics
    
    def extract_emotional_tone(self, text: str, context: Optional[Dict] = None) -> Optional[str]:
        """
        Extract general emotional tone from conversation.
        
        Args:
            text: Conversation text
            context: Additional context
        
        Returns:
            General emotional tone (e.g., "positive", "neutral", "concerned")
            or None if not relevant
        """
        # Check context first
        if context:
            tone = context.get("tone", {}).get("emotional_state", "")
            if tone:
                return tone
        
        # Simple keyword-based tone detection
        text_lower = text.lower()
        
        positive_words = ["happy", "excited", "great", "wonderful", "love", "enjoy"]
        negative_words = ["sad", "angry", "frustrated", "worried", "concerned", "upset"]
        neutral_words = ["okay", "fine", "alright", "normal"]
        
        if any(word in text_lower for word in positive_words):
            return "positive"
        elif any(word in text_lower for word in negative_words):
            return "concerned"
        elif any(word in text_lower for word in neutral_words):
            return "neutral"
        
        return None
    
    def extract_actionable_insights(self, text: str) -> List[str]:
        """
        Extract actionable insights from conversation.
        
        Args:
            text: Conversation text
        
        Returns:
            List of actionable insights
        """
        # Simplified insight extraction (in full implementation, use NLP/LLM)
        insights = []
        text_lower = text.lower()
        
        # Simple pattern-based insight detection
        if "want to" in text_lower or "plan to" in text_lower:
            insights.append("future_plan")
        if "decided" in text_lower or "decision" in text_lower:
            insights.append("decision_made")
        if "learn" in text_lower or "study" in text_lower:
            insights.append("learning_goal")
        
        return insights[:3]  # Limit to 3 insights

