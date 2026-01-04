#!/usr/bin/env python3
"""
Bulk Calling Script for Customer Support Agent
Calls a list of phone numbers one by one with configurable delays.
Logs all activity to CSV and console.
"""

import asyncio
import aiohttp
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List


class BulkCaller:
    def __init__(
        self,
        api_url: str = "http://localhost:8765/call",
        delay_between_calls: int = 30,
        log_dir: str = "call_logs"
    ):
        """
        Initialize the bulk caller.
        
        Args:
            api_url: The URL of the call API endpoint
            delay_between_calls: Seconds to wait between calls (default: 30)
            log_dir: Directory to store log files
        """
        self.api_url = api_url
        self.delay_between_calls = delay_between_calls
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = self.log_dir / f"bulk_call_{timestamp}.csv"
        
        # Initialize CSV file with headers
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp',
                'Phone Number',
                'Status',
                'Response',
                'Error'
            ])
        
        print(f"📋 Log file created: {self.csv_file}")
    
    async def call_number(self, phone_number: str) -> dict:
        """
        Make a call to a single phone number.
        
        Args:
            phone_number: The phone number to call (e.g., "+1234567890")
            
        Returns:
            dict with status information
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'phone_number': phone_number,
            'status': 'unknown',
            'response': '',
            'error': ''
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json={'number': phone_number},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result['status'] = 'success' if response.status == 200 else 'failed'
                    result['response'] = await response.text()
                    
                    if response.status != 200:
                        result['error'] = f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            result['status'] = 'timeout'
            result['error'] = 'Request timed out'
        except aiohttp.ClientConnectorError as e:
            result['status'] = 'connection_error'
            result['error'] = f'Cannot connect to server: {str(e)}'
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def log_to_csv(self, result: dict):
        """Log a call result to the CSV file."""
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result['timestamp'],
                result['phone_number'],
                result['status'],
                result['response'],
                result['error']
            ])
    
    def print_result(self, result: dict, index: int, total: int):
        """Print formatted result to console."""
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'timeout': '⏱️',
            'connection_error': '🔌',
            'error': '⚠️'
        }
        
        emoji = status_emoji.get(result['status'], '❓')
        print(f"\n[{index}/{total}] {emoji} {result['phone_number']}")
        print(f"  Status: {result['status']}")
        print(f"  Response: {result['response']}")
        if result['error']:
            print(f"  Error: {result['error']}")
    
    async def call_list(self, phone_numbers: List[str]):
        """
        Call a list of phone numbers sequentially.
        
        Args:
            phone_numbers: List of phone numbers to call
        """
        total = len(phone_numbers)
        successful = 0
        failed = 0
        
        print(f"\n🚀 Starting bulk calling...")
        print(f"📞 Total numbers to call: {total}")
        print(f"⏱️  Delay between calls: {self.delay_between_calls} seconds")
        print(f"{'='*60}\n")
        
        for index, phone_number in enumerate(phone_numbers, 1):
            # Make the call
            result = await self.call_number(phone_number)
            
            # Log and display result
            self.log_to_csv(result)
            self.print_result(result, index, total)
            
            # Update counters
            if result['status'] == 'success':
                successful += 1
            else:
                failed += 1
            
            # Wait before next call (except for the last one)
            if index < total:
                print(f"\n⏳ Waiting {self.delay_between_calls} seconds before next call...")
                await asyncio.sleep(self.delay_between_calls)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 Summary:")
        print(f"  Total calls: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Success rate: {(successful/total*100):.1f}%")
        print(f"\n📋 Full log saved to: {self.csv_file}")


def load_phone_numbers_from_file(file_path: str) -> List[str]:
    """
    Load phone numbers from a text file (one per line).
    
    Args:
        file_path: Path to the file containing phone numbers
        
    Returns:
        List of phone numbers
    """
    numbers = []
    with open(file_path, 'r') as f:
        for line in f:
            number = line.strip()
            # Skip empty lines and comments
            if number and not number.startswith('#'):
                numbers.append(number)
    return numbers


async def main():
    """Main entry point for the bulk calling script."""
    
    # Configuration
    # Default to Azure endpoint, fall back to localhost for local development
    API_URL = os.environ.get("CALL_API_URL", "https://callcenterapp.mangohill-ecc6369c.eastus2.azurecontainerapps.io/call")
    DELAY_SECONDS = int(os.environ.get("CALL_DELAY_SECONDS", "120"))
    PHONE_LIST_FILE = os.environ.get("PHONE_LIST_FILE", "phone_numbers.txt")
    
    # Option 1: Load from file
    if os.path.exists(PHONE_LIST_FILE):
        print(f"📄 Loading phone numbers from: {PHONE_LIST_FILE}")
        phone_numbers = load_phone_numbers_from_file(PHONE_LIST_FILE)
    else:
        # Option 2: Hardcoded example list (for testing)
        print(f"⚠️  File '{PHONE_LIST_FILE}' not found. Using example numbers.")
        print(f"💡 Create a '{PHONE_LIST_FILE}' file with one number per line.\n")
        phone_numbers = [
            "+1234567890",
            "+1987654321",
            # Add your phone numbers here
        ]
    
    if not phone_numbers:
        print("❌ No phone numbers to call. Exiting.")
        return
    
    # Create caller and start calling
    caller = BulkCaller(
        api_url=API_URL,
        delay_between_calls=DELAY_SECONDS
    )
    
    await caller.call_list(phone_numbers)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise

