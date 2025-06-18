#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console
import time
import sys

console = Console()
fr = FlightRadar24API()

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

    filtered = []
    for a in airports:
        if a.country and a.country.lower() == country.lower():
            # Récupérer coordonnées lat/lng ou position fallback
            lat = getattr(a, "lat", None)
            lng = getattr(a, "lng", None)
            if lat is None or lng is None:
                pos = getattr(a, "position", None)
                if pos and isinstance(pos, dict):
                    lat = pos.get("latitude")
                    lng = pos.get("longitude")
            if lat is not None and lng is not None:
                filtered.append(a)

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

def get_flights_near_airport(airport, radius_km=150):
    lat = getattr(airport, "lat", None)
    lon = getattr(airport, "lng", None)

    if lat is None or lon is None:
        pos = getattr(airport, "position", None)
        if pos and isinstance(pos, dict):
            lat = pos.get("latitude")
            lon = pos.get("longitude")

    if lat is None or lon is None:
        console.print("[red]Impossible de récupérer la position de l'aéroport.[/red]")
        return []

    try:
        # get_flights prend un paramètre 'bounds' = (lat_min, lon_min, lat_max, lon_max)
        # On calcule une box autour de l'aéroport pour approximer le rayon
        lat_min = lat - 1.5
        lat_max = lat + 1.5
        lon_min = lon - 1.5
        lon_max = lon + 1.5
        bounds = (lat_min, lon_min, lat_max, lon_max)

        flights = fr.get_flights(bounds=bounds)
        return flights
    except Exception as e:
        console.print(f"[red]Erreur lors de la récupération des vols : {e}[/red]")
        return []

def choose_flight(flights):
    if not flights:
        console.print("[yellow]Aucun vol trouvé autour de cet aéroport.[/yellow]")
        return None
    choices = []
    for f in flights[:30]:
        callsign = getattr(f, "callsign", None) or getattr(f, "id", None) or "??"
        dep = getattr(f.origin_airport, "icao", "??") if f.origin_airport else "??"
        arr = getattr(f.destination_airport, "icao", "??") if f.destination_airport else "??"
        title = f"{callsign} ({dep} → {arr})"
        choices.append(questionary.Choice(title=title, value=f))
    return questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()

def track_flight(flight):
    callsign = getattr(flight, "callsign", None) or getattr(flight, "id", None)
    if not callsign:
        console.print("[red]Erreur : impossible d'obtenir l'identifiant du vol.[/red]")
        return

    console.print(f"🔄 Tracking du vol [bold green]{callsign}[/bold green] (CTRL+C pour arrêter)...")
    try:
        while True:
            try:
                data = fr.get_flight_details(callsign)
                if not data:
                    console.print("[yellow]Pas de données disponibles pour ce vol pour le moment.[/yellow]")
                else:
                    lat = data.get("latitude")
                    lon = data.get("longitude")
                    altitude = data.get("altitude")
                    speed = data.get("speed")
                    heading = data.get("heading")
                    est_arrival = data.get("estimated_arrival_time")
                    est_departure = data.get("estimated_departure_time")

                    console.clear()
                    console.print(f"[bold cyan]Vol {callsign}[/bold cyan]")
                    console.print(f"Position : lat {lat}, lon {lon}")
                    console.print(f"Altitude : {altitude} ft | Vitesse : {speed} km/h | Cap : {heading}°")
                    console.print(f"Est. Départ : {est_departure}")
                    console.print(f"Est. Arrivée : {est_arrival}")
                    console.print("\n(Press Ctrl+C to stop tracking)")
                time.sleep(5)
            except KeyboardInterrupt:
                console.print("\n[bold red]Tracking arrêté par l'utilisateur.[/bold red]")
                break
            except Exception as e:
                console.print(f"[red]Erreur lors du tracking du vol : {e}[/red]")
                time.sleep(5)
    except KeyboardInterrupt:
        console.print("\n[bold red]Programme arrêté.[/bold red]")

def main():
    console.print("[bold green]Bienvenue dans FlightRadar24 Tracker CLI[/bold green]\n")

    country = choose_country()
    airports = get_airports_for_country(country)
    if not airports:
        console.print("[red]Aucun aéroport disponible pour ce pays.[/red]")
        sys.exit(1)

    airport = choose_airport(airports)
    if not airport:
        console.print("[red]Aucun aéroport sélectionné, sortie.[/red]")
        sys.exit(1)

    console.print(f"\nChargement des vols autour de l'aéroport [bold]{airport.icao} – {airport.name or 'Sans nom'}[/bold]...")
    flights = get_flights_near_airport(airport)
    if not flights:
        console.print("[yellow]Aucun vol trouvé autour de cet aéroport.[/yellow]")
        sys.exit(0)

    flight = choose_flight(flights)
    if not flight:
        console.print("[yellow]Aucun vol sélectionné, sortie.[/yellow]")
        sys.exit(0)

    track_flight(flight)

if __name__ == "__main__":
    main()
