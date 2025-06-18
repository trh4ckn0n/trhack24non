from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
import time
import sys

fr = FlightRadar24API()
console = Console()

def choose_country():
    while True:
        country = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        if country and country.strip():
            return country.strip()
        console.print("[red]Erreur : Veuillez entrer un nom de pays valide.[/red]")

def get_airports_for_country(country):
    try:
        airports = fr.get_airports()
    except Exception as e:
        console.print(f"[red]Erreur lors de la récupération des aéroports : {e}[/red]")
        return []

    filtered = [a for a in airports if a.country and a.country.lower() == country.lower()]
    return filtered

def choose_airport(airports):
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return None
    choices = []
    for a in airports[:30]:
        name = f"{a.icao} – {a.name or 'Sans nom'}"
        choices.append(questionary.Choice(title=name, value=a))
    return questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()

def get_flights_near_airport(airport, radius_km=100):
    if not hasattr(airport, 'position') or not airport.position:
        console.print("[red]Impossible de récupérer la position de l'aéroport.[/red]")
        return []

    lat = airport.position.get('latitude')
    lon = airport.position.get('longitude')
    if lat is None or lon is None:
        console.print("[red]Les coordonnées latitude/longitude sont manquantes.[/red]")
        return []

    try:
        bounds = fr.get_bounds_by_point(lat, lon, radius_km * 1000)
        flights = fr.get_flights(bounds=bounds)
        return flights
    except Exception as e:
        console.print(f"[red]Erreur lors de la récupération des vols : {e}[/red]")
        return []

def choose_flight(flights):
    if not flights:
        console.print("[red]Aucun vol trouvé dans le rayon autour de l'aéroport.[/red]")
        return None

    choices = []
    for f in flights[:30]:
        callsign = getattr(f, 'callsign', None) or "??"
        origin = getattr(f.origin_airport, 'icao', '??') if hasattr(f, 'origin_airport') else "??"
        destination = getattr(f.destination_airport, 'icao', '??') if hasattr(f, 'destination_airport') else "??"
        display = f"{callsign} ({origin} → {destination})"
        choices.append(questionary.Choice(title=display, value=f))
    return questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()

def track_flight(flight):
    if not flight:
        console.print("[red]Aucun vol sélectionné pour le tracking.[/red]")
        return

    flight_id = getattr(flight, 'id', None)
    callsign = getattr(flight, 'callsign', None)

    if not flight_id:
        console.print("[red]Impossible de récupérer l'ID du vol pour le tracking.[/red]")
        return

    console.print(f"[green]🔄 Tracking du vol {callsign or flight_id} (CTRL+C pour arrêter)...[/green]")
    try:
        while True:
            data = fr.get_flight_details(flight_id)
            if not data:
                console.print("[yellow]Aucune donnée détaillée disponible pour ce vol.[/yellow]")
                time.sleep(5)
                continue

            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                table = Table(title=f"Position actuelle du vol {callsign or flight_id}")
                table.add_column("Latitude", justify="center")
                table.add_column("Longitude", justify="center")
                table.add_column("Altitude (ft)", justify="center")
                table.add_column("Vitesse (km/h)", justify="center")

                lat = str(pt.get("lat", "N/A"))
                lon = str(pt.get("lng", "N/A"))
                alt = str(pt.get("alt", "N/A"))
                spd = str(pt.get("spd", "N/A"))

                table.add_row(lat, lon, alt, spd)

                console.clear()
                console.print(table)
            else:
                console.print("[yellow]Aucune donnée de position disponible pour le moment.[/yellow]")

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[yellow]📌 Tracking interrompu par l'utilisateur.[/yellow]")

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]\n")

    country = choose_country()
    airports = get_airports_for_country(country)
    if not airports:
        console.print(f"[red]Aucun aéroport trouvé pour le pays '{country}'.[/red]")
        sys.exit(1)

    airport = choose_airport(airports)
    if not airport:
        console.print("[red]Aucun aéroport sélectionné. Fin du programme.[/red]")
        sys.exit(1)

    console.print(f"\nChargement des vols autour de l'aéroport [bold]{airport.icao} – {airport.name}[/bold]...\n")
    flights = get_flights_near_airport(airport)
    if not flights:
        console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
        sys.exit(1)

    flight = choose_flight(flights)
    if not flight:
        console.print("[red]Aucun vol sélectionné. Fin du programme.[/red]")
        sys.exit(1)

    track_flight(flight)


if __name__ == "__main__":
    main()
