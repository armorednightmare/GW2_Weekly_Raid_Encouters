import sys
import requests
import datetime
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

# Force UTF-8 output on Windows to support Unicode/emoji characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DEFAULT_KP_ID = "257ex"
DEFAULT_GW2_API_KEY = os.environ.get("GW2_API_KEY", "")
WIKI_URL = "https://wiki.guildwars2.com/wiki/Daily_Raid_Bounties"

# --- FALLBACK ROTATION DATA ---
FALLBACK_ROTATION = {
    "Boss 1": { "cycle": 6, "bosses": ["Shiverpeaks Pass", "Voice and Claw", "Fraenir of Jormag", "Gorseval", "Cairn", "Mursaat Overseer"] },
    "Boss 2": { "cycle": 12, "bosses": ["Aetherblade Hideout", "Cardinal Sabir", "Whisper of Jormag", "Vale Guardian", "Cosmic Observatory", "Cold War", "Boneskinner", "Sabetha", "Xunlai Jade Junkyard", "Temple of Febe", "Keep Construct", "Kela"] },
    "Boss 3": { "cycle": 12, "bosses": ["Slothasor", "Matthias", "Xera", "Samarog", "Conjured Amalgamate", "Twin Largos", "Decima, the Stormsinger", "Cardinal Adina", "Old Lion's Court", "Ura, the Steamshrieker", "Kaineng Overlook", "Deimos"] },
    "Boss 4": { "cycle": 6, "bosses": ["Qadim", "Qadim the Peerless", "Soulless Horror", "Harvest Temple", "Dhuum", "Greer, the Blightbringer"] }
}

# --- MAPPING TO API ---
MAPPING = {
    # Raids (Key in api/clear JSON)
    "Gorseval": ("raid", "Gorseval"),
    "Cairn": ("raid", "Cairn"),
    "Mursaat Overseer": ("raid", "Mursaat Overseer"),
    "Cardinal Sabir": ("raid", "Cardinal Sabir"),
    "Vale Guardian": ("raid", "Vale Guardian"),
    "Sabetha": ("raid", "Sabetha"),
    "Keep Construct": ("raid", "Keep Construct"),
    "Slothasor": ("raid", "Slothasor"),
    "Matthias": ("raid", "Matthias"),
    "Xera": ("raid", "Xera"),
    "Samarog": ("raid", "Samarog"),
    "Conjured Amalgamate": ("raid", "Conjured Amalgamate"),
    "Twin Largos": ("raid", "Twin Largos"),
    "Decima, the Stormsinger": ("raid", "Decima, the Stormsinger"),
    "Cardinal Adina": ("raid", "Cardinal Adina"),
    "Ura, the Steamshrieker": ("raid", "Ura, the Steamshrieker"),
    "Deimos": ("raid", "Deimos"),
    "Qadim": ("raid", "Qadim"),
    "Qadim the Peerless": ("raid", "Qadim the Peerless"),
    "Soulless Horror": ("raid", "Soulless Horror"),
    "Dhuum": ("raid", "Voice in the Void"),
    # Dhuum (Wiki) <-> Voice in the Void (Wing List/API) have no common words for fuzzy matching
    "Voice in the Void": ("raid", "Voice in the Void"),
    "Greer, the Blightbringer": ("raid", "Greer, the Blightbringer"),
    
    # Event-style / Other Raids (Will not be in Wiki rotation, but used for full missing list)
    "Spirit Woods": ("raid", "Spirit Woods"),
    "Bandit Trio": ("raid", "Bandit Trio"),
    "Escort": ("raid", "Escort"),
    "Twisted Castle": ("raid", "Twisted Castle"),
    "River of Souls": ("raid", "River of Souls"),
    "Statues of Grenth": ("raid", "Statues of Grenth"),
    "Gate": ("raid", "Gate"),
    "Ruined Camp": ("raid", "Ruined Camp"),

    # IBS Strikes
    "Shiverpeaks Pass": ("strike", "Shiverpeaks Pass"),
    "Voice and Claw": ("strike", "Voice and Claw"),
    "Kodans": ("strike", "Voice and Claw"),
    "Fraenir of Jormag": ("strike", "Fraenir of Jormag"),
    "Whisper of Jormag": ("strike", "Whisper of Jormag"),
    "Boneskinner": ("strike", "Boneskinner"),
    "Cold War": ("strike", "Cold War"),
    # EoD Strikes
    "Aetherblade Hideout": ("strike", "Aetherblade Hideout"),
    "Mai Trin": ("strike", "Aetherblade Hideout"),
    "Xunlai Jade Junkyard": ("strike", "Xunlai Jade Junkyard"),
    "Ankka": ("strike", "Xunlai Jade Junkyard"),
    "Kaineng Overlook": ("strike", "Kaineng Overlook"),
    "Li": ("strike", "Kaineng Overlook"),
    "Harvest Temple": ("strike", "Harvest Temple"),
    "The Void": ("strike", "Harvest Temple"),
    "Old Lion's Court": ("strike", "Old Lion's Court"),
    "OLC": ("strike", "Old Lion's Court"),
    # SotO Strikes
    "Cosmic Observatory": ("strike", "Cosmic Observatory"),
    "Dagda": ("strike", "Cosmic Observatory"),
    "Temple of Febe": ("strike", "Temple of Febe"),
    "Cerus": ("strike", "Temple of Febe"),
    # JW Strikes
    "Guardian's Glade": ("strike", "Guardian's Glade"),
    "Kela": ("strike", "Guardian's Glade"),
}

