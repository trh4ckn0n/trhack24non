import time
import webbrowser
from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_countries_from_airports(airports):
    countries = set()
    for airport in airports:
        country = getattr(airport, "country", None) or airport.get("country")
        if country:
            countries.add(country)
    return sorted(list(countries))

def choose_country(countries):
    console.print("Pays disponibles (extrait) : " + ", ".join(countries[:20]) + " ...")
    while True:
        country_input = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        if country_input in countries:
            return country_input
        console.print(f"[red]Pays '{country_input}' non trouvé, réessayez.[/red]")

def choose_airport(fr, country):
    airports = fr.get_airports()
    filtered = [
        airport for airport in airports
        if (getattr(airport, "country", None) or airport.get("country")) == country
    ]
    if not filtered:
        console.print(f"[red]Aucun aéroport trouvé pour le pays {country}[/red]")
        return None
    choices = [
        questionary.Choice(
            title=f"{getattr(airport, 'icao', '')} – {getattr(airport, 'name', '')}",
            value={
                "icao": getattr(airport, "icao", ""),
                "iata": getattr(airport, "iata", ""),
                "name": getattr(airport, "name", "")
            }
        )
        for airport in filtered
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
        callsign = getattr(f, "callsign", None) or getattr(f, "id", "??")
        title = f"{callsign} ({origin} → {destination})"
        flight_choices.append(questionary.Choice(title=title, value=f))
    return flight_choices

def track_flight(fr, flight, open_browser=False):
    flight_id = getattr(flight, "id", None)
    if not flight_id:
        console.print("[red]Erreur : impossible de récupérer l'ID du vol.[/red]")
        return

    # Récupérer callsign & hex pour URL officielle
    callsign = getattr(flight, "callsign", None) or getattr(flight, "id", None)
    hex_id = getattr(flight, "hex", None)

    if not callsign or not hex_id:
        console.print("[yellow]Impossible de récupérer callsign ou hex_id du vol pour URL FR24[/yellow]")

    fr24_url_2d = f"https://www.flightradar24.com/{callsign}/{hex_id}" if callsign and hex_id else None
    fr24_url_3d = f"{fr24_url_2d}/3d" if fr24_url_2d else None

    if open_browser and fr24_url_2d:
        console.print("[green]Ouverture des URLs Flightradar24 dans votre navigateur...[/green]")
        webbrowser.open(fr24_url_2d)
        if fr24_url_3d:
            time.sleep(1)  # petit délai entre ouverture des onglets
            webbrowser.open(fr24_url_3d)

    console.print(f"\n🔄 Tracking du vol {flight_id} (CTRL+C pour arrêter)...\n")
    try:
        while True:
            data = fr.get_flight_details(flight)
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
            latitude = trail.get("lat", None)
            longitude = trail.get("lng", None)

            console.clear()
            panel_text = (
                f"[bold cyan]Vol : {callsign}[/bold cyan]\n"
                f"Statut : {status}\n"
                f"Origine : {origin} → Destination : {destination}\n"
                f"Altitude : {altitude} pieds\n"
                f"Vitesse sol : {speed} kt\n"
            )
            if latitude is not None and longitude is not None:
                panel_text += f"Position GPS : {latitude:.5f}, {longitude:.5f}\n"
            else:
                panel_text += "[yellow]Position GPS non disponible[/yellow]\n"

            if fr24_url_2d:
                panel_text += f"[blue]URL Flightradar24 2D :[/blue] {fr24_url_2d}\n"
            if fr24_url_3d:
                panel_text += f"[blue]URL Flightradar24 3D :[/blue] {fr24_url_3d}\n"

            console.print(Panel(panel_text, title="Suivi Vol en Temps Réel", subtitle="Appuyez Ctrl+C pour quitter"))

            time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[red]Tracking arrêté par l'utilisateur.[/red]")

def main():
    console.print("[bold green]Bienvenue dans FlightRadar24 Tracker CLI[/bold green]\n")
    fr = FlightRadar24API()

    airports = fr.get_airports()
    countries = get_countries_from_airports(airports)
    country = choose_country(countries)
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

    # Demander si on veut ouvrir la carte dans le navigateur
    open_map = questionary.confirm("Voulez-vous ouvrir les URLs Flightradar24 (2D et 3D) dans le navigateur ?").ask()

    track_flight(fr, selected_flight, open_browser=open_map)

if __name__ == "__main__":
    main()
