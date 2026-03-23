"""
Translation delegation - "Hey Janet, translate X to Japanese"
Uses Ollama with a translation-capable model.
"""
from typing import Optional


def translate_text(
    text: str,
    target_lang: str = "Japanese",
    source_lang: Optional[str] = None,
    llm_client=None,
) -> str:
    """
    Translate text to target language using LLM.
    
    Args:
        text: Text to translate
        target_lang: Target language (e.g., "Japanese", "Spanish")
        source_lang: Optional source language
        llm_client: Ollama/LiteLLM client for generation
        
    Returns:
        Translated text
    """
    if not text.strip():
        return ""
    
    prompt = f"""Translate the following text to {target_lang}.
{f'Source language: {source_lang}.' if source_lang else ''}
Output only the translation, no explanations.

Text:
{text}

Translation:"""
    
    if llm_client:
        try:
            # llm_client can be .route(query) or .generate(prompt, **kwargs)
            if hasattr(llm_client, "route"):
                response = llm_client.route(prompt)
            elif callable(llm_client):
                response = llm_client(prompt)
            else:
                response = None
            return (response or "").strip()
        except Exception as e:
            return f"[Translation error: {e}]"
    
    # Fallback: return original if no LLM
    return text
