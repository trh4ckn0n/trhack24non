import time
import json
import pycountry
from flightradar24 import Api
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt

console = Console()
fr = Api()

def get_country_code_by_name(name):
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2, country.name
    except LookupError:
        return None, None

def list_airports_by_country(country_name):
    try:
        all_airports = fr.get_airports()
        airports = [a for a in all_airports if a.get("country") == country_name]
        return airports
    except Exception as e:
        console.print(f"[red]Erreur récupération aéroports : {e}[/red]")
        return []

def get_flights_by_airports(airports):
    flights = []
    for airport in airports:
        icao = airport.get("icao")
        if not icao:
            continue
        try:
            airport_flights = fr.get_flights(icao)
            if airport_flights:
                flights.extend(airport_flights)
        except Exception:
            # skip if API fails for an airport
            continue
    return flights

def select_flight(flights):
    if not flights:
        console.print("[red]Aucun vol trouvé.[/red]")
        return None

    table = Table(title="Vols actifs")
    table.add_column("Index", justify="center", style="cyan")
    table.add_column("Flight", style="magenta")
    table.add_column("Airline", style="green")
    table.add_column("Origin", style="yellow")
    table.add_column("Destination", style="yellow")

    for idx, flight in enumerate(flights, start=1):
        table.add_row(
            str(idx),
            flight.get("flight", "N/A"),
            flight.get("airline", {}).get("name", "N/A"),
            flight.get("airport", {}).get("origin", {}).get("name", "N/A"),
            flight.get("airport", {}).get("destination", {}).get("name", "N/A"),
        )

    console.print(table)

    while True:
        choice = IntPrompt.ask("Sélectionne un vol par son index (0 pour annuler)", default=0)
        if choice == 0:
            return None
        if 1 <= choice <= len(flights):
            return flights[choice - 1]
        else:
            console.print("[red]Choix invalide. Réessaie.[/red]")

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
            last_pos = trail[-1] if trail else {}

            info = {
                'time': last_pos.get('ts'),
                'latitude': last_pos.get('lat'),
                'longitude': last_pos.get('lng'),
                'altitude': last_pos.get('alt'),
                'speed': last_pos.get('spd'),
                'heading': last_pos.get('hd'),
                'aircraft_model': aircraft.get('model', {}).get('code', 'N/A')
            }

            data_log.append(info)

            table = Table(title=f"Position actuelle du vol {flight_id}")
            for key in info:
                table.add_column(key.capitalize(), justify="center")
            table.add_row(*[str(info[k]) for k in info])
            
            console.clear()
            console.print(table)

            # Sauvegarde dans un fichier JSON
            with open(f"{flight_id}_log.json", "w") as f:
                json.dump(data_log, f, indent=2)

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("[bold yellow]Arrêt manuel du tracking.[/bold yellow]")

def main():
    console.print("[bold blue]Bienvenue dans FlightRadar24 Tracker CLI[/bold blue]\n")

    country_input = Prompt.ask("🌍 Entrez un pays (ex: France, Germany, Spain)").strip()
    country_code, country_name = get_country_code_by_name(country_input)

    if not country_code:
        console.print(f"[red]Pays '{country_input}' inconnu.[/red]")
        return

    console.print(f"🔍 Recherche des aéroports pour : {country_name} ({country_code})")

    airports = list_airports_by_country(country_name)
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return

    console.print(f"[green]Trouvé {len(airports)} aéroports dans {country_name}.[/green]")
    console.print("🔍 Recherche des vols actifs... cela peut prendre quelques secondes...")

    flights = get_flights_by_airports(airports)
    if not flights:
        console.print("[red]Aucun vol actif trouvé sur ces aéroports.[/red]")
        return

    selected_flight = select_flight(flights)
    if not selected_flight:
        console.print("❌ Aucun vol sélectionné. Fin du programme.")
        return

    flight_id = selected_flight.get("id")
    if not flight_id:
        console.print("[red]Impossible de récupérer l'ID du vol sélectionné.[/red]")
        return

    track_flight(flight_id, interval=10)

if __name__ == "__main__":
    main()
