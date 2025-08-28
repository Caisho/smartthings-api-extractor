# SmartThings API Extractor

A Python tool for extracting and analyzing device history data from the SmartThings API. This tool retrieves paginated history data for specific SmartThings devices, processes it into structured formats (CSV/JSON), and provides specialized analysis for appliance cycles (particularly dryer cycles).

## Features

- **Comprehensive Data Extraction**: Retrieves all historical events from SmartThings devices with automatic pagination
- **Multiple Output Formats**: Saves data in both CSV and JSON formats for flexible analysis
- **Timezone Support**: Handles timezone conversion for accurate time-based analysis
- **Drying Cycle Analysis**: Specialized functionality to calculate and analyze dryer cycle durations
- **Robust Error Handling**: Includes retry logic and comprehensive logging
- **Configurable**: Uses environment variables for easy configuration without code changes

## Prerequisites

- Python 3.10 or higher
- SmartThings API Bearer Token
- SmartThings Location ID and Device ID

## Installation

### Option 1: Using uv (recommended)

1. **Install uv package manager** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/Caisho/smartthings-api-extractor.git
   cd smartthings-api-extractor
   ```

3. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv --python 3.10
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync --extra dev
   ```

### Option 2: Using pip

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Caisho/smartthings-api-extractor.git
   cd smartthings-api-extractor
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

## Configuration

Create a `.env` file in the project root with your SmartThings API credentials:

```env
BEARER_TOKEN=your_smartthings_bearer_token_here
LOCATION_ID=your_location_id_here
DEVICE_ID=your_device_id_here
TIMEZONE=America/New_York  # Optional, defaults to Asia/Singapore
```

### Getting Your SmartThings API Credentials

1. **Bearer Token**: 
   - Go to the [SmartThings Developer Portal](https://smartthings.developer.samsung.com/)
   - Create a Personal Access Token with the required scopes
   
2. **Location ID**: 
   - Use the SmartThings API to list your locations: `GET /v1/locations`
   
3. **Device ID**: 
   - Use the SmartThings API to list devices in your location: `GET /v1/devices`

## Usage

### Basic Usage

After setting up your `.env` file, run the extraction script:

```bash
python src/scripts/extract_smartthings_history.py
```

### Command Line Options

The script can be configured through environment variables:

- `BEARER_TOKEN`: Your SmartThings API bearer token (required)
- `LOCATION_ID`: The location ID containing your device (required)  
- `DEVICE_ID`: The specific device ID to extract data from (required)
- `TIMEZONE`: Timezone for data processing (optional, defaults to "Asia/Singapore")

### Output Files

The script generates several output files with timestamps:

- `smartthings_history_YYYYMMDD_HHMMSS_timezone.csv` - Processed data in CSV format
- `smartthings_history_raw_YYYYMMDD_HHMMSS_timezone.json` - Raw API response data
- `smartthings_history_durations_YYYYMMDD_HHMMSS_timezone.csv` - Drying cycle analysis (if applicable)

### Example Output

```
=== EXTRACTION SUMMARY ===
Total records extracted: 1500
DataFrame shape: (1500, 8)
Timezone: America/New_York
Date range: 2024-01-01 00:00:00 to 2024-01-31 23:59:59

=== DRYING CYCLES SUMMARY ===
Total drying cycles: 45
Average drying duration: 1.25 hours
Shortest drying cycle: 0.75 hours
Longest drying cycle: 2.10 hours
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Or with pip:
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

Format code:
```bash
ruff format
```

Lint code:
```bash
ruff check
```

Check for dead code:
```bash
vulture src/
```

### Development Tools

- **pytest**: Testing framework
- **ruff**: Fast Python linter and formatter
- **vulture**: Dead code finder
- **pytest-cov**: Test coverage reporting

## Data Analysis Features

### Drying Cycle Analysis

The tool provides specialized analysis for dryer devices:

- Identifies complete drying cycles from power on to cycle completion
- Calculates cycle durations and timing
- Provides statistical summaries (average, min, max durations)
- Exports detailed cycle data for further analysis

### Supported Event Types

The extractor works with various SmartThings device events:

- Power events (on/off)
- Operational state changes
- Sensor readings
- Device status updates

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your `BEARER_TOKEN` is valid and has the correct permissions
2. **No Data Retrieved**: Check that `LOCATION_ID` and `DEVICE_ID` are correct
3. **Timezone Issues**: Ensure the `TIMEZONE` value is a valid pytz timezone string
4. **Rate Limiting**: The tool includes automatic retry logic for API rate limits

### Logging

The tool provides detailed logging. Check the console output for:
- API request details
- Data processing steps
- Error messages and suggestions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality (`pytest`, `ruff check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the SmartThings ecosystem
- Uses the official SmartThings API
- Designed for home automation enthusiasts and data analysts