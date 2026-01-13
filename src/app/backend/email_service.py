import logging
from typing import List, Optional
from azure.communication.email import EmailClient

logger = logging.getLogger("voicerag")

class EmailService:
    """Service for sending emails via Azure Communication Services."""
    
    def __init__(self, connection_string: str, sender_address: str, default_recipients: List[str] = None):
        """
        Initialize the email service.
        
        Args:
            connection_string: Azure Communication Services connection string
            sender_address: The verified sender email address (e.g., DoNotReply@<your-domain>.azurecomm.net)
            default_recipients: List of default recipient email addresses
        """
        self.connection_string = connection_string
        self.sender_address = sender_address
        self.default_recipients = default_recipients or []
        self.client = None
        
        if connection_string and sender_address:
            try:
                self.client = EmailClient.from_connection_string(connection_string)
                logger.info(f"✅ Email service initialized with sender: {sender_address}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize email client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ Email service not configured (missing connection string or sender address)")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self.client is not None
    
    async def send_transcript_email(
        self,
        subject: str,
        html_content: str,
        recipients: List[str] = None,
        plain_text_content: str = None
    ) -> bool:
        """
        Send a transcript email.
        
        Args:
            subject: Email subject line
            html_content: HTML formatted email body
            recipients: List of recipient email addresses (uses default if not provided)
            plain_text_content: Plain text version of email (optional)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.error("❌ Email service not configured. Cannot send email.")
            return False
        
        # Use default recipients if none provided
        recipient_list = recipients or self.default_recipients
        
        if not recipient_list:
            logger.error("❌ No recipients specified for email")
            return False
        
        try:
            # Create email message using dictionary structure
            message = {
                "senderAddress": self.sender_address,
                "recipients": {
                    "to": [{"address": recipient} for recipient in recipient_list]
                },
                "content": {
                    "subject": subject,
                    "plainText": plain_text_content or "Please view this email in HTML format.",
                    "html": html_content
                }
            }
            
            logger.info(f"📧 Sending transcript email to: {', '.join(recipient_list)}")
            logger.info(f"   Subject: {subject}")
            
            # Send the email using the poller pattern
            poller = self.client.begin_send(message)
            
            # Wait for the operation to complete
            result = poller.result()
            
            logger.info(f"✅ Email sent successfully! Message ID: {result.get('id', 'unknown')}")
            logger.info(f"   Status: {result.get('status', 'unknown')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            logger.exception(e)
            return False
    
    async def send_call_transcript(
        self,
        call_id: str,
        phone_number: str,
        html_transcript: str,
        plain_text_transcript: str = None,
        duration: str = None,
        recipients: List[str] = None
    ) -> bool:
        """
        Send a call transcript email with formatted subject and content.
        
        Args:
            call_id: The call connection ID
            phone_number: The phone number that was called
            html_transcript: HTML formatted transcript
            plain_text_transcript: Plain text transcript (optional)
            duration: Call duration string (optional)
            recipients: List of recipient emails (uses default if not provided)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Build subject line
        subject = f"Call Transcript - {phone_number}"
        if duration:
            subject += f" ({duration})"
        
        return await self.send_transcript_email(
            subject=subject,
            html_content=html_transcript,
            plain_text_content=plain_text_transcript,
            recipients=recipients
        )
