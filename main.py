from FlightRadar24 import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
import json, time

fr = FlightRadar24API()
console = Console()

def choose_country():
    country = questionary.text("🌍 Entrez un pays (ex: France, Germany, Spain)").ask().strip()
    return country

def get_country_airports(country):
    try:
        airports = fr.get_airports()  # pas d'argument ici !
        filtered = [a for a in airports if a.get("country") == country]
        return filtered
    except Exception as e:
        console.print(f"[red]Erreur récupération aéroports : {e}[/red]")
        return []

def choose_airport(airports):
    if not airports:
        return None
    choices = [questionary.Choice(f"{a['icao']} – {a['name']}", value=a) for a in airports[:20]]
    return questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()

def get_airport_flights(icao):
    try:
        return fr.get_flights(icao)
    except Exception as e:
        console.print(f"[red]Erreur récupération vols : {e}[/red]")
        return []

def choose_flight(flights):
    if not flights:
        return None
    choices = [questionary.Choice(f"{f['flight']} – {f['airline']['name']}", value=f) for f in flights[:20]]
    return questionary.select("✈️ Choisis un vol :", choices=choices).ask()

def track_flight(flight_id):
    console.print(f"[green]🔄 Tracking du vol {flight_id}… (CTRL+C pour arrêter)[/green]")
    try:
        while True:
            data = fr.get_flight_details(flight_id)
            trail = data.get("trail", [])
            if trail:
                pt = trail[-1]
                table = Table(title="📡 Dernière position")
                table.add_column("Latitude"); table.add_column("Longitude")
                table.add_column("Altitude"); table.add_column("Vitesse")
                table.add_row(str(pt.get("lat")), str(pt.get("lng")), str(pt.get("alt")), str(pt.get("spd")))
                console.clear(); console.print(table)
            else:
                console.print("[yellow]Pas de données de vol disponibles.[/yellow]")
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("[yellow]⏹️ Suivi interrompu.[/yellow]")

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]")
    country = choose_country()
    airports = get_country_airports(country)
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return
    airport = choose_airport(airports)
    if not airport:
        console.print("[red]Aucun aéroport sélectionné.[/red]")
        return
    flights = get_airport_flights(airport['icao'])
    if not flights:
        console.print("[red]Aucun vol trouvé depuis cet aéroport.[/red]")
        return
    flight = choose_flight(flights)
    if not flight:
        console.print("[red]Aucun vol sélectionné.[/red]")
        return
    track_flight(flight['id'])

if __name__ == "__main__":
    main()
