#!/usr/bin/env python3
"""
Test script for simulating call transcripts and testing the summary/email pipeline.
This allows testing the transcript feature without making actual phone calls.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src/app to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "app"))

from backend.transcript_manager import TranscriptManager
from backend.email_service import EmailService
from backend.call_summarizer import CallSummarizer
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Predefined test scenarios
SCENARIOS = {
    "meeting_scheduled": [
        ("assistant", "Hello! Hi there, this is Jane calling from EVITAVONNI Construction Group. Thank you so much for getting in touch with us about the Bluetooth Hard Hat! I'm an AI assistant helping our team connect with folks interested in learning more about our patented hands-free communication system for job sites. I'd love to set up a Zoom call with our team - it typically takes about 30 minutes - so we can walk you through how it works and answer any questions you might have. Our business hours are 9 to 5 Eastern Standard Time, Monday through Friday. Do you have a preferred day and time that works for you?"),
        ("user", "Hi Jane! Yes, I'm very interested. I work in construction and we've been looking for better communication solutions."),
        ("assistant", "That's wonderful! Construction is exactly where our Bluetooth Hard Hat really shines. The hands-free design means you can stay focused on your work while staying connected with your team. What day and time works best for you for a Zoom demonstration?"),
        ("user", "How about next Tuesday, January 21st at 2 PM?"),
        ("assistant", "Perfect! January 21st at 2 PM EST works great. Can I get your email address so we can send you the Zoom link?"),
        ("user", "Sure, it's kyle.a.lee24@gmail.com"),
        ("assistant", "Great, thank you! And could you spell that out for me to make sure I have it exactly right?"),
        ("user", "K-Y-L-E dot A dot L-E-E-2-4 at gmail.com"),
        ("assistant", "Perfect! So that's kyle.a.lee24@gmail.com. And what's the best phone number to reach you at in case of any technical issues?"),
        ("user", "My number is 647-969-9379"),
        ("assistant", "Excellent! Just to confirm, we'll send a Zoom link to kyle.a.lee24@gmail.com for Tuesday, January 21st at 2 PM EST. If anything comes up and you need to reschedule, you can reply to the email or call us at 740-272-5441. Is there anything else about the Bluetooth Hard Hat I can clarify for you?"),
        ("user", "No, that's perfect. Thanks!"),
        ("assistant", "You're very welcome! We're excited to show you how the Bluetooth Hard Hat can transform communication on your job site. Talk to you next week!"),
    ],
    
    "inquiry_only": [
        ("assistant", "Hello! This is Jane calling from EVITAVONNI Construction Group. Thanks for your interest in the Bluetooth Hard Hat!"),
        ("user", "Hi, I saw your product online. Can you tell me more about how it works?"),
        ("assistant", "Absolutely! The Bluetooth Hard Hat Add-On transforms any standard hard hat into a hands-free communication hub. It uses harmonic resonance technology to turn the hard hat shell itself into a speaker, so your ears stay uncovered for full situational awareness."),
        ("user", "Interesting. What about noisy job sites? Will I be able to hear clearly?"),
        ("assistant", "Great question! That's one of the best features. The harmonic resonance delivers crystal-clear audio even in loud environments. Plus, since it doesn't cover your ears like traditional headsets, you maintain awareness of equipment, alarms, and voices around you - which is crucial for safety."),
        ("user", "How much does it cost?"),
        ("assistant", "I'd love for our team to walk through pricing and package options with you on a Zoom call, since it depends on factors like team size and features you need. They can create a customized solution. Would you like to schedule a quick demo?"),
        ("user", "Let me think about it and discuss with my team first."),
        ("assistant", "That makes complete sense! When you're ready, feel free to reach out. You can call us at 740-272-5441 or visit our website at bluetoothhardhat.com. Is there anything else I can answer for you right now?"),
        ("user", "No, that's all for now. Thanks."),
        ("assistant", "You're welcome! Thanks for your interest. We're here whenever you're ready to learn more!"),
    ],
    
    "technical_questions": [
        ("assistant", "Hello! This is Jane from EVITAVONNI Construction Group. How can I help you today?"),
        ("user", "Hi, I have some technical questions about the Bluetooth Hard Hat."),
        ("assistant", "I'd be happy to help! What would you like to know?"),
        ("user", "Does it work with any brand of hard hat?"),
        ("assistant", "Yes! It's designed as a universal retrofit for any ANSI or CSA-certified hard hat. The control module clips right into the standard pencil holder slot, and the vibrating speaker attaches with industrial-grade adhesive. No modifications to the hard hat required."),
        ("user", "What's the battery life like?"),
        ("assistant", "The system monitors battery life in real-time through the app, so supervisors can see everyone's charge level. For detailed specs on battery duration, our team can discuss that in depth on a Zoom call. Would you like to schedule a demonstration?"),
        ("user", "What about range? How far does the signal reach?"),
        ("assistant", "Since it works on Wi-Fi and cellular networks, the range is essentially unlimited - as long as you have network coverage. You're not limited by radio range like traditional walkie-talkies. Team members across huge job sites, or even at different sites, can communicate seamlessly."),
        ("user", "That's impressive. Can we try it before buying?"),
        ("assistant", "That's exactly what the Zoom call is for! Our team can arrange demos and discuss trial options based on your needs. They'll make sure it's the right fit for your operation. What day works for you?"),
        ("user", "Actually, let me get back to you on that."),
        ("assistant", "No problem at all! When you're ready, just give us a call at 740-272-5441. Thanks for your questions today!"),
    ],
    
    "short_call": [
        ("assistant", "Hello! This is Jane from EVITAVONNI Construction Group."),
        ("user", "Hi, I think I have the wrong number."),
        ("assistant", "No worries! If you ever need information about industrial communication solutions, feel free to reach out. Have a great day!"),
        ("user", "Thanks, bye."),
    ],
    
    "detailed_meeting": [
        ("assistant", "Hello! This is Jane calling from EVITAVONNI Construction Group. I'm here to help schedule a Zoom call about our Bluetooth Hard Hat Add-On."),
        ("user", "Hi Jane! Yes, I'm interested. My name is Kyle and I run an electrical contracting company."),
        ("assistant", "Wonderful, Kyle! Electrical work is perfect for our hands-free solution. When you're working with live wires, having true hands-free communication is crucial. What day and time works best for a Zoom demonstration?"),
        ("user", "I'd like to schedule it for January 21st at 3 PM EST. Will that work?"),
        ("assistant", "January 21st at 3 PM EST works perfectly! Can I get your email address for the Zoom link?"),
        ("user", "It's kyle.a.lee24@gmail.com"),
        ("assistant", "Great! Could you spell that out for me to make sure I have it exactly right?"),
        ("user", "K-Y-L-E dot A dot L-E-E-2-4 at gmail dot com"),
        ("assistant", "Perfect, so that's kyle.a.lee24@gmail.com. And what's your phone number in case we need to reach you?"),
        ("user", "My number is 647-969-9379"),
        ("assistant", "Excellent! Just to confirm that's 647-969-9379, correct?"),
        ("user", "Yes, that's correct."),
        ("assistant", "Perfect! So we have you scheduled for January 21st at 3 PM EST. We'll send the Zoom link to kyle.a.lee24@gmail.com. Before we wrap up, what type of electrical work does your team primarily do?"),
        ("user", "We do commercial and industrial electrical installations, mostly in manufacturing facilities."),
        ("assistant", "That's great context! Our team will have relevant examples ready for manufacturing environments. You'll see how the system handles communication in those settings. Is there anything else you'd like to know?"),
        ("user", "No, I think that covers it. Looking forward to the meeting!"),
        ("assistant", "Wonderful! Thank you for your interest, Kyle. We'll send over the calendar invitation shortly, and if anything comes up, just reply to the email or call us at 740-272-5441. Looking forward to connecting next week!"),
    ],
}

def print_usage():
    """Print usage information."""
    print("Usage: python test_transcript.py [options]")
    print("\nOptions:")
    print("  --scenario NAME    Use a predefined scenario")
    print("  --list            List available scenarios")
    print("  --custom FILE     Load conversation from a file")
    print("  --phone NUMBER    Phone number to use (default: +16479699379)")
    print("\nExamples:")
    print("  python test_transcript.py --scenario meeting_scheduled")
    print("  python test_transcript.py --scenario inquiry_only")
    print("  python test_transcript.py --list")
    print("  python test_transcript.py --custom my_conversation.txt")

def list_scenarios():
    """List available test scenarios."""
    print("\n📋 Available Test Scenarios:\n")
    for name, conversation in SCENARIOS.items():
        print(f"  • {name}")
        print(f"    Messages: {len(conversation)}")
        print(f"    Preview: {conversation[0][1][:60]}...")
        print()

def load_custom_conversation(filepath: str):
    """Load a custom conversation from a file."""
    conversation = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Format: user: text or assistant: text
                if ':' in line:
                    speaker, text = line.split(':', 1)
                    speaker = speaker.strip().lower()
                    text = text.strip()
                    if speaker in ['user', 'assistant']:
                        conversation.append((speaker, text))
    return conversation

async def simulate_call_transcript(
    scenario_name: str = None,
    custom_file: str = None,
    phone_number: str = "+16479699379"
):
    """
    Simulate a call transcript and test the summary/email pipeline.
    
    Args:
        scenario_name: Name of predefined scenario
        custom_file: Path to custom conversation file
        phone_number: Phone number to use for the test call
    """
    load_dotenv()
    
    print("\n" + "="*80)
    print("🧪 CALL TRANSCRIPT SIMULATOR")
    print("="*80 + "\n")
    
    # Load conversation
    if custom_file:
        print(f"📄 Loading custom conversation from: {custom_file}")
        conversation = load_custom_conversation(custom_file)
    elif scenario_name:
        if scenario_name not in SCENARIOS:
            print(f"❌ Unknown scenario: {scenario_name}")
            print("Run with --list to see available scenarios")
            return
        print(f"📝 Using scenario: {scenario_name}")
        conversation = SCENARIOS[scenario_name]
    else:
        print("❌ Please specify --scenario or --custom")
        print_usage()
        return
    
    print(f"💬 Conversation has {len(conversation)} messages\n")
    
    # Initialize services
    print("🔧 Initializing services...")
    
    # Initialize transcript manager
    transcript_manager = TranscriptManager()
    print("  ✓ Transcript manager initialized")
    
    # Initialize call summarizer
    llm_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    
    if not llm_endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set in environment")
        return
    
    call_summarizer = CallSummarizer(llm_endpoint, llm_key)
    print("  ✓ Call summarizer initialized")
    
    # Initialize email service
    email_connection_string = os.environ.get("ACS_EMAIL_CONNECTION_STRING")
    email_sender = os.environ.get("ACS_EMAIL_SENDER")
    email_recipients = os.environ.get("TRANSCRIPT_EMAIL_RECIPIENTS", "").split(",")
    email_recipients = [r.strip() for r in email_recipients if r.strip()]
    
    if not email_connection_string or not email_sender or not email_recipients:
        print("⚠️  Email service not configured. Summary will be shown but not emailed.")
        email_service = None
    else:
        email_service = EmailService(email_connection_string, email_sender, email_recipients)
        print(f"  ✓ Email service initialized (recipients: {', '.join(email_recipients)})")
    
    print()
    
    # Create a test call session
    call_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"📞 Creating test call session: {call_id}")
    
    # Set up call metadata
    start_time = datetime.now() - timedelta(minutes=2)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    metadata = {
        "target_number": phone_number,
        "source_number": "+18332739896",
        "initiated_at": start_time.isoformat(),
        "connected_at": (start_time + timedelta(seconds=5)).isoformat(),
        "disconnected_at": end_time.isoformat(),
        "duration_seconds": duration,
        "status": "disconnected"
    }
    
    transcript_manager.create_session(call_id, metadata)
    print(f"  ✓ Session created with metadata")
    print(f"  ✓ Phone: {phone_number}")
    print(f"  ✓ Duration: {int(duration//60)}m {int(duration%60)}s\n")
    
    # Inject conversation into transcript
    print("💬 Injecting conversation into transcript...")
    base_time = start_time + timedelta(seconds=10)
    
    for i, (speaker, text) in enumerate(conversation):
        # Add some time variation between messages
        message_time = base_time + timedelta(seconds=i * 8)
        transcript_manager.add_entry(call_id, speaker, text)
    
    print(f"  ✓ Injected {len(conversation)} messages\n")
    
    # Display the transcript
    print("="*80)
    print(f"📋 CAPTURED TRANSCRIPT")
    print("="*80)
    transcript_text = transcript_manager.format_as_text(call_id)
    print(transcript_text)
    print("="*80 + "\n")
    
    # Generate call summary
    print("📊 Generating AI call summary with o4-mini...")
    summary_data = await call_summarizer.summarize_call(transcript_text, metadata)
    
    if summary_data.get("error"):
        print(f"❌ Error generating summary: {summary_data['error']}\n")
    else:
        print("✅ Summary generated successfully!\n")
        print("-"*80)
        print("CALL SUMMARY")
        print("-"*80)
        print(summary_data.get("full_response", summary_data.get("summary")))
        print("-"*80 + "\n")
    
    # Format HTML email
    print("📧 Formatting HTML email...")
    html_content = transcript_manager.format_as_html(call_id, summary_data)
    print("  ✓ HTML email formatted\n")
    
    # Save HTML to file for inspection
    html_output = Path("call_logs") / f"test_email_{call_id}.html"
    html_output.parent.mkdir(exist_ok=True)
    with open(html_output, 'w') as f:
        f.write(html_content)
    print(f"💾 HTML email saved to: {html_output}")
    print(f"  (Open in browser to see how the email looks)\n")
    
    # Send email if configured
    if email_service and email_service.is_configured():
        print("📮 Sending test email...")
        duration_str = f"{int(duration//60)}m {int(duration%60)}s"
        
        success = await email_service.send_call_transcript(
            call_id=call_id,
            phone_number=phone_number,
            html_transcript=html_content,
            plain_text_transcript=transcript_text,
            duration=duration_str
        )
        
        if success:
            print(f"✅ Test email sent successfully to: {', '.join(email_recipients)}")
        else:
            print("❌ Failed to send test email")
    else:
        print("⚠️  Skipping email send (not configured)")
    
    # Save transcript JSON
    transcript_manager.save_transcript(call_id)
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print("\nCheck your email and the call_logs/ directory for results!")
    print()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate call transcripts for testing")
    parser.add_argument("--scenario", help="Predefined scenario name")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    parser.add_argument("--custom", help="Custom conversation file path")
    parser.add_argument("--phone", default="+16479699379", help="Phone number (default: +16479699379)")
    
    args = parser.parse_args()
    
    if args.list:
        list_scenarios()
        return
    
    if not args.scenario and not args.custom:
        print_usage()
        return
    
    # Run the simulation
    asyncio.run(simulate_call_transcript(
        scenario_name=args.scenario,
        custom_file=args.custom,
        phone_number=args.phone
    ))

if __name__ == "__main__":
    main()
