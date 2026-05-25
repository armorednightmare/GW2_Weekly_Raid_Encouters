# GW2 Weekly Raid & Strike Bounties Tracker

A Python terminal script that tracks your Guild Wars 2 weekly raid clears, strike mission clears, and daily bounties. It pulls data from the official **Guild Wars 2 API** and cross-references it with **Killproof.me** to provide a comprehensive, colorful console overview of what you are missing for the week.

## Features

- **Daily Bounties**: Shows today's raid and strike bounties based on the GW2 Wiki rotation.
- **Weekly Missing Bounties**: Lists any bounties you missed earlier in the week.
- **Raid & Strike Overview**: Shows a complete list of all encounters with your current clear status.
- **Killproof.me Integration**: Displays a checkmark (`✔`) if the clear is also registered on your Killproof.me profile.

## Requirements

- Python 3.8+
- A Guild Wars 2 API key with `progression` permissions.
- Your Killproof.me profile ID.

## Installation

1. **Clone or Download** the repository.
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   ```
3. **Activate the virtual environment**:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. **Install dependencies**:
   ```bash
   pip install requests beautifulsoup4 rich python-dotenv
   ```

## Configuration

You need to provide your GW2 API Key and your Killproof.me ID to the script.

**Method 1: Using a `.env` file (Recommended for security)**
Create a file named `.env` in the same folder as the script and add your API key:
```ini
GW2_API_KEY="YOUR-GW2-API-KEY-HERE"
```
*Note: Make sure `.env` is added to your `.gitignore` so your key isn't uploaded to a public repository!*

**Method 2: Directly in the script**
If you prefer not to use a `.env` file, you can open `gw2_raid_bounties.py` and replace the empty string on the `DEFAULT_GW2_API_KEY` line:
```python
DEFAULT_GW2_API_KEY = os.environ.get("GW2_API_KEY", "YOUR-GW2-API-KEY-HERE")
```

**Killproof.me ID**
By default, the script looks for `DEFAULT_KP_ID` inside `gw2_raid_bounties.py`. You can change the ID directly in the script (around line 20):
```python
DEFAULT_KP_ID = "your_kp_id"
```

## Usage

Simply run the script from your terminal:
```bash
python gw2_raid_bounties.py
```

You can also pass the KP ID and API key dynamically as command-line arguments:
```bash
python gw2_raid_bounties.py [KP_ID] [GW2_API_KEY]
```
