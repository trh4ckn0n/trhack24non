import flightradar24
import json
import csv
import time
import questionary
from rich.console import Console
from rich.table import Table

fr = flightradar24.Api()
console = Console()

def save_to_csv(filename, data):
    keys = data[0].keys()
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def track_flight(flight_id, callsign, interval=10):
    console.print(f"[bold green]Suivi du vol {callsign} (ID: {flight_id}) toutes les {interval} secondes[/bold green]")
    data_log = []

    try:
        while True:
            details = fr.get_flight_details(flight_id)
            if not details:
                console.print("[bold red]Données introuvables pour ce vol.[/bold red]")
                break
            
            trail = details.get('trail', [])
            last_pos = trail[-1] if trail else {}
            info = {
                'time': last_pos.get('ts'),
                'latitude': last_pos.get('lat'),
                'longitude': last_pos.get('lng'),
                'altitude': last_pos.get('alt'),
                'speed': last_pos.get('spd'),
                'heading': last_pos.get('hd'),
            }

            data_log.append(info)

            table = Table(title="Position actuelle du vol")
            for k in info: table.add_column(k, justify="center")
            table.add_row(*[str(info[k]) for k in info])
            console.clear()
            console.print(table)

            with open(f"{callsign}_log.json", "w") as f:
                json.dump(data_log, f, indent=2)
            save_to_csv(f"{callsign}_log.csv", data_log)

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("[bold yellow]Arrêt manuel du tracking.[/bold yellow]")

def list_flights_by_area_and_filter():
    console.print("[bold cyan]🔍 Sélection de zone géographique :[/bold cyan]")
    north = float(questionary.text("Latitude nord (ex: 55)").ask())
    south = float(questionary.text("Latitude sud (ex: 40)").ask())
    west = float(questionary.text("Longitude ouest (ex: -5)").ask())
    east = float(questionary.text("Longitude est (ex: 15)").ask())

    all_flights = fr.get_flights()
    flights = [
        f for f in all_flights
        if f.get('latitude') and f.get('longitude') and
           south <= f['latitude'] <= north and
           west <= f['longitude'] <= east
    ]

    if not flights:
        console.print("[red]Aucun vol trouvé dans cette zone.[/red]")
        return None

    filter_icao = questionary.text("Filtrer par compagnie ? (ex: AFR, RYR ou vide pour tous)").ask().upper().strip()
    if filter_icao:
        flights = [f for f in flights if f.get('callsign', '').startswith(filter_icao)]

    if not flights:
        console.print("[red]Aucun vol ne correspond au filtre ICAO.[/red]")
        return None

    # On limite à 20 vols pour éviter un menu trop long
    choices = [
        questionary.Choice(
            f"{f['callsign']} | {f.get('origin_airport_iata', '???')} → {f.get('destination_airport_iata', '???')}", value=f
        )
        for f in flights[:20]
    ]

    flight = questionary.select("✈️ Choisis un vol à suivre :", choices=choices).ask()
    return flight

if __name__ == "__main__":
    method = questionary.select(
        "🔍 Comment veux-tu sélectionner le vol ?",
        choices=["Explorer les vols actifs par zone", "Saisir manuellement le code de vol"]
    ).ask()

    selected_flight = None

    if method == "Explorer les vols actifs par zone":
        selected_flight = list_flights_by_area_and_filter()
        if selected_flight:
            track_flight(selected_flight['id'], selected_flight['callsign'])

    else:
        code = questionary.text("Entrez le numéro de vol (ex: AFR1234)").ask().strip().upper()
        results = fr.search(code)
        if results and results.get('results'):
            f = results['results'][0]
            track_flight(f['id'], f['detail']['flight'])
        else:
            console.print("[bold red]Aucun résultat pour ce vol.[/bold red]")
