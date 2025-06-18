import flightradar24
import json
import time
from rich.console import Console
from rich.table import Table
import questionary

fr = flightradar24.Api()
console = Console()

def track_flight(flight_id, interval=10):
    console.print(f"[bold green]Suivi du vol {flight_id} toutes les {interval} secondes[/bold green]")
    data_log = []

    try:
        while True:
            details = fr.get_flight_details(flight_id)
            if not details:
                console.print("[bold red]Données introuvables pour ce vol.[/bold red]")
                break

            trail = details['trail'][-1] if details['trail'] else {}

            info = {
                'time': trail.get('ts'),
                'latitude': trail.get('lat'),
                'longitude': trail.get('lng'),
                'altitude': trail.get('alt'),
                'speed': trail.get('spd'),
                'heading': trail.get('hd'),
            }

            data_log.append(info)

            table = Table(title="📍 Position actuelle du vol")
            for key in info:
                table.add_column(key, justify="center")
            table.add_row(*[str(info[k]) for k in info])
            console.clear()
            console.print(table)

            with open(f"{flight_id}_log.json", "w") as f:
                json.dump(data_log, f, indent=2)

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[bold yellow]🛑 Arrêt manuel du tracking.[/bold yellow]")

def list_flights_by_area_and_filter():
    # Demander une zone géographique (valeurs par défaut : Europe)
    north = float(questionary.text("Latitude nord (ex: 55)").ask() or 55)
    south = float(questionary.text("Latitude sud (ex: 40)").ask() or 40)
    west = float(questionary.text("Longitude ouest (ex: -5)").ask() or -5)
    east = float(questionary.text("Longitude est (ex: 15)").ask() or 15)

    flights = fr.get_flights(bounds=(north, west, south, east))
    console.print(f"[bold blue]🛫 {len(flights)} vols trouvés dans cette zone[/bold blue]")

    if not flights:
        console.print("[bold red]Aucun vol actif dans cette zone.[/bold red]")
        return None

    # Filtrage
    filter_mode = questionary.select(
        "Filtrer les vols par :",
        choices=["Aucun filtre", "Origine", "Destination"]
    ).ask()

    keyword = ""
    if filter_mode != "Aucun filtre":
        keyword = questionary.text("Entrez le nom ou le code IATA (ex: CDG, JFK)").ask().lower()

    # Liste lisible
    filtered_flights = []
    for f in flights:
        origin = f.get('origin', '') or ''
        destination = f.get('destination', '') or ''
        if filter_mode == "Origine" and keyword not in origin.lower():
            continue
        if filter_mode == "Destination" and keyword not in destination.lower():
            continue

        title = f"{f['callsign']} | {origin} → {destination} | {f.get('aircraft_code', '')}"
        filtered_flights.append({"name": title, "value": f['id']})

    if not filtered_flights:
        console.print("[bold red]Aucun vol ne correspond à ce filtre.[/bold red]")
        return None

    selected_id = questionary.select("✈️ Sélectionne un vol à suivre :", choices=filtered_flights).ask()
    return selected_id

if __name__ == "__main__":
    mode = questionary.select(
        "🔍 Comment veux-tu sélectionner le vol ?",
        choices=["Recherche par numéro", "Explorer les vols actifs par zone"]
    ).ask()

    if mode == "Recherche par numéro":
        flight_code = input("🔎 Entrez le numéro de vol (ex: AFR1234) : ").strip().upper()
        search_results = fr.search(flight_code)

        if not search_results or not search_results['results']:
            console.print("[bold red]Aucun vol trouvé avec ce code.[/bold red]")
        else:
            flights = search_results['results']
            options = []

            for f in flights:
                label = f"{f.get('airline', {}).get('name', '?')} | {f.get('flight', {}).get('iata', '??')} | {f.get('airport', {}).get('origin', {}).get('code', '???')} → {f.get('airport', {}).get('destination', {}).get('code', '???')} | {f.get('status', 'N/A')}"
                options.append({"name": label, "value": f['id']})

            selected_id = questionary.select("✈️ Sélectionne un vol :", choices=options).ask()
            track_flight(selected_id)

    else:
        flight_id = list_flights_by_area_and_filter()
        if flight_id:
            track_flight(flight_id)
