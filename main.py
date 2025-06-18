import time
from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console

console = Console()

# Liste statique simple de pays (extraits)
COUNTRIES = [
    "Belgium", "France", "Germany", "Spain", "Italy", "United Kingdom",
    "United States", "Canada", "Australia", "Netherlands"
]

def choose_country():
    console.print("Pays disponibles (extrait) : " + ", ".join(COUNTRIES))
    while True:
        country_input = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        if country_input in COUNTRIES:
            return country_input
        console.print(f"[red]Pays '{country_input}' non trouvé, réessayez.[/red]")

def choose_airport(fr, country):
    airports = fr.get_airports(country)
    if not airports:
        console.print("[red]Aucun aéroport disponible pour ce pays.[/red]")
        return None
    choices = [
        questionary.Choice(title=f"{icao} – {airport['name']}", value={"icao": icao, "iata": airport["iata"], "name": airport["name"]})
        for icao, airport in airports.items()
    ]
    selected = questionary.select("🛫 Sélectionne un aéroport", choices=choices).ask()
    return selected

def list_flights_around_airport(fr, airport):
    console.print(f"\nChargement des vols autour de l'aéroport {airport['icao']} – {airport['name']}...\n")
    flights = fr.get_flights(airport["icao"])
    console.print(f"Nombre de vols récupérés avec ICAO ({airport['icao']}) : {len(flights)}")
    if len(flights) == 0 and airport["iata"]:
        console.print(f"Aucun vol trouvé avec ICAO, tentative avec IATA {airport['iata']}...")
        flights = fr.get_flights(airport["iata"])
        console.print(f"Nombre de vols récupérés avec IATA ({airport['iata']}) : {len(flights)}")

    if len(flights) == 0:
        console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
        return []

    flight_choices = []
    for f in flights:
        origin = getattr(f, "origin_airport_icao", "??")
        destination = getattr(f, "destination_airport_icao", "??")
        callsign = getattr(f, "callsign", f.id if hasattr(f, "id") else "??")
        title = f"{callsign} ({origin} → {destination})"
        flight_choices.append(questionary.Choice(title=title, value=f))
    return flight_choices

def track_flight(fr, flight):
    flight_id = flight.id if hasattr(flight, "id") else flight
    console.print(f"\n🔄 Tracking du vol {flight_id} (CTRL+C pour arrêter)...\n")
    try:
        while True:
            data = fr.get_flight_details(flight_id)
            if not data:
                console.print("[red]Impossible de récupérer les détails du vol.[/red]")
                break

            callsign = data.get("identification", {}).get("callsign", "N/A")
            status = data.get("status", {}).get("text", "N/A")
            origin = data.get("airport", {}).get("origin", {}).get("code", "N/A")
            destination = data.get("airport", {}).get("destination", {}).get("code", "N/A")
            trail = data.get("trail", [{}])[-1]
            altitude = trail.get("altitude", "N/A")
            speed = trail.get("groundspeed", "N/A")
            latitude = trail.get("lat", "N/A")
            longitude = trail.get("lng", "N/A")

            console.clear()
            console.print(f"[bold cyan]Vol : {callsign}[/bold cyan]")
            console.print(f"Statut : {status}")
            console.print(f"Origine : {origin} → Destination : {destination}")
            console.print(f"Altitude : {altitude} pieds")
            console.print(f"Vitesse sol : {speed} kt")
            console.print(f"Position GPS : {latitude}, {longitude}")

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[red]Tracking arrêté par l'utilisateur.[/red]")

def main():
    console.print("[bold green]Bienvenue dans FlightRadar24 Tracker CLI[/bold green]\n")
    fr = FlightRadar24API()

    country = choose_country()
    airport = choose_airport(fr, country)
    if not airport:
        return

    flights_choices = list_flights_around_airport(fr, airport)
    if not flights_choices:
        return

    selected_flight = questionary.select("✈️ Sélectionne un vol :", choices=flights_choices).ask()
    if not selected_flight:
        console.print("[red]Aucun vol sélectionné.[/red]")
        return

    track_flight(fr, selected_flight)

if __name__ == "__main__":
    main()
