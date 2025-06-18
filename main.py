#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
import time
import sys

console = Console()
fr = FlightRadar24API()

def list_countries(airports):
    countries = set()
    for a in airports:
        if a.country:
            countries.add(a.country.strip())
    return sorted(countries)

def choose_country():
    airports = fr.get_airports()
    countries = list_countries(airports)
    console.print(f"[green]Pays disponibles (extrait) :[/green] {', '.join(countries[:30])} ...")
    while True:
        country = questionary.text("🌍 Entrez un pays (ex: France, Spain, Italy)").ask()
        if not country or not country.strip():
            console.print("[red]Veuillez entrer un nom de pays valide.[/red]")
            continue
        country_input = country.strip().lower()

        found = any(c.lower() == country_input for c in countries)
        if not found:
            console.print(f"[yellow]Attention : le pays '{country}' n'a pas été trouvé dans la liste.[/yellow]")
            retry = questionary.confirm("Voulez-vous réessayer ?").ask()
            if retry:
                continue
            else:
                return country.strip()
        return country.strip()

def get_airports_for_country(country):
    airports = fr.get_airports()
    country_lower = country.lower()
    return [a for a in airports if a.country and a.country.strip().lower() == country_lower]

def choose_airport(airports):
    if not airports:
        console.print("[red]Aucun aéroport trouvé pour ce pays.[/red]")
        return None
    choices = []
    for a in airports[:30]:
        name = f"{a.icao} – {a.name or 'Sans nom'}"
        choices.append(questionary.Choice(title=name, value=a))
    return questionary.select("🛫 Sélectionne un aéroport :", choices=choices).ask()

def list_flights_around_airport(airport):
    console.print(f"[blue]Récupération des vols autour de l'aéroport {airport.icao} ({airport.iata})...[/blue]")
    flights = []
    try:
        flights = fr.get_flights(airport.icao)
        console.print(f"[green]Nombre de vols récupérés avec ICAO ({airport.icao}) : {len(flights)}[/green]")
        if not flights and airport.iata:
            console.print(f"[yellow]Aucun vol trouvé avec ICAO, tentative avec IATA {airport.iata}...[/yellow]")
            flights = fr.get_flights(airport.iata)
            console.print(f"[green]Nombre de vols récupérés avec IATA ({airport.iata}) : {len(flights)}[/green"])
    except Exception as e:
        console.print(f"[red]Erreur lors de la récupération des vols : {e}[/red]")
        return []

    if not flights:
        console.print("[yellow]Aucun vol trouvé autour de cet aéroport.[/yellow]")
        return []

    choices = []
    for f in flights:
        # Récupération robuste des codes aéroport origine/destination
        dep = getattr(f, 'origin_airport_icao', None) or getattr(f, 'origin_airport_iata', None) or "??"
        arr = getattr(f, 'destination_airport_icao', None) or getattr(f, 'destination_airport_iata', None) or "??"

        title = f"{f.callsign} ({dep} → {arr})"
        choices.append(questionary.Choice(title=title, value=f))
    return choices

def format_flight_data(data):
    table = Table(title="Informations de vol en temps réel")
    table.add_column("Clé")
    table.add_column("Valeur")

    for key in [
        "flight", "registration", "model", "speed", "altitude",
        "departure", "arrival", "latitude", "longitude", "status"
    ]:
        val = data.get(key, "N/A")
        table.add_row(key.capitalize(), str(val))
    return table

def track_flight(flight):
    console.print(f"🔄 Tracking du vol [bold cyan]{flight.callsign}[/bold cyan] (CTRL+C pour arrêter)...")
    with Live(refresh_per_second=1) as live:
        try:
            while True:
                data = fr.get_flight_details(flight.id)
                if not data:
                    console.print("[yellow]Pas de données disponibles pour ce vol actuellement.[/yellow]")
                else:
                    live.update(Panel(format_flight_data(data), title=f"Vol {flight.callsign}"))

                time.sleep(3)
        except KeyboardInterrupt:
            console.print("\n[red]Tracking arrêté par l'utilisateur.[/red]")

def main():
    console.print("[bold green]Bienvenue dans FlightRadar24 Tracker CLI[/bold green]\n")
    country = choose_country()
    airports = get_airports_for_country(country)
    if not airports:
        console.print(f"[red]Aucun aéroport disponible pour le pays '{country}'.[/red]")
        sys.exit(1)
    airport = choose_airport(airports)
    if not airport:
        console.print("[red]Aucun aéroport sélectionné, sortie.[/red]")
        sys.exit(1)
    console.print(f"Vous avez choisi : {airport.icao} – {airport.name}")

    console.print(f"\nChargement des vols autour de l'aéroport {airport.icao} – {airport.name}...\n")
    flight_choices = list_flights_around_airport(airport)
    if not flight_choices:
        sys.exit(0)

    selected_flight = questionary.select("✈️ Sélectionne un vol :", choices=flight_choices).ask()
    if not selected_flight:
        console.print("[red]Aucun vol sélectionné, sortie.[/red]")
        sys.exit(1)

    track_flight(selected_flight)

if __name__ == "__main__":
    main()
