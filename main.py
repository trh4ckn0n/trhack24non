#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from FlightRadar24.api import FlightRadar24API
import questionary
from rich.console import Console
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

        # On vérifie si le pays est dans la liste (cas insensible)
        found = any(c.lower() == country_input for c in countries)
        if not found:
            console.print(f"[yellow]Attention : le pays '{country}' n'a pas été trouvé dans la liste des pays disponibles.[/yellow]")
            choice = questionary.confirm("Voulez-vous réessayer ?").ask()
            if choice:
                continue
            else:
                return country.strip()
        return country.strip()

def get_airports_for_country(country):
    airports = fr.get_airports()
    filtered = []
    country_lower = country.lower()
    for a in airports:
        if not a.country:
            continue
        if a.country.strip().lower() == country_lower:
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

if __name__ == "__main__":
    main()