# --- ALL RAID BOSSES (Wings 1-8) ---
ALL_RAID_WINGS = {
    "Wing 1: Spirit Vale": ["Vale Guardian", "Spirit Woods", "Gorseval", "Sabetha"],
    "Wing 2: Salvation Pass": ["Slothasor", "Bandit Trio", "Matthias"],
    "Wing 3: Stronghold of the Faithful": ["Escort", "Keep Construct", "Twisted Castle", "Xera"],
    "Wing 4: Bastion of the Penitent": ["Cairn", "Mursaat Overseer", "Samarog", "Deimos"],
    "Wing 5: Hall of Chains": ["Soulless Horror", "River of Souls", "Statues of Grenth", "Voice in the Void"],
    "Wing 6: Mythwright Gambit": ["Conjured Amalgamate", "Twin Largos", "Qadim"],
    "Wing 7: The Key of Ahdashim": ["Gate", "Cardinal Adina", "Cardinal Sabir", "Qadim the Peerless"],
    "Wing 8: Mount Balrior": ["Ruined Camp", "Greer, the Blightbringer", "Decima, the Stormsinger", "Ura, the Steamshrieker"]
}

# --- ALL STRIKE MISSIONS ---
ALL_STRIKES = {
    "IBS Strikes": ["Shiverpeaks Pass", "Voice and Claw", "Fraenir of Jormag", "Whisper of Jormag", "Boneskinner", "Cold War"],
    "EoD Strikes": ["Aetherblade Hideout", "Xunlai Jade Junkyard", "Kaineng Overlook", "Harvest Temple", "Old Lion's Court"],
    "SotO Strikes": ["Cosmic Observatory", "Temple of Febe"],
    "JW Strikes": ["Guardian's Glade"]
}

def fetch_wiki_rotation():
    """Scrapes the bounty rotation directly from GW2 Wiki."""
    try:
        res = requests.get(WIKI_URL, timeout=10)
        if res.status_code != 200:
            return None
        
        soup = BeautifulSoup(res.text, "html.parser")
        tables = soup.find_all("table", class_="mech1")
        
        if len(tables) < 4:
            return None
            
        dynamic_rotation = {}
        for i, table in enumerate(tables[:4]):
            boss_key = f"Boss {i+1}"
            bosses = []
            for row in table.find_all("tr")[1:]:
                td = row.find("td")
                if td:
                    links = td.find_all("a")
                    if links:
                        boss_name = links[-1].text.strip()
                        if boss_name == "Voice and Claw of the Fallen":
                            boss_name = "Voice and Claw"
                        bosses.append(boss_name)
            
            if bosses:
                dynamic_rotation[boss_key] = {
                    "cycle": len(bosses),
                    "bosses": bosses
                }
        
        return dynamic_rotation if len(dynamic_rotation) == 4 else None
    except Exception:
        return None

def get_bounties_for_date(rotation_data, target_date):
    """Calculates bounties for a specific UTC date (Jan 1 = 0)."""
    doy = target_date.timetuple().tm_yday - 1
    is_leap = (target_date.year % 4 == 0 and (target_date.year % 100 != 0 or target_date.year % 400 == 0))
    if not is_leap and doy >= 59:
        doy += 1
        
    bounties = {}
    for key, data in rotation_data.items():
        idx = doy % data["cycle"]
        bounties[key] = data["bosses"][idx]
    
    return bounties

