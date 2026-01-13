import logging
from typing import Optional, Dict
from openai import AsyncAzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger("voicerag")

class CallSummarizer:
    """Service for summarizing call transcripts using GPT-4o-mini."""
    
    def __init__(self, endpoint: str, api_key: str = None, credentials = None):
        """
        Initialize the call summarizer.
        
        Args:
            endpoint: Azure OpenAI endpoint
            api_key: API key (optional, uses credentials if not provided)
            credentials: Azure credentials (optional)
        """
        self.endpoint = endpoint
        
        # Initialize OpenAI client
        # Use 2024-12-01-preview API version for o4-mini compatibility
        if api_key:
            self.client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint
            )
        elif credentials:
            token_provider = get_bearer_token_provider(
                credentials,
                "https://cognitiveservices.azure.com/.default"
            )
            self.client = AsyncAzureOpenAI(
                azure_ad_token_provider=token_provider,
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint
            )
        else:
            raise ValueError("Either api_key or credentials must be provided")
        
        logger.info("✅ Call summarizer initialized")
    
    async def summarize_call(self, transcript_text: str, call_metadata: dict = None) -> Dict[str, str]:
        """
        Summarize a call transcript and extract key information.
        
        Args:
            transcript_text: Plain text transcript of the call
            call_metadata: Optional metadata about the call
        
        Returns:
            Dictionary with 'summary' and 'zoom_info_table' keys
        """
        if not transcript_text or transcript_text.strip() == "" or "No transcript available" in transcript_text:
            return {
                "summary": "No conversation content available to summarize.",
                "zoom_info_table": "No meeting information scheduled."
            }
        
        # Create the summarization prompt
        prompt = f"""You are analyzing a call transcript from a customer support agent for EVITAVONNI Construction Group, which sells Bluetooth Hard Hat Add-Ons.

Please analyze the following call transcript and provide:

1. **Call Summary**: A concise 2-3 paragraph summary of the call, including:
   - Purpose of the call
   - Key topics discussed
   - Customer's interests or concerns
   - Outcome of the call

2. **Zoom Meeting Information**: If a Zoom meeting was scheduled, extract the details and present them in a markdown table format with these columns:
   - Meeting Date
   - Meeting Time (with timezone)
   - Customer Name
   - Customer Email
   - Customer Phone
   - Additional Notes

If no meeting was scheduled, state "No meeting scheduled during this call."

Here is the call transcript:

{transcript_text}

Please provide your response in the following format:

## Call Summary
[Your summary here]

## Zoom Meeting Information
[Either a markdown table with the meeting details, or "No meeting scheduled during this call."]
"""
        
        try:
            logger.info("📊 Generating call summary with o4-mini...")
            
            # Call the model
            # Note: o4-mini only supports default temperature (1) and max_completion_tokens
            response = await self.client.chat.completions.create(
                model="o4-mini",  # Using o4-mini deployment for call summarization
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional call transcript analyst. Provide clear, concise summaries and extract meeting information accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=1000  # o4-mini requires max_completion_tokens (not max_tokens)
            )
            
            # Extract the summary
            summary_content = response.choices[0].message.content
            
            logger.info("✅ Call summary generated successfully")
            
            # Parse the response to separate summary and zoom info
            parts = summary_content.split("## Zoom Meeting Information")
            
            if len(parts) == 2:
                summary = parts[0].replace("## Call Summary", "").strip()
                zoom_info = parts[1].strip()
            else:
                # Fallback if format is different
                summary = summary_content
                zoom_info = "No meeting information extracted."
            
            return {
                "summary": summary,
                "zoom_info_table": zoom_info,
                "full_response": summary_content
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate call summary: {str(e)}")
            logger.exception(e)
            return {
                "summary": "Error generating call summary.",
                "zoom_info_table": "Unable to extract meeting information.",
                "error": str(e)
            }
