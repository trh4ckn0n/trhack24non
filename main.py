import time import webbrowser from FlightRadar24.api import FlightRadar24API import questionary from rich.console import Console from rich.panel import Panel from rich.text import Text from rich.live import Live from rich.align import Align

console = Console()

Bannière ASCII animée

banner_frames = [ r"""


---

|  () __ | | __| | __ |  | | | ___  ___  | | ___   __ _ | |  | | ' | |/  |/ _ | | / _ _  / |/ _ / __| | |/ _ \ / ` | |  | | | | | | | (| | (| |  |  __// /| |  _/_ _| | () | (| | ||   ||| |||_,|_,||  _/||_||()|___/ _, | |___/ """, r"""


---

|  () __ | | __| | __ |  | | | ___  ___  | | ___   __ _ | |  | | ' | |/  |/ _ | | / _ _  / |/ _ / __| | |/ _ \ / ` | |  | | | | | | | (| | (| |  |  __// /| |  _/_ _| | () | (| | ||   ||| |||_,|_,||  _/||_||()|___/ _, | |___/ trhacknon - FlightRadar24 Tracker CLI """, ]

def animate_banner(duration=5): start = time.time() i = 0 with Live(console=console, refresh_per_second=2) as live: while time.time() - start < duration: frame = banner_frames[i % len(banner_frames)] text = Text(frame, style="bold cyan") live.update(Align.center(text)) time.sleep(0.5) i += 1 console.clear()

def get_countries_from_airports(airports): countries = set() for airport in airports: country = getattr(airport, "country", None) or airport.get("country") if country: countries.add(country) return sorted(countries)

def choose_country(countries): console.print("[bold yellow]Pays disponibles (extrait) :[/bold yellow] " + ", ".join(countries[:20]) + " ...") while True: country_input = questionary.text("\U0001F30D Entrez un pays (ex: France, Spain, Italy)").ask() if country_input in countries: return country_input console.print(f"[red]Pays '{country_input}' non trouvé, réessayez.[/red]")

def choose_airport(fr, country): airports = fr.get_airports() filtered = [ airport for airport in airports if (getattr(airport, "country", None) or airport.get("country")) == country ] if not filtered: console.print(f"[red]Aucun aéroport trouvé pour le pays {country}[/red]") return None

choices = []
for airport in filtered:
    icao = getattr(airport, "icao", "") or airport.get("icao", "")
    name = getattr(airport, "name", "") or airport.get("name", "")
    iata = getattr(airport, "iata", "") or airport.get("iata", "")
    title = f"{icao} ({iata}) – {name}"
    choices.append(questionary.Choice(title=title, value={"icao": icao, "iata": iata, "name": name}))
return questionary.select("🛫 Sélectionnez un aéroport :", choices=choices).ask()

def list_flights_around_airport(fr, airport): console.print(f"\n[bold green]Chargement des vols autour de l'aéroport {airport['icao']} – {airport['name']}...[/bold green]\n") flights = fr.get_flights(airport["icao"]) console.print(f"Nombre de vols récupérés avec ICAO ({airport['icao']}) : {len(flights)}")

if len(flights) == 0 and airport["iata"]:
    console.print(f"Aucun vol trouvé avec ICAO, tentative avec IATA {airport['iata']}...")
    flights = fr.get_flights(airport["iata"])
    console.print(f"Nombre de vols récupérés avec IATA ({airport['iata']}) : {len(flights)}")

if len(flights) == 0:
    console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
    return []

flight_choices = []
for f in flights:
    callsign = getattr(f, "callsign", None) or getattr(f, "id", "??")
    origin = getattr(f, "origin_airport_icao", "??")
    destination = getattr(f, "destination_airport_icao", "??")
    title = f"{callsign} ({origin} → {destination})"
    flight_choices.append(questionary.Choice(title=title, value=f))
return flight_choices

def track_flight(fr, flight, open_browser=False): flight_id = getattr(flight, "id", None) if not flight_id: console.print("[red]Erreur : impossible de récupérer l'ID du vol.[/red]") return

callsign = getattr(flight, "callsign", None) or getattr(flight, "id", None)
hex_id = getattr(flight, "hex", None)

fr24_url_2d = f"https://www.flightradar24.com/{callsign}/{hex_id}" if callsign and hex_id else None
fr24_url_3d = f"{fr24_url_2d}/3d" if fr24_url_2d else None

if open_browser and fr24_url_2d:
    console.print("[green]Ouverture des URLs Flightradar24 dans votre navigateur...[/green]")
    webbrowser.open(fr24_url_2d)
    if fr24_url_3d:
        time.sleep(1)
        webbrowser.open(fr24_url_3d)

console.print("\n[bold cyan]URLs à copier si besoin :[/bold cyan]")
if fr24_url_2d:
    console.print(f"2D : [underline blue]{fr24_url_2d}[/underline blue]")
if fr24_url_3d:
    console.print(f"3D : [underline blue]{fr24_url_3d}[/underline blue]")

console.print(f"\n🔄 [bold cyan]Tracking du vol {flight_id}[/bold cyan] (Ctrl+C pour arrêter)...\n")

try:
    while True:
        data = fr.get_flight_details(flight)
        if not data:
            console.print("[red]Impossible de récupérer les détails du vol.[/red]")
            break

        callsign = data.get("identification", {}).get("callsign", "N/A")
        status = data.get("status", {}).get("text", "N/A")
        origin_code = data.get("airport", {}).get("origin", {}).get("code", "N/A")
        destination_code = data.get("airport", {}).get("destination", {}).get("code", "N/A")
        trail = data.get("trail", [{}])[-1]
        altitude = trail.get("altitude", "N/A")
        speed = trail.get("groundspeed", "N/A")
        latitude = trail.get("

