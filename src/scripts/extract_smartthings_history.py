#!/usr/bin/env python3
"""
SmartThings Device History Extractor

This script extracts all paginated history data from the SmartThings API
for a specific device and location, then parses it into a pandas DataFrame.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pytz

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SmartThingsHistoryExtractor:
    """Extract and parse SmartThings device history data."""

    def __init__(self, bearer_token: str, timezone: str = "Asia/Singapore"):
        """
        Initialize the extractor with authentication token and timezone.

        Args:
            bearer_token: SmartThings API bearer token
            timezone: Timezone string (e.g., 'Asia/Singapore', 'UTC', 'America/New_York')
        """
        self.bearer_token = bearer_token
        self.timezone = timezone
        try:
            self.tz = pytz.timezone(timezone)
            logger.info(f"Using timezone: {timezone}")
        except pytz.UnknownTimeZoneError:
            logger.warning(f"Unknown timezone '{timezone}', falling back to UTC")
            self.tz = pytz.UTC
            self.timezone = "UTC"
        
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def make_request(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Make HTTP request with retry logic.

        Args:
            url: API endpoint URL
            max_retries: Maximum number of retry attempts

        Returns:
            JSON response data or None if failed
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Making request to: {url}")
                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2**attempt
                    logger.warning(
                        f"Rate limited. Waiting {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        return None

    def extract_all_history(
        self,
        location_id: str,
        device_id: str,
        limit: int = 20,
        oldest_first: bool = False,
    ) -> List[Dict]:
        """
        Extract all paginated history data from SmartThings API.

        Args:
            location_id: SmartThings location ID
            device_id: SmartThings device ID
            limit: Number of records per page
            oldest_first: Whether to retrieve oldest records first

        Returns:
            List of all history records
        """
        base_url = "https://api.smartthings.com/v1/history/devices"
        all_data = []

        # Initial request
        initial_params = {
            "locationId": location_id,
            "deviceId": device_id,
            "limit": limit,
            "oldestFirst": str(oldest_first).lower(),
        }

        url = f"{base_url}?" + "&".join(
            [f"{k}={v}" for k, v in initial_params.items()]
        )

        page_count = 0

        while url:
            page_count += 1
            logger.info(f"Processing page {page_count}...")

            response_data = self.make_request(url)

            if not response_data:
                logger.error("Failed to get response data")
                break

            # Extract items from current page
            items = response_data.get("items", [])
            all_data.extend(items)

            logger.info(
                f"Page {page_count}: Retrieved {len(items)} records. Total: {len(all_data)}"
            )

            # Check for next page
            links = response_data.get("_links", {})
            next_link = links.get("next", {})
            url = next_link.get("href") if next_link else None

            # Add small delay to be respectful to the API
            time.sleep(0.1)

        logger.info(
            f"Extraction completed. Total records: {len(all_data)} from {page_count} pages"
        )
        return all_data

    def parse_to_dataframe(self, history_data: List[Dict]) -> pd.DataFrame:
        """
        Parse history data into a pandas DataFrame.

        Args:
            history_data: List of history record dictionaries

        Returns:
            Pandas DataFrame with parsed data
        """
        if not history_data:
            logger.warning("No data to parse")
            return pd.DataFrame()

        logger.info(f"Parsing {len(history_data)} records to DataFrame...")

        # Normalize the JSON data
        df = pd.json_normalize(history_data)

        # Convert timestamp columns to datetime if they exist
        timestamp_columns = [
            col
            for col in df.columns
            if "time" in col.lower() or "date" in col.lower()
        ]

        for col in timestamp_columns:
            if col in df.columns:
                try:
                    # Handle different timestamp formats
                    if df[col].dtype == "object":
                        # Parse as UTC first, then convert to target timezone
                        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                        df[col] = df[col].dt.tz_convert(self.tz)
                    elif df[col].dtype in ["int64", "float64"]:
                        # Assume Unix timestamp in milliseconds, convert to target timezone
                        df[col] = pd.to_datetime(
                            df[col], unit="ms", errors="coerce", utc=True
                        )
                        df[col] = df[col].dt.tz_convert(self.tz)
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to datetime: {e}")

        # Sort by timestamp if available
        if "time" in df.columns:
            df = df.sort_values("time", ascending=True)
        elif "timestamp" in df.columns:
            df = df.sort_values("timestamp", ascending=True)

        logger.info(f"DataFrame created with shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    def calculate_drying_durations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate drying durations from start to end events.
        A valid drying cycle requires:
        - Start: "Power of Dryer is On" followed by "Dryer Device status was Drying"
        - End: "Power of Dryer is Off"
        
        Paused events are filtered out to ensure reliable cycle detection.
        
        Args:
            df: DataFrame with SmartThings history data
            
        Returns:
            DataFrame with drying cycles and their durations
        """
        if df.empty or 'text' not in df.columns or 'time' not in df.columns:
            logger.warning("No data or required columns for duration calculation")
            return pd.DataFrame()
        
        logger.info("Calculating drying durations with consecutive power on + drying status...")
        
        # Sort by time to ensure proper order
        df_sorted = df.sort_values('time').reset_index(drop=True)
        
        # Filter out paused events to avoid interference with cycle detection
        paused_events_count = len(df_sorted[df_sorted['text'] == 'Dryer Device status was Paused'])
        logger.info(f"Filtering out {paused_events_count} paused events for reliable cycle detection")
        
        df_filtered = df_sorted[df_sorted['text'] != 'Dryer Device status was Paused'].reset_index(drop=True)
        
        logger.info(f"Processing {len(df_filtered)} events after filtering out paused status")
        
        # Find valid drying cycle starts (power on followed by drying status)
        valid_starts = []
        
        for i in range(len(df_filtered) - 1):
            current_event = df_filtered.iloc[i]
            next_event = df_filtered.iloc[i + 1]
            
            # Check if current event is "Power of Dryer is On"
            if (current_event['text'] == 'Power of Dryer is On' and 
                next_event['text'] == 'Dryer Device status was Drying'):
                
                # Use the "Dryer Device status was Drying" event as the actual start time
                valid_starts.append({
                    'power_on_time': current_event['time'],
                    'drying_start_time': next_event['time'],
                    'start_event': next_event,
                    'power_on_event': current_event
                })
        
        # Filter for end events (from filtered data)
        end_events = df_filtered[df_filtered['text'] == 'Power of Dryer is Off'].copy()
        
        if not valid_starts or end_events.empty:
            logger.warning(f"Found {len(valid_starts)} valid start sequences and {len(end_events)} end events")
            return pd.DataFrame()
        
        logger.info(f"Found {len(valid_starts)} valid drying start sequences and {len(end_events)} end events")
        
        drying_cycles = []
        
        for start_info in valid_starts:
            drying_start_time = start_info['drying_start_time']
            power_on_time = start_info['power_on_time']
            start_event = start_info['start_event']
            power_on_event = start_info['power_on_event']
            
            # Find the next end event after this start sequence
            matching_end_events = end_events[end_events['time'] > drying_start_time]
            
            if not matching_end_events.empty:
                end_event = matching_end_events.iloc[0]  # Get the first (earliest) end event
                end_time = end_event['time']
                
                # Calculate duration from when drying actually started
                duration = end_time - drying_start_time
                duration_minutes = duration.total_seconds() / 60
                duration_hours = duration_minutes / 60
                
                # Calculate total time including power-on to end
                total_duration = end_time - power_on_time
                total_duration_minutes = total_duration.total_seconds() / 60
                total_duration_hours = total_duration_minutes / 60
                
                # Create cycle record
                cycle = {
                    'power_on_time': power_on_time,
                    'drying_start_time': drying_start_time,
                    'cycle_end_time': end_time,
                    'drying_duration_minutes': round(duration_minutes, 2),
                    'drying_duration_hours': round(duration_hours, 2),
                    'total_duration_minutes': round(total_duration_minutes, 2),
                    'total_duration_hours': round(total_duration_hours, 2),
                    'drying_duration_formatted': str(duration).split('.')[0],  # Remove microseconds
                    'total_duration_formatted': str(total_duration).split('.')[0],
                    'timezone': self.timezone,
                    'start_deviceId': start_event['deviceId'],
                    'start_deviceName': start_event['deviceName'],
                    'start_locationId': start_event['locationId'],
                    'start_locationName': start_event['locationName'],
                    'end_deviceId': end_event['deviceId'],
                    'end_deviceName': end_event['deviceName'],
                    'end_locationId': end_event['locationId'],
                    'end_locationName': end_event['locationName']
                }
                
                drying_cycles.append(cycle)
        
        if not drying_cycles:
            logger.warning("No matching start-end event pairs found")
            return pd.DataFrame()
        
        cycles_df = pd.DataFrame(drying_cycles)
        logger.info(f"Created {len(cycles_df)} valid drying cycles (paused events filtered out)")
        
        return cycles_df

    def save_data(
        self,
        df: pd.DataFrame,
        raw_data: List[Dict],
        output_prefix: str = "smartthings_history",
    ) -> Tuple[str, str, Optional[str]]:
        """
        Save data to files.

        Args:
            df: DataFrame to save
            raw_data: Raw JSON data to save
            output_prefix: Prefix for output filenames

        Returns:
            Tuple of (csv_filename, json_filename, duration_csv_filename)
        """
        # Use timezone-aware timestamp for filename
        now = datetime.now(self.tz)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        tz_suffix = now.strftime("%z")  # Add timezone offset
        
        # Save DataFrame as CSV
        csv_filename = f"{output_prefix}_{timestamp}_{self.timezone.replace('/', '_')}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"DataFrame saved to: {csv_filename}")

        # Save raw data as JSON
        json_filename = f"{output_prefix}_raw_{timestamp}_{self.timezone.replace('/', '_')}.json"
        with open(json_filename, "w") as f:
            json.dump(raw_data, f, indent=2, default=str)
        logger.info(f"Raw data saved to: {json_filename}")

        # Calculate and save drying durations
        durations_df = self.calculate_drying_durations(df)
        duration_csv_filename = None
        
        if not durations_df.empty:
            duration_csv_filename = f"{output_prefix}_durations_{timestamp}_{self.timezone.replace('/', '_')}.csv"
            durations_df.to_csv(duration_csv_filename, index=False)
            logger.info(f"Drying durations saved to: {duration_csv_filename}")
        else:
            logger.warning("No drying durations to save")

        return csv_filename, json_filename, duration_csv_filename