def fetch_clear_data(kp_id):
    """Fetches clear data from Killproof.me API."""
    try:
        url = f"https://killproof.me/api/clear/{kp_id}"
        res = requests.get(url, timeout=10)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def fetch_gw2_api_clears(api_key):
    """Fetches strike/raid clear data from official GW2 API."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        result = {}

        # 1. Fetch Strikes (Achievement 9125)
        ach_id = 9125
        res_static = requests.get(f"https://api.guildwars2.com/v2/achievements?ids={ach_id}", timeout=10)
        if res_static.status_code == 200:
            static_data = res_static.json()[0]
            bits_map = {idx: bit["text"] for idx, bit in enumerate(static_data.get("bits", []))}

            res_acc = requests.get("https://api.guildwars2.com/v2/account/achievements", headers=headers, timeout=10)
            if res_acc.status_code == 200:
                acc_data = res_acc.json()
                my_progress = next((ach for ach in acc_data if ach["id"] == ach_id), None)
                
                gw2_api_strikes = {}
                if my_progress:
                    completed_bits = []
                    if my_progress.get("done", False):
                        completed_bits = list(bits_map.keys())
                    elif "bits" in my_progress:
                        completed_bits = my_progress["bits"]
                        
                    for bit in completed_bits:
                        if bit in bits_map:
                            strike_name = bits_map[bit]
                            if strike_name == "Voice of the Fallen and Claw of the Fallen":
                                strike_name = "Voice and Claw"
                            gw2_api_strikes[strike_name] = 1
                result["GW2_API_Strikes"] = gw2_api_strikes

        # 2. Fetch Raids (account/raids)
        GW2_API_RAID_MAP = {
            "vale_guardian": "Vale Guardian",
            "spirit_woods": "Spirit Woods",
            "gorseval": "Gorseval",
            "sabetha": "Sabetha",
            "slothasor": "Slothasor",
            "bandit_trio": "Bandit Trio",
            "matthias": "Matthias",
            "escort": "Escort",
            "keep_construct": "Keep Construct",
            "twisted_castle": "Twisted Castle",
            "xera": "Xera",
            "cairn": "Cairn",
            "mursaat_overseer": "Mursaat Overseer",
            "samarog": "Samarog",
            "deimos": "Deimos",
            "soulless_horror": "Soulless Horror",
            "river_of_souls": "River of Souls",
            "statues_of_grenth": "Statues of Grenth",
            "voice_in_the_void": "Voice in the Void",
            "conjured_amalgamate": "Conjured Amalgamate",
            "twin_largos": "Twin Largos",
            "qadim": "Qadim",
            "gate": "Gate",
            "adina": "Cardinal Adina",
            "sabir": "Cardinal Sabir",
            "qadim_the_peerless": "Qadim the Peerless",
            "greer": "Greer, the Blightbringer",
            "decima": "Decima, the Stormsinger",
            "ura": "Ura, the Steamshrieker",
            "ruined_camp": "Ruined Camp"
        }
        res_raids = requests.get("https://api.guildwars2.com/v2/account/raids", headers=headers, timeout=10)
        if res_raids.status_code == 200:
            gw2_api_raids = {}
            for raid_id in res_raids.json():
                if raid_id in GW2_API_RAID_MAP:
                    gw2_api_raids[GW2_API_RAID_MAP[raid_id]] = 1
                else:
                    gw2_api_raids[raid_id.replace("_", " ").title()] = 1
            result["GW2_API_Raids"] = gw2_api_raids
            
        return result if result else None
    except Exception:
        return None

def get_mapping_data(boss_name):
    """Resolves a boss name to its (category, api_key) using MAPPING."""
    name_low = boss_name.lower()
    
    # 1. Try exact match (case insensitive)
    for m_name, (cat, key) in MAPPING.items():
        if m_name.lower() == name_low:
            return cat, key
            
    # 2. Try fuzzy match - sort by length descending to prefer more specific matches
    # This prevents "Qadim" matching "Qadim the Peerless" incorrectly.
    sorted_items = sorted(MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
    for m_name, (cat, key) in sorted_items:
        m_low = m_name.lower()
        if m_low in name_low or name_low in m_low:
            return cat, key
            
    return None, None

def get_api_key(boss_name):
    """Resolves a boss name to its API key used in Killproof.me clears."""
    cat, key = get_mapping_data(boss_name)
    return key if key else boss_name

def check_boss_status(boss_name, clear_data):
    """Returns (status, category) where status is '✅ Done   ', '✅ Done ✔ ', or '❌ Missing'."""
    category, api_key = get_mapping_data(boss_name)
    
    if not category:
        category = "unknown"
    if not api_key:
        api_key = boss_name
                
    is_kp_done = False
    is_gw2_done = False

    for category_name, bosses in clear_data.items():
        is_gw2_api_category = category_name.startswith("GW2_API_")
        
        if isinstance(bosses, list):
            for boss_obj in bosses:
                for k, v in boss_obj.items():
                    if api_key.lower() == k.lower() and v == 1:
                        if is_gw2_api_category:
                            is_gw2_done = True
                        else:
                            is_kp_done = True
        elif isinstance(bosses, dict):
            for k, v in bosses.items():
                if api_key.lower() == k.lower() and v == 1:
                    if is_gw2_api_category:
                        is_gw2_done = True
                    else:
                        is_kp_done = True
                        
    if is_gw2_done or is_kp_done:
        return ("✅ Done ✔ ", category) if is_kp_done else ("✅ Done   ", category)
        
    return "❌ Missing", category

def generate_overview_table(title, data_dict, upcoming_bounties, clear_data, today_name=None):
    """Generates a rich Table for a given set of encounters (Raid Wings or Strikes)."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Encounter", style="bold white")
    table.add_column("Status", justify="left", no_wrap=True)
    table.add_column("Upcoming Bounty", style="italic cyan", justify="center")

    for section_name, bosses in data_dict.items():
        table.add_section()
        table.add_row(f"[bold cyan]{section_name}[/bold cyan]", "", "")
        for boss in bosses:
            status, _ = check_boss_status(boss, clear_data)
            is_completed = ("Done" in status or "✅" in status)

            # Find upcoming bounty days for this boss
            boss_api_key = get_api_key(boss).lower()
            bounty_days = upcoming_bounties.get(boss_api_key, [])

            formatted_days = []
            for d in bounty_days:
                if d == today_name:
                    formatted_days.append(f"[bold green]({d})[/bold green]")
                else:
                    formatted_days.append(f"({d})")

            bounty_note = " ".join(formatted_days) if formatted_days else "[dim]—[/dim]"
            status_str = f"[green]{status}[/green]" if is_completed else f"[red]{status}[/red]"

            table.add_row(f"  {boss}", status_str, bounty_note)
    return table

