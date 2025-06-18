from FlightRadar24 import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
import time
import sys

fr = FlightRadar24API()
console = Console()

def choose_country():
    country = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
    if not country or not country.strip():
        console.print("[red]Vous devez entrer un nom de pays valide.[/red]")
        sys.exit(1)
    return country.strip()

def list_airports(country):
    airports = fr.get_airports()
    filtered = [a for a in airports if getattr(a, "country", "").lower() == country.lower()]
    return filtered

def choose_airport(airports):
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        sys.exit(1)
    choices = [questionary.Choice(f"{a.icao} – {a.name}", a) for a in airports[:30]]
    airport = questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()
    if airport is None:
        console.print("[red]Aéroport non sélectionné.[/red]")
        sys.exit(1)
    return airport

def get_airport_coords(airport):
    # Récupère lat/lon avec plusieurs fallback
    lat = getattr(airport, "lat", None) or getattr(airport, "latitude", None)
    lon = getattr(airport, "lng", None) or getattr(airport, "longitude", None)
    if lat and lon:
        return lat, lon

    pos = getattr(airport, "position", None)
    if pos:
        if isinstance(pos, dict):
            lat = pos.get("lat", None)
            lon = pos.get("lng", None)
        else:
            lat = getattr(pos, "lat", None)
            lon = getattr(pos, "lng", None)
        if lat and lon:
            return lat, lon

    return None, None

def get_nearby_flights(airport, radius_km=100):
    lat, lon = get_airport_coords(airport)
    if lat is None or lon is None:
        console.print("[red]Impossible de récupérer la latitude et longitude de l'aéroport.[/red]")
        sys.exit(1)
    bounds = fr.get_bounds_by_point(lat, lon, radius_km * 1000)
    flights = fr.get_flights(bounds=bounds)
    return flights

def choose_flight(flights):
    if not flights:
        console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
        sys.exit(1)
    choices = []
    for f in flights[:30]:
        callsign = getattr(f, "callsign", "N/A")
        origin = getattr(f, "origin", "??")
        dest = getattr(f, "destination", "??")
        choices.append(questionary.Choice(f"{callsign} ({origin} → {dest})", f))
    flight = questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()
    if flight is None:
        console.print("[red]Vol non sélectionné.[/red]")
        sys.exit(1)
    return flight

def track_flight(flight):
    callsign = getattr(flight, "callsign", "N/A")
    console.print(f"[green]🔄 Tracking du vol {callsign} (CTRL+C pour arrêter)...[/green]")
    try:
        while True:
            data = fr.get_flight_details(callsign)
            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                table = Table(title=f"Position actuelle du vol {callsign}")
                table.add_column("Latitude", justify="right")
                table.add_column("Longitude", justify="right")
                table.add_column("Altitude (ft)", justify="right")
                table.add_column("Vitesse (knots)", justify="right")

                table.add_row(
                    str(pt.get("lat", "?")),
                    str(pt.get("lng", "?")),
                    str(pt.get("alt", "?")),
                    str(pt.get("spd", "?")),
                )
                console.clear()
                console.print(table)
            else:
                console.print("[yellow]Aucune donnée de position disponible pour ce vol.[/yellow]")
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[yellow]📌 Tracking interrompu par l'utilisateur.[/yellow]")

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]\n")
    country = choose_country()
    airports = list_airports(country)
    airport = choose_airport(airports)
    console.print(f"\n[blue]Chargement des vols autour de l'aéroport {airport.icao} – {airport.name}...[/blue]")
    flights = get_nearby_flights(airport)
    flight = choose_flight(flights)
    track_flight(flight)

if __name__ == "__main__":
    main()
