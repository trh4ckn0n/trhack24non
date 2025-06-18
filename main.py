import sys
import time
import questionary
from rich.console import Console
from rich.table import Table
from FlightRadar24.api import FlightRadar24

console = Console()
fr = FlightRadar24()

def choose_country():
    country = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
    if not country:
        console.print("[red]Pays non renseigné.[/red]")
        sys.exit(1)
    return country

def list_airports(country):
    airports = fr.get_airports(country)
    if not airports:
        console.print(f"[red]Aucun aéroport trouvé pour {country}.[/red]")
        sys.exit(1)
    return airports

def choose_airport(airports):
    choices = []
    for airport in airports:
        # Certains aéroports n'ont pas 'icao' ou 'name', on sécurise
        icao = getattr(airport, "icao", "???")
        name = getattr(airport, "name", "Inconnu")
        choices.append(questionary.Choice(f"{icao} – {name}", airport))
    airport = questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()
    if not airport:
        console.print("[red]Aéroport non sélectionné.[/red]")
        sys.exit(1)
    return airport

def get_nearby_flights(airport):
    # On récupère la position de l'aéroport
    if not hasattr(airport, "position") or airport.position is None:
        console.print("[red]Impossible de récupérer la position de l'aéroport.[/red]")
        sys.exit(1)
    pos = airport.position
    flights = fr.get_flights(lat=pos["lat"], lng=pos["lng"])
    if not flights:
        console.print("[red]Aucun vol autour de cet aéroport.[/red]")
        sys.exit(1)
    return flights

def choose_flight(flights):
    choices = []
    for f in flights[:30]:
        callsign = getattr(f, "callsign", "N/A")
        origin = getattr(f, "origin", "??")
        destination = getattr(f, "destination", "??")
        choices.append(questionary.Choice(f"{callsign} ({origin} → {destination})", f))
    flight = questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()
    if not flight:
        console.print("[red]Vol non sélectionné.[/red]")
        sys.exit(1)
    return flight

def track_flight(flight):
    console.print(f"[green]🔄 Tracking du vol {flight.id} (CTRL+C pour arrêter)...[/green]")
    try:
        while True:
            data = fr.get_flight_details(flight)  # On passe l'objet Flight complet
            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                table = Table(title=f"Position actuelle du vol {flight.callsign}")
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
    track_flight(flight)  # On passe l'objet Flight complet ici

if __name__ == "__main__":
    main()