def get_key_press(prompt):
    print(prompt, end="", flush=True)
    try:
        import msvcrt
        char = msvcrt.getch()
        if char in (b'\x00', b'\xe0'):
            msvcrt.getch()  # consume second byte of special keys
            print()
            return ""
        val = char.decode('utf-8', errors='ignore').lower()
        print()
        return val
    except ImportError:
        # Fallback to standard input on non-Windows
        val = input().strip().lower()
        return val

def main():
    console = Console()
    kp_id = DEFAULT_KP_ID
    gw2_api_key = DEFAULT_GW2_API_KEY if DEFAULT_GW2_API_KEY else None
    
    if len(sys.argv) > 1:
        kp_id = sys.argv[1]
    if len(sys.argv) > 2:
        gw2_api_key = sys.argv[2]
    
    while True:
        console.clear()
        console.print(Panel.fit(f"[bold green]GW2 Daily Bounty Tracker[/bold green]\nProfile: [cyan]{kp_id}[/cyan]", border_style="magenta"))
        
        # 1. Fetch Rotation
        with console.status("[bold yellow]Fetching Wiki rotation...[/bold yellow]"):
            rotation_data = fetch_wiki_rotation() or FALLBACK_ROTATION
                
        # 2. Daily & Weekly Logic
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        days_since_monday = now_utc.weekday()
        monday_reset = now_utc - datetime.timedelta(days=days_since_monday)
        
        with console.status("[bold yellow]Fetching Killproof.me clears...[/bold yellow]"):
            clear_data = fetch_clear_data(kp_id)
        
        if not clear_data and not gw2_api_key:
            console.print("[bold red]Error: Could not retrieve clear data from Killproof.me.[/bold red]")
            user_choice = get_key_press('\nPress [R] to Retry, [Q] to Quit: ')
            if user_choice == 'q':
                break
            continue
            
        if not clear_data:
            clear_data = {}

        if gw2_api_key:
            with console.status("[bold yellow]Fetching official GW2 API clears...[/bold yellow]"):
                gw2_clears = fetch_gw2_api_clears(gw2_api_key)
                if gw2_clears:
                    clear_data.update(gw2_clears)
                else:
                    console.print("[bold red]Warning: Could not retrieve or parse official GW2 API data.[/bold red]")

        # --- VIEW 1: TODAY'S BOUNTIES ---
        today_bounties = get_bounties_for_date(rotation_data, now_utc)
        table_today = Table(title=f"1) Daily Bounties: {now_utc.strftime('%Y-%m-%d')}", show_header=True, header_style="bold cyan")
        table_today.add_column("Category", style="dim")
        table_today.add_column("Bounty Boss", style="bold white")
        table_today.add_column("Status", justify="left")

        for cat in ["Boss 1", "Boss 2", "Boss 3", "Boss 4"]:
            boss = today_bounties[cat]
            status, category = check_boss_status(boss, clear_data)
            
            status_style = "green" if "✅" in status else "red"
            display_boss = boss + " [dim](Strike)[/dim]" if category == "strike" else boss
            table_today.add_row(cat, display_boss, f"[{status_style}]{status}[/{status_style}]")
        
        # --- VIEW 2: WEEKLY MISSING BOUNTIES (Mon -> Today) ---
        table_weekly = Table(title="2) Missing Bounties from this week (Mon -> Today)", show_header=True, header_style="bold yellow")
        table_weekly.add_column("Date", style="dim")
        table_weekly.add_column("Bounty Boss", style="bold white")
        table_weekly.add_column("Status", justify="left")

        has_missing_weekly = False
        for i in range(days_since_monday + 1):
            target_date = monday_reset + datetime.timedelta(days=i)
            day_bounties = get_bounties_for_date(rotation_data, target_date)
            for boss in day_bounties.values():
                status, category = check_boss_status(boss, clear_data)
                if "Missing" in status:
                    display_boss = boss + " [dim](Strike)[/dim]" if category == "strike" else boss
                    table_weekly.add_row(target_date.strftime("%a %d.%m"), display_boss, f"[red]{status}[/red]")
                    has_missing_weekly = True
        
        view2_renderable = table_weekly if has_missing_weekly else Panel("[green]✔ No missing bounties from earlier this week![/green]", border_style="green")
        
        # --- SHARED DATA FOR OVERVIEW TABLES ---
        upcoming_bounties = {}  # api_key (lower) -> List[day_str]
        for i in range(days_since_monday, 7):
            target_date = monday_reset + datetime.timedelta(days=i)
            day_name = target_date.strftime("%a")
            day_bounties = get_bounties_for_date(rotation_data, target_date)
            for boss in day_bounties.values():
                _, cat_key = get_mapping_data(boss)
                key = (cat_key or boss).lower()
                if key not in upcoming_bounties:
                    upcoming_bounties[key] = []
                upcoming_bounties[key].append(day_name)

        # --- VIEW 3: COMPLETE WEEKLY RAID OVERVIEW ---
        today_name = now_utc.strftime("%a")
        table_raids = generate_overview_table("3) All Raid Bosses – Weekly Overview", ALL_RAID_WINGS, upcoming_bounties, clear_data, today_name)

        # --- VIEW 4: COMPLETE WEEKLY STRIKE OVERVIEW ---
        table_strikes = generate_overview_table("4) All Strike Missions – Weekly Overview", ALL_STRIKES, upcoming_bounties, clear_data, today_name)

        # Combine into a single grid to ensure consistent column alignment
        grid = Table.grid(padding=(1, 4))
        grid.add_row(table_today, view2_renderable)
        grid.add_row(table_raids, table_strikes)
        console.print(grid)

        console.print("[dim]* ✔ indicates the clear is also registered on Killproof.me[/dim]\n")

        user_choice = get_key_press("Press [R] to Refresh, [Q] to Quit: ")
        if user_choice == 'q':
            break

if __name__ == "__main__":
    main()