def main():
    """Main execution function."""    
    # Configuration from environment variables
    BEARER_TOKEN = os.getenv("BEARER_TOKEN")
    LOCATION_ID = os.getenv("LOCATION_ID")
    DEVICE_ID = os.getenv("DEVICE_ID")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Singapore")  # Default timezone

    # Validate required environment variables
    if not BEARER_TOKEN:
        raise ValueError("BEARER_TOKEN environment variable is required")
    if not LOCATION_ID:
        raise ValueError("LOCATION_ID environment variable is required")
    if not DEVICE_ID:
        raise ValueError("DEVICE_ID environment variable is required")

    try:
        # Initialize extractor with timezone
        extractor = SmartThingsHistoryExtractor(BEARER_TOKEN, timezone=TIMEZONE)

        # Extract all history data
        logger.info("Starting SmartThings history extraction...")
        history_data = extractor.extract_all_history(
            location_id=LOCATION_ID,
            device_id=DEVICE_ID,
            limit=200,  # Larger page size for efficiency
            oldest_first=False,
        )

        if not history_data:
            logger.error("No data extracted")
            return

        # Parse to DataFrame
        df = extractor.parse_to_dataframe(history_data)

        # Display basic info
        print("\n=== EXTRACTION SUMMARY ===")
        print(f"Total records extracted: {len(history_data)}")
        print(f"DataFrame shape: {df.shape}")
        print(f"Timezone: {TIMEZONE}")
        print(
            f"Date range: {df['time'].min() if 'time' in df.columns else 'N/A'} to {df['time'].max() if 'time' in df.columns else 'N/A'}"
        )

        # Display first few rows
        print("\n=== FIRST 5 ROWS ===")
        print(df.head())

        # Display column info
        print("\n=== COLUMN INFO ===")
        print(df.info())

        # Save data (including durations)
        csv_file, json_file, duration_csv_file = extractor.save_data(df, history_data)
        print("\n=== FILES SAVED ===")
        print(f"CSV: {csv_file}")
        print(f"JSON: {json_file}")
        if duration_csv_file:
            print(f"Duration CSV: {duration_csv_file}")
            
            # Display duration summary
            durations_df = extractor.calculate_drying_durations(df)
            if not durations_df.empty:
                print("\n=== DRYING CYCLES SUMMARY ===")
                print(f"Total drying cycles: {len(durations_df)}")
                print(f"Average drying duration: {durations_df['drying_duration_hours'].mean():.2f} hours")
                print(f"Shortest drying cycle: {durations_df['drying_duration_hours'].min():.2f} hours")
                print(f"Longest drying cycle: {durations_df['drying_duration_hours'].max():.2f} hours")
                print("\n=== FIRST 5 DRYING CYCLES ===")
                print(durations_df.head())

        return df

    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        raise


if __name__ == "__main__":
    df = main()
