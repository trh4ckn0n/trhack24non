from FlightRadar24 import FlightRadar24API
import questionary
import json
import time
from rich.console import Console
from rich.table import Table

fr = FlightRadar24API()
console = Console()

def choose_country():
    code = questionary.text("🔁 Code pays ISO 2‑lettres (ex: FR, ES, IT)").ask().strip().upper()
    return code

def list_airports(country_code):
    try:
        airports = fr.get_airports(country_code)
        return airports
    except Exception as e:
        console.print(f"[red]Erreur get_airports : {e}[/red]")
        return []

def choose_airport(airports):
    choices = [questionary.Choice(f"{a['icao']} – {a['name']}", value=a) for a in airports[:20]]
    return questionary.select("✈️ Choisis un aéroport :", choices=choices).ask()

def list_flights(icao):
    try:
        return fr.get_flights(icao)
    except Exception as e:
        console.print(f"[red]Erreur get_flights : {e}[/red]")
        return []

def choose_flight(flights):
    choices = [questionary.Choice(f"{f['flight']} – {f['airline']['name']}", value=f) for f in flights[:20]]
    return questionary.select("🚀 Choisis un vol :", choices=choices).ask()

def track(flight_id):
    console.print(f"[green]🔄 Tracking du vol {flight_id}… (CTRL+C pour arrêter)[/green]")
    data=[]
    try:
        while True:
            d=fr.get_flight_details(flight_id)
            trail = d.get('trail',[])
            if not trail: break
            pt = trail[-1]
            row = {
                "ts": pt.get('ts'),
                "lat": pt.get('lat'),
                "lng": pt.get('lng'),
                "alt": pt.get('alt'),
                "spd": pt.get('spd'),
            }
            data.append(row)
            t = Table(title="📡 Position actuelle")
            for k in row: t.add_column(k); t.add_row(str(row[k]))
            console.clear(); console.print(t)
            with open(f"{flight_id}.json","w") as f: json.dump(data,f,indent=2)
            time.sleep(5)
    except KeyboardInterrupt:
        console.print("[yellow]Arrêt du tracking.[/yellow]")

def main():
    country = choose_country()
    airports = list_airports(country)
    if not airports:
        console.print("[red]Aucun aéroport trouvé.[/red]"); return
    airport = choose_airport(airports)
    flights = list_flights(airport['icao'])
    if not flights:
        console.print("[red]Aucun vol trouvé.[/red]"); return
    flight = choose_flight(flights)
    track(flight['id'])

if __name__ == "__main__":
    main()
