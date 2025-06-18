import time
from FlightRadar24.api import FlightRadar24
import questionary
from rich.console import Console

console = Console()

def choose_country(fr):
    countries = fr.get_countries()
    countries_sorted = sorted(countries.keys())

    console.print("Pays disponibles (extrait) : " + ", ".join(countries_sorted[:50]) + " ...")
    while True:
        country_input = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        country_input = country_input.strip()
        if country_input in countries:
            return country_input
        else:
            console.print(f"[red]Pays '{country_input}' non trouvé, réessayez.[/red]")

def choose_airport(fr, country):
    airports = fr.get_airports(country)
    if not airports:
        console.print("[red]Aucun aéroport disponible pour ce pays.[/red]")
        return None
    # Création d'une liste de choix formatée
    choices = [
        questionary.Choice(title=f"{icao} – {airport['name']}", value={"icao": icao, "iata": airport["iata"], "name": airport["name"]})
        for icao, airport in airports.items()
    ]
    selected = questionary.select("🛫 Sélectionne un aéroport", choices=choices).ask()
    if selected:
        return selected
    else:
        return None

def list_flights_around_airport(fr, airport):
    console.print(f"\nChargement des vols autour de l'aéroport {airport['icao']} – {airport['name']}...\n")
    # Essaye avec ICAO d'abord
    flights = fr.get_flights(airport["icao"])
    console.print(f"Nombre de vols récupérés avec ICAO ({airport['icao']}) : {len(flights)}")
    if len(flights) == 0 and airport["iata"]:
        console.print(f"Aucun vol trouvé avec ICAO, tentative avec IATA {airport['iata']}...")
        flights = fr.get_flights(airport["iata"])
        console.print(f"Nombre de vols récupérés avec IATA ({airport['iata']}) : {len(flights)}")

    if len(flights) == 0:
        console.print("[red]Aucun vol trouvé autour de cet aéroport.[/red]")
        return []

    # Création d'une liste de choix de vols, stockant l'objet complet Flight
    flight_choices = []
    for f in flights:
        # Certains attributs peuvent ne pas exister, gérons ça
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

            # Exemples d'informations à afficher, adapte selon ce que tu veux voir
            callsign = data.get("identification", {}).get("callsign", "N/A")
            status = data.get("status", {}).get("text", "N/A")
            origin = data.get("airport", {}).get("origin", {}).get("code", "N/A")
            destination = data.get("airport", {}).get("destination", {}).get("code", "N/A")
            altitude = data.get("trail", [{}])[-1].get("altitude", "N/A")
            speed = data.get("trail", [{}])[-1].get("groundspeed", "N/A")
            latitude = data.get("trail", [{}])[-1].get("lat", "N/A")
            longitude = data.get("trail", [{}])[-1].get("lng", "N/A")

            console.clear()
            console.print(f"[bold cyan]Vol : {callsign}[/bold cyan]")
            console.print(f"Statut : {status}")
            console.print(f"Origine : {origin} → Destination : {destination}")
            console.print(f"Altitude : {altitude} pieds")
            console.print(f"Vitesse sol : {speed} kt")
            console.print(f"Position GPS : {latitude}, {longitude}")

            time.sleep(5)  # Refresh toutes les 5 secondes
    except KeyboardInterrupt:
        console.print("\n[red]Tracking arrêté par l'utilisateur.[/red]")

def main():
    console.print("[bold green]Bienvenue dans FlightRadar24 Tracker CLI[/bold green]\n")
    fr = FlightRadar24()

    country = choose_country(fr)
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
