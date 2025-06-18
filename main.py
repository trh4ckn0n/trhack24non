import flightradar24
import json
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

fr = flightradar24.Api()
console = Console()

def list_airports_by_country(country_name):
    try:
        airports_data = fr.get_airports()
        # Debug pour voir la structure (à commenter après)
        # console.print(json.dumps(airports_data, indent=2))
        
        all_airports = airports_data.get('airports', [])
        airports = [a for a in all_airports if a.get("country") == country_name]
        return airports
    except Exception as e:
        console.print(f"[red]Erreur récupération aéroports : {e}[/red]")
        return []

def list_flights_by_airport(airport_code):
    try:
        flights = fr.get_flights(airport_code)
        return flights
    except Exception as e:
        console.print(f"[red]Erreur récupération vols pour {airport_code} : {e}[/red]")
        return []

def display_flights(flights):
    table = Table(title="Vols disponibles")
    table.add_column("Index", justify="center")
    table.add_column("Vol")
    table.add_column("Compagnie")
    table.add_column("Départ")
    table.add_column("Arrivée")

    for i, flight in enumerate(flights):
        table.add_row(
            str(i),
            flight.get("flight", "N/A"),
            flight.get("airline", "N/A"),
            flight.get("airport", {}).get("origin", "N/A"),
            flight.get("airport", {}).get("destination", "N/A"),
        )
    console.print(table)

def track_flight(flight_id, interval=10):
    console.print(f"[bold green]Suivi du vol {flight_id} toutes les {interval} secondes[/bold green]")
    data_log = []

    try:
        while True:
            details = fr.get_flight_details(flight_id)
            if not details:
                console.print("[bold red]Données introuvables pour ce vol.[/bold red]")
                break
            
            aircraft = details.get('aircraft', {})
            trail = details.get('trail', [])
            last_trail = trail[-1] if trail else {}

            info = {
                'time': last_trail.get('ts'),
                'latitude': last_trail.get('lat'),
                'longitude': last_trail.get('lng'),
                'altitude': last_trail.get('alt'),
                'speed': last_trail.get('spd'),
                'heading': last_trail.get('hd'),
            }

            data_log.append(info)

            table = Table(title="Position actuelle du vol")
            for key in info:
                table.add_column(key, justify="center")
            table.add_row(*[str(info[k]) for k in info])
            console.clear()
            console.print(table)

            with open(f"{flight_id}_log.json", "w") as f:
                json.dump(data_log, f, indent=2)

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[bold yellow]Arrêt manuel du tracking.[/bold yellow]")

def main():
    console.print("[bold blue]Bienvenue dans FlightRadar24 Tracker CLI[/bold blue]\n")

    country_name = Prompt.ask("🌍 Entrez un pays (ex: France, Germany, Spain)").strip()

    console.print(f"🔍 Recherche des aéroports pour : {country_name}")
    airports = list_airports_by_country(country_name)

    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return

    # Afficher les aéroports disponibles
    table_airports = Table(title=f"Aéroports en {country_name}")
    table_airports.add_column("Index", justify="center")
    table_airports.add_column("Nom")
    table_airports.add_column("Code ICAO")
    table_airports.add_column("Ville")

    for i, airport in enumerate(airports):
        table_airports.add_row(
            str(i),
            airport.get("name", "N/A"),
            airport.get("icao", "N/A"),
            airport.get("city", "N/A")
        )
    console.print(table_airports)

    # Choix de l'aéroport
    airport_index = Prompt.ask(f"🔢 Choisissez un aéroport (0-{len(airports)-1})", default="0")
    try:
        airport_index = int(airport_index)
        selected_airport = airports[airport_index]
    except (ValueError, IndexError):
        console.print("[red]Sélection invalide.[/red]")
        return

    airport_code = selected_airport.get("icao")
    console.print(f"🔍 Recherche des vols pour l'aéroport : {airport_code}")

    flights = list_flights_by_airport(airport_code)

    if not flights:
        console.print("[red]Aucun vol trouvé pour cet aéroport.[/red]")
        return

    display_flights(flights)

    flight_index = Prompt.ask(f"✈️ Choisissez un vol à suivre (0-{len(flights)-1})", default="0")
    try:
        flight_index = int(flight_index)
        selected_flight = flights[flight_index]
    except (ValueError, IndexError):
        console.print("[red]Sélection invalide.[/red]")
        return

    flight_id = selected_flight.get("id")
    if not flight_id:
        console.print("[red]Impossible de récupérer l'ID du vol sélectionné.[/red]")
        return

    track_flight(flight_id)

if __name__ == "__main__":
    main()
