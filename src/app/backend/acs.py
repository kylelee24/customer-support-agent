from aiohttp import web
from azure.core.messaging import CloudEvent
from azure.eventgrid import EventGridEvent
from azure.communication.callautomation import (
    CallAutomationClient,
    PhoneNumberIdentifier,
    MediaStreamingOptions,
    MediaStreamingTransportType,
    MediaStreamingContentType,
    MediaStreamingAudioChannelType,
    AudioFormat)
import json
import os
from datetime import datetime
from pathlib import Path

class AcsCaller:
    source_number: str
    acs_connection_string: str
    acs_callback_path: str
    websocket_url: str
    media_streaming_configuration: MediaStreamingOptions
    call_events: dict  # Track call events by connection ID
    transcript_manager = None  # Reference to TranscriptManager
    email_service = None  # Reference to EmailService
    rtmt = None  # Reference to RTMiddleTier for transcript tracking

    def __init__(self, source_number:str, acs_connection_string: str, acs_callback_path: str, acs_media_streaming_websocket_path: str):
        self.source_number = source_number
        self.acs_connection_string = acs_connection_string
        self.acs_callback_path = acs_callback_path
        self.media_streaming_configuration = MediaStreamingOptions(
            transport_url=acs_media_streaming_websocket_path,
            transport_type=MediaStreamingTransportType.WEBSOCKET,
            content_type=MediaStreamingContentType.AUDIO,
            audio_channel_type=MediaStreamingAudioChannelType.MIXED,
            start_media_streaming=True,
            enable_bidirectional=True,
            audio_format=AudioFormat.PCM24_K_MONO
        )
        
        # Initialize call tracking
        self.call_events = {}
        
        # Setup logging directory
        self.log_dir = Path("call_logs")
        self.log_dir.mkdir(exist_ok=True)
        self.events_log_file = self.log_dir / "call_events.jsonl"
    
    def log_call_event(self, event_type: str, call_connection_id: str, data: dict = None):
        """Log call events to a JSONL file for tracking."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "call_connection_id": call_connection_id,
            "data": data or {}
        }
        
        # Write to JSONL file (one JSON object per line)
        with open(self.events_log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # Also print to console for real-time monitoring
        print(f"[{event['timestamp']}] {event_type} - Call ID: {call_connection_id}")
        if data:
            print(f"  Data: {json.dumps(data, indent=2)}")
    
    async def send_transcript_email(self, call_connection_id: str):
        """Send transcript email for a completed call."""
        if not self.transcript_manager or not self.email_service:
            print(f"⚠️ Transcript or email service not configured. Skipping email for call {call_connection_id}")
            return
        
        if not self.email_service.is_configured():
            print(f"⚠️ Email service not configured. Skipping email for call {call_connection_id}")
            return
        
        # Get call info
        call_info = self.call_events.get(call_connection_id, {})
        phone_number = call_info.get("target_number", "Unknown")
        duration_seconds = call_info.get("duration_seconds", 0)
        
        # Format duration
        if duration_seconds:
            minutes = int(duration_seconds) // 60
            seconds = int(duration_seconds) % 60
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = "N/A"
        
        # Get transcript
        transcript_html = self.transcript_manager.format_as_html(call_connection_id)
        transcript_text = self.transcript_manager.format_as_text(call_connection_id)
        
        # Log the transcript to application logs
        print("\n" + "="*80)
        print(f"📋 CALL TRANSCRIPT - {phone_number} ({duration_str})")
        print("="*80)
        print(transcript_text)
        print("="*80 + "\n")
        
        # Send email
        try:
            success = await self.email_service.send_call_transcript(
                call_id=call_connection_id,
                phone_number=phone_number,
                html_transcript=transcript_html,
                plain_text_transcript=transcript_text,
                duration=duration_str
            )
            
            if success:
                print(f"✅ Transcript email sent successfully for call {call_connection_id}")
            else:
                print(f"❌ Failed to send transcript email for call {call_connection_id}")
        except Exception as e:
            print(f"❌ Error sending transcript email: {str(e)}")
    
    async def initiate_call(self, target_number: str):
        self.call_automation_client = CallAutomationClient.from_connection_string(self.acs_connection_string)
        self.target_participant = PhoneNumberIdentifier(target_number)
        self.source_caller = PhoneNumberIdentifier(self.source_number)
        
        # Log call initiation
        print(f"🔄 Initiating call to: {target_number}")
        
        result = self.call_automation_client.create_call(
            self.target_participant, 
            self.acs_callback_path,
            media_streaming=self.media_streaming_configuration,
            source_caller_id_number=self.source_caller
        )
        
        # Log the initiation with call details
        if hasattr(result, 'call_connection_id'):
            call_id = result.call_connection_id
            self.call_events[call_id] = {
                "target_number": target_number,
                "source_number": self.source_number,
                "initiated_at": datetime.now().isoformat(),
                "status": "initiated"
            }
            self.log_call_event("CallInitiated", call_id, {
                "target_number": target_number,
                "source_number": self.source_number
            })
            
            # Update transcript manager metadata if available
            if self.transcript_manager:
                self.transcript_manager.update_session_metadata(call_id, self.call_events[call_id])
        
        return result

    async def answer_inbound_call(self, incoming_call_context: str):
        self.call_automation_client = CallAutomationClient.from_connection_string(self.acs_connection_string)
        self.call_automation_client.answer_call(
            incoming_call_context,
            self.acs_callback_path,
            media_streaming=self.media_streaming_configuration
        )

    async def outbound_call_handler(self, request):
        cloudevent = await request.json() 
        for event_dict in cloudevent:
            event = CloudEvent.from_dict(event_dict)
            if event.data is None:
                continue
                
            call_connection_id = event.data['callConnectionId']
            
            # Track different call events
            if event.type == "Microsoft.Communication.CallConnected":
                print("✅ Call connected")
                if call_connection_id in self.call_events:
                    self.call_events[call_connection_id]["connected_at"] = datetime.now().isoformat()
                    self.call_events[call_connection_id]["status"] = "connected"
                    
                    # Update transcript metadata
                    if self.transcript_manager:
                        self.transcript_manager.update_session_metadata(
                            call_connection_id, 
                            self.call_events[call_connection_id]
                        )
                
                self.log_call_event("CallConnected", call_connection_id, {
                    "call_info": self.call_events.get(call_connection_id, {})
                })
            
            elif event.type == "Microsoft.Communication.CallDisconnected":
                print("❌ Call disconnected")
                if call_connection_id in self.call_events:
                    self.call_events[call_connection_id]["disconnected_at"] = datetime.now().isoformat()
                    self.call_events[call_connection_id]["status"] = "disconnected"
                    
                    # Calculate call duration if connected
                    if "connected_at" in self.call_events[call_connection_id]:
                        connected = datetime.fromisoformat(self.call_events[call_connection_id]["connected_at"])
                        disconnected = datetime.fromisoformat(self.call_events[call_connection_id]["disconnected_at"])
                        duration_seconds = (disconnected - connected).total_seconds()
                        self.call_events[call_connection_id]["duration_seconds"] = duration_seconds
                    
                    # Update transcript metadata with final call info
                    if self.transcript_manager:
                        self.transcript_manager.update_session_metadata(
                            call_connection_id, 
                            self.call_events[call_connection_id]
                        )
                
                self.log_call_event("CallDisconnected", call_connection_id, {
                    "call_info": self.call_events.get(call_connection_id, {})
                })
                
                # Send transcript email after call disconnects
                await self.send_transcript_email(call_connection_id)
            
            elif event.type == "Microsoft.Communication.CallTransferAccepted":
                self.log_call_event("CallTransferAccepted", call_connection_id)
            
            elif event.type == "Microsoft.Communication.CallTransferFailed":
                self.log_call_event("CallTransferFailed", call_connection_id)
            
            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                self.log_call_event("RecognizeCompleted", call_connection_id)
            
            elif event.type == "Microsoft.Communication.RecognizeFailed":
                self.log_call_event("RecognizeFailed", call_connection_id)
            
            else:
                # Log any other event types we receive
                self.log_call_event(event.type, call_connection_id)

        return web.Response(status=200)

    async def inbound_call_handler(self, request):
        # Check if this is an Event Grid validation request
        if request.headers.get('aeg-event-type') == 'SubscriptionValidation':
            data = await request.json()
            validation_code = data[0]['data']['validationCode']
            return web.json_response({
                'validationResponse': validation_code
            })

        # Handle incoming call events
        try:
            event_data = await request.json()
            print(f"📞 Received inbound event data: {event_data}")
            
            # EventGrid sends events in an array
            for event_dict in event_data:
                print(f"Processing event: {event_dict}")
                event = EventGridEvent.from_dict(event_dict)
                
                if event.event_type == "Microsoft.Communication.IncomingCall":
                    print(f"📥 Incoming call event data: {event.data}")
                    incoming_call_context = event.data['incomingCallContext']
                    
                    # Log the incoming call
                    from_number = event.data.get('from', {}).get('phoneNumber', {}).get('value', 'unknown')
                    to_number = event.data.get('to', {}).get('phoneNumber', {}).get('value', 'unknown')
                    
                    self.log_call_event("IncomingCall", "incoming", {
                        "from_number": from_number,
                        "to_number": to_number,
                        "incoming_call_context": incoming_call_context
                    })
                    
                    await self.answer_inbound_call(incoming_call_context)
                    print("✅ Incoming call answered")
                    return web.Response(status=200)
                
        except Exception as e:
            print(f"❌ Error handling inbound call: {str(e)}")
            self.log_call_event("InboundCallError", "error", {"error": str(e)})
            return web.Response(status=500, text=str(e))

        return web.Response(status=200)
