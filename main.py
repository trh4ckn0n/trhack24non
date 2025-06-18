import flightradar24
import questionary
import json
import time
import pycountry
from rich.console import Console
from rich.table import Table

fr = flightradar24.Api()
console = Console()

def track_flight(flight_id, interval=10):
    console.print(f"[bold green]🛰️ Suivi du vol {flight_id} toutes les {interval} secondes...[/bold green]")
    data_log = []

    try:
        while True:
            details = fr.get_flight_details(flight_id)
            if not details:
                console.print("[bold red]❌ Données introuvables pour ce vol.[/bold red]")
                break

            trail = details.get('trail', [])
            if not trail:
                console.print("[yellow]⚠️ Aucune donnée de trajectoire disponible.[/yellow]")
                break

            current = trail[-1]
            info = {
                'timestamp': current.get('ts'),
                'latitude': current.get('lat'),
                'longitude': current.get('lng'),
                'altitude (ft)': current.get('alt'),
                'vitesse (kt)': current.get('spd'),
                'cap (°)': current.get('hd'),
            }

            data_log.append(info)

            table = Table(title="📡 Position actuelle du vol")
            for key in info:
                table.add_column(key, justify="center")
            table.add_row(*[str(info[k]) for k in info])
            console.clear()
            console.print(table)

            with open(f"{flight_id}_log.json", "w") as f:
                json.dump(data_log, f, indent=2)

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[bold yellow]🛑 Suivi interrompu par l'utilisateur.[/bold yellow]")

def list_flights_by_country():
    country_input = questionary.text("🌍 Entrez un pays (ex: France, Germany, Spain)").ask().strip()

    try:
        country = pycountry.countries.search_fuzzy(country_input)[0]
    except LookupError:
        console.print("[red]❌ Pays non reconnu.[/red]")
        return None

    country_code = country.alpha_2
    console.print(f"[cyan]🔍 Recherche des vols pour : {country.name} ({country_code})[/cyan]")

    try:
        all_airports = fr.get_airports()
        airports = [a for a in all_airports if a.get("country") == country.name]
    except Exception as e:
        console.print(f"[red]Erreur récupération aéroports : {e}[/red]")
    return None

    if not airports:
        console.print("[yellow]⚠️ Aucun aéroport trouvé pour ce pays.[/yellow]")
        return None

    latitudes = [float(a['lat']) for a in airports if 'lat' in a]
    longitudes = [float(a['lon']) for a in airports if 'lon' in a]
    if not latitudes or not longitudes:
        console.print("[red]❌ Coordonnées manquantes.[/red]")
        return None

    north, south = max(latitudes), min(latitudes)
    east, west = max(longitudes), min(longitudes)

    try:
        all_flights = fr.get_flights()
    except Exception as e:
        console.print(f"[red]Erreur récupération des vols : {e}[/red]")
        return None

    flights_in_area = []
    for f in all_flights:
        try:
            lat, lon = float(f['latitude']), float(f['longitude'])
            if south <= lat <= north and west <= lon <= east:
                flights_in_area.append(f)
        except:
            continue

    if not flights_in_area:
        console.print("[yellow]Aucun vol actif trouvé au-dessus de ce pays.[/yellow]")
        return None

    choices = [
        questionary.Choice(
            f"{f['callsign']} | {f.get('origin_airport_iata', '?')} → {f.get('destination_airport_iata', '?')} | Alt: {f.get('altitude')} ft",
            value=f
        ) for f in flights_in_area[:20]
    ]

    selected = questionary.select("✈️ Sélectionne un vol à suivre :", choices=choices).ask()
    return selected['id'] if selected else None

def search_by_flight_number():
    flight_code = questionary.text("🔎 Entrez le numéro du vol (ex: AFR1234)").ask().strip().upper()
    search_results = fr.search(flight_code)

    if not search_results or not search_results['results']:
        console.print("[red]❌ Aucun vol trouvé avec ce numéro.[/red]")
        return None

    flight = search_results['results'][0]
    return flight['id']

if __name__ == "__main__":
    console.print("[bold magenta]✈️ Bienvenue dans FlightRadar24 Tracker CLI[/bold magenta]")

    mode = questionary.select(
        "🔍 Comment veux-tu sélectionner le vol ?",
        choices=[
            "🌍 Explorer les vols actifs par pays",
            "🔢 Rechercher par numéro de vol"
        ]
    ).ask()

    selected_flight = None
    if mode == "🌍 Explorer les vols actifs par pays":
        selected_flight = list_flights_by_country()
    elif mode == "🔢 Rechercher par numéro de vol":
        selected_flight = search_by_flight_number()

    if selected_flight:
        track_flight(selected_flight)
    else:
        console.print("[bold red]❌ Aucun vol sélectionné. Fin du programme.[/bold red]")
