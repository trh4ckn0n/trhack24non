from FlightRadar24 import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
import time

fr = FlightRadar24API()
console = Console()

def choose_country():
    return questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask().strip()

def list_airports(country):
    airports = fr.get_airports()
    return [a for a in airports if a.country.lower() == country.lower()]

def choose_airport(airports):
    return questionary.select(
        "🛫 Sélectionne un aéroport :",
        choices=[questionary.Choice(f"{a.icao} – {a.name}", a) for a in airports[:20]]
    ).ask()

def get_nearby_flights(airport, radius_km=100):
    fr_bounds = fr.get_bounds_by_point(airport.latitude, airport.longitude, radius_km * 1000)
    return fr.get_flights(bounds=fr_bounds)

def choose_flight(flights):
    return questionary.select(
        "✈️ Sélectionne un vol :",
        choices=[questionary.Choice(f"{f.flight} – {f.airline['name']}", f) for f in flights[:20]]
    ).ask()

def track_flight(flight_id):
    console.print(f"[green]🔄 Tracking du vol {flight_id} (CTRL+C pour arrêter)…[/green]")
    try:
        while True:
            data = fr.get_flight_details(flight_id)
            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                t = Table()
                t.add_column("Lat"); t.add_column("Lon")
                t.add_column("Alt"); t.add_column("Spd")
                t.add_row(str(pt["lat"]), str(pt["lng"]), str(pt["alt"]), str(pt["spd"]))
                console.clear(); console.print(t)
            else:
                console.print("[yellow]Aucune donnée de position disponible.[/yellow]")
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("[yellow]📌 Tracking interrompu.[/yellow]")

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]")
    country = choose_country()
    airports = list_airports(country)

    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return

    selected_airport = choose_airport(airports)

    # Récupère les infos précises de l'aéroport (latitude, longitude, etc.)
    airport = fr.get_airport(code=selected_airport.icao)
    flights = get_nearby_flights(airport)

    if not flights:
        console.print("[red]Aucun vol trouvé dans un rayon autour de l'aéroport.[/red]")
        return

    flight = choose_flight(flights)
    track_flight(flight.id)

if __name__ == "__main__":
    main()
