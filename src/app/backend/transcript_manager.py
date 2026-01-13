import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("voicerag")

class TranscriptEntry:
    """Represents a single entry in a conversation transcript."""
    def __init__(self, speaker: str, text: str, timestamp: str):
        self.speaker = speaker
        self.text = text
        self.timestamp = timestamp
    
    def to_dict(self):
        return {
            "speaker": self.speaker,
            "text": self.text,
            "timestamp": self.timestamp
        }

class TranscriptManager:
    """Manages conversation transcripts for call sessions."""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("call_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Store transcripts by session/connection ID
        self.transcripts: Dict[str, List[TranscriptEntry]] = {}
        self.session_metadata: Dict[str, dict] = {}
        
    def create_session(self, session_id: str, metadata: dict = None):
        """Initialize a new transcript session."""
        self.transcripts[session_id] = []
        self.session_metadata[session_id] = metadata or {}
        logger.info(f"📝 Created transcript session: {session_id}")
    
    def add_entry(self, session_id: str, speaker: str, text: str):
        """Add a transcript entry to a session."""
        if not text or text.strip() == "":
            return  # Skip empty text
            
        if session_id not in self.transcripts:
            self.create_session(session_id)
        
        timestamp = datetime.now().isoformat()
        entry = TranscriptEntry(speaker, text.strip(), timestamp)
        self.transcripts[session_id].append(entry)
        
        # Log to console
        logger.info(f"💬 [{speaker}]: {text.strip()}")
    
    def get_transcript(self, session_id: str) -> List[TranscriptEntry]:
        """Retrieve the transcript for a session."""
        return self.transcripts.get(session_id, [])
    
    def format_as_text(self, session_id: str) -> str:
        """Format transcript as plain text."""
        entries = self.get_transcript(session_id)
        if not entries:
            return "No transcript available."
        
        lines = []
        for entry in entries:
            lines.append(f"[{entry.timestamp}] {entry.speaker}: {entry.text}")
        
        return "\n".join(lines)
    
    def format_as_html(self, session_id: str, summary_data: dict = None) -> str:
        """Format transcript as HTML for email with optional AI-generated summary."""
        entries = self.get_transcript(session_id)
        metadata = self.session_metadata.get(session_id, {})
        
        if not entries:
            return "<p>No transcript available.</p>"
        
        # Build HTML
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            ".container { max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            ".header { border-bottom: 3px solid #0078d4; padding-bottom: 15px; margin-bottom: 25px; }",
            ".header h1 { color: #0078d4; margin: 0; font-size: 24px; }",
            ".metadata { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 25px; }",
            ".metadata p { margin: 5px 0; color: #555; }",
            ".metadata strong { color: #333; }",
            ".transcript { background-color: #fafafa; padding: 20px; border-radius: 5px; border-left: 4px solid #0078d4; }",
            ".entry { margin-bottom: 20px; padding: 12px; background-color: white; border-radius: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }",
            ".user { border-left: 3px solid #28a745; }",
            ".assistant { border-left: 3px solid #0078d4; }",
            ".speaker { font-weight: bold; color: #0078d4; margin-bottom: 5px; }",
            ".user .speaker { color: #28a745; }",
            ".timestamp { font-size: 11px; color: #888; margin-bottom: 5px; }",
            ".text { color: #333; line-height: 1.6; }",
            ".footer { margin-top: 25px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #888; text-align: center; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            "<div class='header'>",
            "<h1>📞 Call Transcript</h1>",
            "</div>",
        ]
        
        # Add metadata section
        html_parts.append("<div class='metadata'>")
        html_parts.append("<h2 style='margin-top: 0; font-size: 18px; color: #333;'>Call Information</h2>")
        
        if metadata.get("target_number"):
            html_parts.append(f"<p><strong>Phone Number:</strong> {metadata.get('target_number')}</p>")
        if metadata.get("source_number"):
            html_parts.append(f"<p><strong>From:</strong> {metadata.get('source_number')}</p>")
        if metadata.get("initiated_at"):
            html_parts.append(f"<p><strong>Call Started:</strong> {metadata.get('initiated_at')}</p>")
        if metadata.get("connected_at"):
            html_parts.append(f"<p><strong>Connected:</strong> {metadata.get('connected_at')}</p>")
        if metadata.get("disconnected_at"):
            html_parts.append(f"<p><strong>Ended:</strong> {metadata.get('disconnected_at')}</p>")
        if metadata.get("duration_seconds"):
            duration = int(metadata.get("duration_seconds"))
            minutes = duration // 60
            seconds = duration % 60
            html_parts.append(f"<p><strong>Duration:</strong> {minutes}m {seconds}s</p>")
        
        html_parts.append(f"<p><strong>Total Messages:</strong> {len(entries)}</p>")
        html_parts.append("</div>")
        
        # Add AI-generated summary if available
        if summary_data and summary_data.get("summary"):
            html_parts.append("<div class='summary-section' style='background-color: #e8f4f8; padding: 20px; border-radius: 5px; margin-bottom: 25px; border-left: 4px solid #0078d4;'>")
            html_parts.append("<h2 style='margin-top: 0; font-size: 18px; color: #0078d4; margin-bottom: 15px;'>📊 AI-Generated Call Summary</h2>")
            
            # Add call summary
            summary_text = summary_data.get("summary", "")
            # Convert markdown to HTML (simple conversion for paragraphs)
            summary_paragraphs = summary_text.split('\n\n')
            for para in summary_paragraphs:
                if para.strip():
                    html_parts.append(f"<p style='margin: 10px 0; line-height: 1.6; color: #333;'>{para.strip()}</p>")
            
            # Add zoom meeting table if available
            zoom_info = summary_data.get("zoom_info_table", "")
            if zoom_info and "No meeting scheduled" not in zoom_info:
                html_parts.append("<h3 style='margin-top: 20px; margin-bottom: 10px; font-size: 16px; color: #0078d4;'>🗓️ Scheduled Meeting</h3>")
                # Convert markdown table to HTML table (simplified)
                if "|" in zoom_info:
                    html_parts.append("<div style='overflow-x: auto; margin-top: 10px;'>")
                    html_parts.append("<table style='border-collapse: collapse; width: 100%; background: white; border-radius: 5px; overflow: hidden;'>")
                    
                    lines = zoom_info.strip().split('\n')
                    for i, line in enumerate(lines):
                        if '|' in line:
                            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                            if i == 0:
                                # Header row
                                html_parts.append("<thead style='background-color: #0078d4; color: white;'><tr>")
                                for cell in cells:
                                    html_parts.append(f"<th style='padding: 12px; text-align: left; font-weight: 600;'>{cell}</th>")
                                html_parts.append("</tr></thead>")
                            elif i > 1 and not all(c in ['-', ' ', '|'] for c in line):
                                # Data row (skip separator line)
                                html_parts.append("<tbody><tr>")
                                for cell in cells:
                                    html_parts.append(f"<td style='padding: 12px; border-bottom: 1px solid #ddd;'>{cell}</td>")
                                html_parts.append("</tr></tbody>")
                    
                    html_parts.append("</table>")
                    html_parts.append("</div>")
                else:
                    # Not a table, just show as text
                    html_parts.append(f"<p style='margin: 10px 0; color: #333;'>{zoom_info}</p>")
            elif zoom_info:
                html_parts.append(f"<p style='margin: 15px 0; color: #666; font-style: italic;'>{zoom_info}</p>")
            
            html_parts.append("</div>")
        
        # Add transcript entries
        html_parts.append("<div class='transcript'>")
        html_parts.append("<h2 style='margin-top: 0; font-size: 18px; color: #333; margin-bottom: 15px;'>Conversation</h2>")
        
        for entry in entries:
            speaker_class = "user" if entry.speaker.lower() == "user" else "assistant"
            speaker_display = "👤 Customer" if entry.speaker.lower() == "user" else "🤖 AI Assistant"
            
            html_parts.append(f"<div class='entry {speaker_class}'>")
            html_parts.append(f"<div class='speaker'>{speaker_display}</div>")
            html_parts.append(f"<div class='timestamp'>{entry.timestamp}</div>")
            html_parts.append(f"<div class='text'>{entry.text}</div>")
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        
        # Footer
        html_parts.append("<div class='footer'>")
        html_parts.append("<p>Generated automatically by Customer Support Agent</p>")
        html_parts.append(f"<p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html_parts.append("</div>")
        
        html_parts.extend(["</div>", "</body>", "</html>"])
        
        return "\n".join(html_parts)
    
    def save_transcript(self, session_id: str, filename: str = None) -> Path:
        """Save transcript to a file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{session_id}_{timestamp}.json"
        
        filepath = self.log_dir / filename
        
        data = {
            "session_id": session_id,
            "metadata": self.session_metadata.get(session_id, {}),
            "entries": [entry.to_dict() for entry in self.get_transcript(session_id)],
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Saved transcript to: {filepath}")
        return filepath
    
    def close_session(self, session_id: str):
        """Close and clean up a transcript session."""
        if session_id in self.transcripts:
            entry_count = len(self.transcripts[session_id])
            logger.info(f"✅ Closed transcript session: {session_id} ({entry_count} entries)")
            
            # Save before clearing (optional)
            if entry_count > 0:
                self.save_transcript(session_id)
            
            # Keep the transcript in memory for email sending
            # We'll let the garbage collector clean it up later
            # Or we could explicitly delete after email is sent
    
    def get_session_metadata(self, session_id: str) -> dict:
        """Get metadata for a session."""
        return self.session_metadata.get(session_id, {})
    
    def update_session_metadata(self, session_id: str, metadata: dict):
        """Update metadata for a session."""
        if session_id not in self.session_metadata:
            self.session_metadata[session_id] = {}
        self.session_metadata[session_id].update(metadata)
