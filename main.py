import time
import sys
from FlightRadar24.api import FlightRadar24
import questionary
from rich.console import Console

console = Console()
fr = FlightRadar24()

def choose_country():
    countries = fr.get_countries()
    countries_names = sorted([c['name'] for c in countries])
    console.print(f"Pays disponibles (extrait) : {', '.join(countries_names[:30])} ...")
    while True:
        country_name = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        if country_name in countries_names:
            return country_name
        console.print("[red]Pays non disponible, essaie encore.[/red]")

def choose_airport(country_name):
    airports = fr.get_airports(country_name)
    if not airports:
        console.print("[red]Aucun aéroport disponible pour ce pays.[/red]")
        return None

    choices = []
    for icao, airport in airports.items():
        # Affiche ICAO + nom
        title = f"{icao} – {airport['name']}"
        choices.append(questionary.Choice(title=title, value=icao))

    airport_icao = questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()
    selected = airports.get(airport_icao)
    if selected:
        console.print(f"Vous avez choisi : {airport_icao} – {selected['name']}")
        # Retourne l'objet complet (avec ICAO, IATA, etc)
        return {'icao': airport_icao, **selected}
    else:
        return None

def list_flights_around_airport(airport):
    icao = airport['icao']
    iata = airport.get('iata')
    console.print(f"Chargement des vols autour de l'aéroport {icao} – {airport['name']}...\n")

    flights = fr.get_flights(icao)
    console.print(f"Nombre de vols récupérés avec ICAO ({icao}) : {len(flights)}")

    if len(flights) == 0 and iata:
        flights = fr.get_flights(iata)
        console.print(f"Aucun vol trouvé avec ICAO, tentative avec IATA {iata}...")
        console.print(f"Nombre de vols récupérés avec IATA ({iata}) : {len(flights)}")

    if len(flights) == 0:
        console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
        return []

    # Crée une liste de choix avec l'objet vol complet en value
    choices = []
    for f in flights:
        dep = getattr(f, 'origin_airport_icao', None) or getattr(f, 'origin_airport_iata', '??')
        arr = getattr(f, 'destination_airport_icao', None) or getattr(f, 'destination_airport_iata', '??')
        title = f"{f.callsign} ({dep} → {arr})"
        choices.append(questionary.Choice(title=title, value=f))

    return choices

def track_flight(flight):
    flight_id = flight.id
    console.print(f"🔄 Tracking du vol {flight.callsign} (ID: {flight_id}) (CTRL+C pour arrêter)...")

    try:
        while True:
            data = fr.get_flight_details(flight_id)
            if not data:
                console.print("[red]Impossible de récupérer les détails du vol.[/red]")
                break

            lat = data.get('lat', '??')
            lng = data.get('lng', '??')
            altitude = data.get('altitude', '??')
            speed = data.get('speed', '??')
            heading = data.get('heading', '??')

            console.clear()
            console.print(f"[green]Tracking du vol {flight.callsign}[/green]")
            console.print(f"Position : {lat}, {lng}")
            console.print(f"Altitude : {altitude} m")
            console.print(f"Vitesse : {speed} km/h")
            console.print(f"Cap : {heading}°")

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[bold red]Tracking arrêté par l'utilisateur.[/bold red]")
        sys.exit(0)

def main():
    console.print("[bold cyan]Bienvenue dans FlightRadar24 Tracker CLI[/bold cyan]\n")

    country = choose_country()
    airport = choose_airport(country)
    if not airport:
        console.print("[red]Sortie car aucun aéroport choisi.[/red]")
        return

    flight_choices = list_flights_around_airport(airport)
    if not flight_choices:
        return

    selected_flight = questionary.select("✈️ Sélectionne un vol :", choices=flight_choices).ask()
    if not selected_flight:
        console.print("[red]Aucun vol sélectionné, sortie.[/red]")
        return

    track_flight(selected_flight)

if __name__ == "__main__":
    main()
