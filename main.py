from FlightRadar24 import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
import time

fr = FlightRadar24API()
console = Console()

def choose_country():
    country = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
    if not country:
        console.print("[red]Erreur : pays non renseigné.[/red]")
        exit(1)
    return country.strip()

def list_airports(country):
    airports = fr.get_airports()
    filtered = [a for a in airports if a.country and a.country.lower() == country.lower()]
    return filtered

def choose_airport(airports):
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        exit(1)
    choices = [questionary.Choice(f"{a.icao} – {a.name}", value=a) for a in airports[:30]]
    selected = questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()
    if not selected:
        console.print("[red]Erreur : aucun aéroport sélectionné.[/red]")
        exit(1)
    return selected

def get_nearby_flights(airport, radius_km=100):
    # Récupère l'aéroport précis avec lat/lon
    airport_detail = fr.get_airport(code=airport.icao)
    if not airport_detail or not hasattr(airport_detail, 'lat') or not hasattr(airport_detail, 'lon'):
        console.print("[red]Impossible de récupérer les coordonnées de l'aéroport.[/red]")
        exit(1)
    bounds = fr.get_bounds_by_point(airport_detail.lat, airport_detail.lon, radius_km * 1000)
    flights = fr.get_flights(bounds=bounds)
    return flights

def choose_flight(flights):
    if not flights:
        console.print("[red]Aucun vol trouvé dans le rayon autour de l'aéroport.[/red]")
        exit(1)
    choices = [
        questionary.Choice(f"{f.callsign} – {f.aircraft_model or 'Modèle inconnu'}", value=f)
        for f in flights[:30]
    ]
    selected = questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()
    if not selected:
        console.print("[red]Erreur : aucun vol sélectionné.[/red]")
        exit(1)
    return selected

def track_flight(flight):
    console.print(f"[green]🔄 Tracking du vol {flight.callsign} (CTRL+C pour arrêter)...[/green]")
    try:
        while True:
            data = fr.get_flight_details(flight.id)
            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                table = Table(title=f"Position actuelle du vol {flight.callsign}")
                table.add_column("Latitude", justify="right")
                table.add_column("Longitude", justify="right")
                table.add_column("Altitude (ft)", justify="right")
                table.add_column("Vitesse (knots)", justify="right")
                table.add_row(
                    f"{pt.get('lat', '?')}",
                    f"{pt.get('lng', '?')}",
                    f"{pt.get('alt', '?')}",
                    f"{pt.get('spd', '?')}"
                )
                console.clear()
                console.print(table)
            else:
                console.print("[yellow]Aucune donnée de position disponible pour ce vol.[/yellow]")
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("[yellow]📌 Tracking interrompu par l'utilisateur.[/yellow]")

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]\n")

    country = choose_country()
    airports = list_airports(country)

    airport = choose_airport(airports)
    flights = get_nearby_flights(airport)

    flight = choose_flight(flights)
    track_flight(flight)

if __name__ == "__main__":
    main()
