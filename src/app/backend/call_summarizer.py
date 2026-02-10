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
                "consultation_info_table": "No consultation scheduled."
            }

        # Create the summarization prompt
        prompt = f"""You are analyzing a call transcript from MacHenry Realtor, a real estate company specializing in Dominican Republic property (luxury homes, beachfront villas, and investment properties).

Please analyze the following call transcript and provide:

1. **Call Summary**: A concise 2-3 paragraph summary of the call, including:
   - Purpose of the call (buying, selling, investing, general inquiry)
   - Key topics discussed (property types, locations, budget, buying process, residency, etc.)
   - Caller's interests, preferences, or concerns
   - Outcome of the call (consultation scheduled, information provided, follow-up needed)

2. **Lead Qualification**: If the caller shared any of the following, extract and present in a markdown table:
   - Caller Name
   - Email
   - Phone Number
   - Property Interest (villa, condo, beachfront, land, etc.)
   - Location Preference (areas in the DR)
   - Budget Range
   - Timeline
   - Purpose (relocation, vacation home, investment)

If no lead information was gathered, state "No lead information captured during this call."

3. **Consultation Details**: If a consultation was scheduled, extract the details and present in a markdown table:
   - Consultation Date
   - Consultation Time (with timezone)
   - Contact Name
   - Contact Email
   - Contact Phone
   - Notes

If no consultation was scheduled, state "No consultation scheduled during this call."

Here is the call transcript:

{transcript_text}

Please provide your response in the following format:

## Call Summary
[Your summary here]

## Lead Qualification
[Either a markdown table with lead details, or "No lead information captured during this call."]

## Consultation Details
[Either a markdown table with consultation details, or "No consultation scheduled during this call."]
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
                        "content": "You are a professional call transcript analyst for MacHenry Realtor, a Dominican Republic real estate company. Provide clear, concise summaries, extract lead qualification details, and identify any scheduled consultations."
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
            
            # Parse the response to separate summary, lead info, and consultation info
            summary = summary_content
            lead_info = "No lead information extracted."
            consultation_info = "No consultation information extracted."

            # Extract Call Summary
            if "## Call Summary" in summary_content:
                after_summary = summary_content.split("## Call Summary", 1)[1]
                # Find the next section
                next_section = None
                for header in ["## Lead Qualification", "## Consultation Details"]:
                    if header in after_summary:
                        next_section = header
                        break
                if next_section:
                    summary = after_summary.split(next_section, 1)[0].strip()
                else:
                    summary = after_summary.strip()

            # Extract Lead Qualification
            if "## Lead Qualification" in summary_content:
                after_lead = summary_content.split("## Lead Qualification", 1)[1]
                if "## Consultation Details" in after_lead:
                    lead_info = after_lead.split("## Consultation Details", 1)[0].strip()
                else:
                    lead_info = after_lead.strip()

            # Extract Consultation Details
            if "## Consultation Details" in summary_content:
                consultation_info = summary_content.split("## Consultation Details", 1)[1].strip()

            return {
                "summary": summary,
                "lead_info_table": lead_info,
                "consultation_info_table": consultation_info,
                "full_response": summary_content
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate call summary: {str(e)}")
            logger.exception(e)
            return {
                "summary": "Error generating call summary.",
                "lead_info_table": "",
                "consultation_info_table": "",
                "error": str(e)
            }
