import flightradar24
import questionary
from rich.console import Console
from rich.table import Table
import json
import csv
import time
import os

fr = flightradar24.Api()
console = Console()

def choose_mode():
    return questionary.select(
        "🔍 Comment veux-tu sélectionner le vol ?",
        choices=[
            "📡 Par numéro de vol (AFR1234)",
            "🌍 Explorer les vols actifs par zone",
            "❌ Quitter"
        ]).ask()

def search_flight_by_code():
    code = questionary.text("🆔 Entrez le code du vol (ex: AFR1234)").ask().strip().upper()
    results = fr.search(code)
    if not results or not results['results']:
        console.print("[red]Aucun vol trouvé pour ce code.[/red]")
        return None

    choices = [
        questionary.Choice(
            f"{r['detail']}: {r.get('airport', {}).get('origin', {}).get('position', {}).get('region', {}).get('city', '???')} → {r.get('airport', {}).get('destination', {}).get('position', {}).get('region', {}).get('city', '???')}",
            value=r
        )
        for r in results['results']
    ]

    selected = questionary.select("✈️ Choisis un vol :", choices=choices).ask()
    return selected

def list_flights_by_area():
    console.print("[cyan]🌍 Définis une zone géographique à scanner :[/cyan]")
    try:
        north = float(questionary.text("Latitude nord (ex: 55)").ask())
        south = float(questionary.text("Latitude sud (ex: 40)").ask())
        west = float(questionary.text("Longitude ouest (ex: -5)").ask())
        east = float(questionary.text("Longitude est (ex: 15)").ask())
    except Exception:
        console.print("[red]Entrée invalide.[/red]")
        return None

    try:
        flights = fr.get_flights_by_bounds(north=north, south=south, east=east, west=west)
    except Exception as e:
        console.print(f"[red]Erreur : {e}[/red]")
        return None

    if not flights:
        console.print("[yellow]Aucun vol trouvé dans cette zone.[/yellow]")
        return None

    filter_icao = questionary.text("Filtrer par code compagnie (ex: AFR) ou vide :").ask().strip().upper()
    if filter_icao:
        flights = [f for f in flights if f.get('callsign', '').startswith(filter_icao)]

    if not flights:
        console.print("[yellow]Aucun vol trouvé avec ce filtre.[/yellow]")
        return None

    choices = [
        questionary.Choice(
            f"{f['callsign']} | {f.get('origin_airport_iata', '???')} → {f.get('destination_airport_iata', '???')}",
            value=f
        ) for f in flights[:20]
    ]
    return questionary.select("✈️ Sélectionne un vol :", choices=choices).ask()

def track_flight(flight_id, filename_base="flight_log"):
    interval = int(questionary.text("⏱️ Intervalle de mise à jour (sec)", default="10").ask())
    export_format = questionary.select("💾 Format de sauvegarde ?", choices=["JSON", "CSV"]).ask()
    data_log = []

    console.print(f"[green]🔄 Suivi du vol {flight_id} toutes les {interval} secondes...[/green]")

    try:
        while True:
            details = fr.get_flight_details(flight_id)
            if not details:
                console.print("[red]Aucune donnée trouvée pour ce vol.[/red]")
                break

            aircraft = details.get('aircraft', {})
            trail = details.get('trail', [{}])[-1]

            info = {
                'timestamp': trail.get('ts'),
                'latitude': trail.get('lat'),
                'longitude': trail.get('lng'),
                'altitude': trail.get('alt'),
                'speed': trail.get('spd'),
                'heading': trail.get('hd'),
                'reg': aircraft.get('registration'),
                'model': aircraft.get('model'),
                'hex': aircraft.get('hex')
            }

            data_log.append(info)

            # Affichage
            table = Table(title="📍 Position actuelle")
            for key in info:
                table.add_column(key, justify="center")
            table.add_row(*[str(info[k]) for k in info])
            console.clear()
            console.print(table)

            # Sauvegarde
            file_path = f"{filename_base}.{export_format.lower()}"
            if export_format == "JSON":
                with open(file_path, "w") as f:
                    json.dump(data_log, f, indent=2)
            elif export_format == "CSV":
                with open(file_path, "w", newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=info.keys())
                    writer.writeheader()
                    writer.writerows(data_log)

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("[bold yellow]🛑 Suivi interrompu par l'utilisateur.[/bold yellow]")

if __name__ == "__main__":
    os.system("clear")
    console.print("[bold magenta]✈️ Bienvenue dans FlightRadar24 Tracker CLI[/bold magenta]\n")

    mode = choose_mode()
    selected_flight = None

    if mode == "📡 Par numéro de vol (AFR1234)":
        flight_info = search_flight_by_code()
        if flight_info:
            selected_flight = flight_info['id']
    elif mode == "🌍 Explorer les vols actifs par zone":
        flight_info = list_flights_by_area()
        if flight_info:
            selected_flight = flight_info['id']

    if selected_flight:
        track_flight(selected_flight)
    else:
        console.print("[red]Aucun vol sélectionné. Fin du programme.[/red]")
