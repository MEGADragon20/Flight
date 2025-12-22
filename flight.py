import random as r
import math
from typing import List, Optional
from datetime import datetime, timedelta

# ==================== MODEL CLASSES ====================

class Instant:
    """Zeitpunkt mit Tag, Stunde und Minute"""
    DAYS = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 
            'H': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'U': 'Sunday'}
    
    def __init__(self, day: str, hour: int, minute: int):
        self.day = day
        self.hour = hour
        self.minute = minute
    
    def __str__(self):
        return f"{self.day}-{self.hour}-{self.minute}"
    
    @classmethod
    def from_string(cls, string: str):
        """Erstellt Instant aus String (z.B. 'M-10-30')"""
        parts = string.split("-")
        return cls(parts[0], int(parts[1]), int(parts[2]))
    
    def to_minutes(self) -> int:
        """Konvertiert zu Minuten seit Wochenbeginn"""
        day_index = list(self.DAYS.keys()).index(self.day)
        return day_index * 24 * 60 + self.hour * 60 + self.minute
    
    def add_minutes(self, minutes: int):
        """Addiert Minuten und gibt neuen Instant zurück"""
        total_minutes = self.to_minutes() + minutes
        day_index = (total_minutes // (24 * 60)) % 7
        remaining = total_minutes % (24 * 60)
        hour = remaining // 60
        minute = remaining % 60
        return Instant(list(self.DAYS.keys())[day_index], hour, minute)


class City:
    """Stadt mit Name, Population und Koordinaten"""
    def __init__(self, name: str, population: int, x: int, y: int, short: str):
        self.name = name
        self.population = population
        self.x = x
        self.y = y
        self.short = short
    
    def __str__(self):
        return f"{self.name} ({self.short})"
    
    def distance_to(self, other: 'City') -> float:
        """Berechnet Distanz zu anderer Stadt"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class PlaneModel:
    """Flugzeugmodell das gekauft werden kann"""
    def __init__(self, name: str, capacity: int, max_distance: int, velocity: int, price: int):
        self.name = name
        self.capacity = capacity
        self.max_distance = max_distance
        self.velocity = velocity
        self.price = price
    
    def __str__(self):
        return f"{self.name} - €{self.price:,} (Kap: {self.capacity}, Dist: {self.max_distance}, Vel: {self.velocity})"


class Plane:
    """Flugzeug mit Eigenschaften und Flugliste"""
    def __init__(self, model: PlaneModel, registration: str):
        self.model = model
        self.registration = registration
        self.capacity = model.capacity
        self.max_distance = model.max_distance
        self.velocity = model.velocity
        self.current_city: Optional[City] = None
        self.flights: List['Flight'] = []
    
    def __str__(self):
        return f"{self.registration} ({self.model.name})"
    
    def info(self) -> str:
        return f"{self.registration} | {self.model.name} | {self.capacity} | {self.max_distance} | {self.velocity}"
    
    def can_fly(self, distance: float) -> bool:
        """Prüft ob Flugzeug die Distanz fliegen kann"""
        return distance <= self.max_distance


class Flight:
    """Flug zwischen zwei Städten"""
    PRICE_PER_KM = 0.15  # Euro pro Kilometer
    COST_PER_KM = 0.08   # Kosten pro Kilometer
    
    def __init__(self, origin: City, destination: City, plane: Plane, start: Instant, passengers: int):
        self.origin = origin
        self.destination = destination
        self.plane = plane
        self.passengers = passengers
        self.distance = origin.distance_to(destination)
        self.duration = round(self.distance / plane.velocity)
        self.start = start
        self.end = start.add_minutes(self.duration)
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        return f"{self.origin.short}{self.destination.short}{self.start}#{self.plane.registration}"
    
    def __str__(self):
        return f"{self.origin.short}→{self.destination.short} ({self.start}) [{self.passengers}pax]"
    
    def calculate_revenue(self) -> float:
        """Berechnet Einnahmen des Flugs"""
        return self.passengers * self.distance * self.PRICE_PER_KM
    
    def calculate_cost(self) -> float:
        """Berechnet Kosten des Flugs"""
        return self.distance * self.COST_PER_KM
    
    def calculate_profit(self) -> float:
        """Berechnet Gewinn des Flugs"""
        return self.calculate_revenue() - self.calculate_cost()
    
    def info(self) -> str:
        return (f"{self.id}\n"
                f"  Von: {self.origin.name} Nach: {self.destination.name}\n"
                f"  Start: {self.start} Ende: {self.end}\n"
                f"  Dauer: {self.duration}min Distanz: {self.distance:.0f}km\n"
                f"  Passagiere: {self.passengers}/{self.plane.capacity}\n"
                f"  Gewinn: €{self.calculate_profit():.2f}")


# ==================== GAME MANAGER ====================

class AirlineManager:
    """Hauptklasse für die Spiellogik"""
    
    def __init__(self):
        self.cities: List[City] = []
        self.planes: List[Plane] = []
        self.flights: List[Flight] = []
        self.money: float = 50000.0  # Startkapital
        self.week: int = 1
        self.plane_counter: int = 1
        
        self._initialize_game()
    
    def _initialize_game(self):
        """Initialisiert Spiel mit Standarddaten"""
        # Städte
        self.cities = [
            City("Berlin", 3700000, 0, 0, "BER"),
            City("München", 1500000, 500, 600, "MUC"),
            City("Hamburg", 1800000, -100, -400, "HAM"),
            City("Frankfurt", 750000, 300, 200, "FRA"),
            City("Köln", 1100000, -200, 100, "CGN"),
            City("Paris", 2200000, -500, 300, "CDG"),
            City("London", 8900000, -800, -200, "LHR"),
            City("Amsterdam", 820000, -300, -300, "AMS"),
        ]
        
        # Verfügbare Flugzeugmodelle
        self.available_models = [
            PlaneModel("Cessna 172", 4, 1200, 20, 15000),
            PlaneModel("DHC-6 Twin Otter", 19, 1400, 30, 35000),
            PlaneModel("ATR 72", 70, 1500, 45, 80000),
            PlaneModel("Boeing 737", 180, 5500, 70, 250000),
            PlaneModel("Airbus A320", 180, 6100, 75, 280000),
            PlaneModel("Boeing 787", 330, 14000, 90, 650000),
            PlaneModel("Airbus A350", 350, 15000, 95, 700000),
        ]
        
        # Startflugzeug
        starter_model = PlaneModel("Dash 8 Q200", 50, 2000, 40, 0)
        starter_plane = Plane(starter_model, f"D-GAME{self.plane_counter}")
        starter_plane.current_city = self.cities[0]  # Startet in Berlin
        self.planes.append(starter_plane)
        self.plane_counter += 1
    
    # City operations
    def find_city(self, name: str) -> Optional[City]:
        for city in self.cities:
            if city.name.lower() == name.lower() or city.short.lower() == name.lower():
                return city
        return None
    
    def get_all_cities(self) -> List[City]:
        return self.cities.copy()
    
    # Plane operations
    def buy_plane(self, model_name: str) -> Plane:
        """Kauft ein neues Flugzeug"""
        model = None
        for m in self.available_models:
            if m.name.lower() == model_name.lower():
                model = m
                break
        
        if not model:
            raise ValueError(f"Flugzeugmodell '{model_name}' nicht gefunden")
        
        if self.money < model.price:
            raise ValueError(f"Nicht genug Geld! Benötigt: €{model.price:,}, Verfügbar: €{self.money:,.2f}")
        
        self.money -= model.price
        registration = f"D-GAME{self.plane_counter}"
        self.plane_counter += 1
        
        plane = Plane(model, registration)
        plane.current_city = self.cities[0]  # Neue Flugzeuge starten in erster Stadt
        self.planes.append(plane)
        
        return plane
    
    def find_plane(self, registration: str) -> Optional[Plane]:
        for plane in self.planes:
            if plane.registration.lower() == registration.lower():
                return plane
        return None
    
    def get_all_planes(self) -> List[Plane]:
        return self.planes.copy()
    
    def get_available_models(self) -> List[PlaneModel]:
        return self.available_models.copy()
    
    # Flight operations
    def create_flight(self, origin_name: str, dest_name: str, 
                     plane_reg: str, start: Instant, passengers: int) -> Flight:
        """Erstellt neuen Flug mit Validierung"""
        origin = self.find_city(origin_name)
        destination = self.find_city(dest_name)
        plane = self.find_plane(plane_reg)
        
        if not origin:
            raise ValueError(f"Stadt '{origin_name}' nicht gefunden")
        if not destination:
            raise ValueError(f"Stadt '{dest_name}' nicht gefunden")
        if not plane:
            raise ValueError(f"Flugzeug '{plane_reg}' nicht gefunden")
        
        if passengers > plane.capacity:
            raise ValueError(f"Zu viele Passagiere! Max: {plane.capacity}")
        
        distance = origin.distance_to(destination)
        if not plane.can_fly(distance):
            raise ValueError(f"Flugzeug kann diese Distanz nicht fliegen ({distance:.0f} > {plane.max_distance})")
        
        flight = Flight(origin, destination, plane, start, passengers)
        self.flights.append(flight)
        plane.flights.append(flight)
        return flight
    
    def get_all_flights(self) -> List[Flight]:
        return self.flights.copy()
    
    def clear_flights(self):
        """Löscht alle Flüge (für neue Woche)"""
        self.flights.clear()
        for plane in self.planes:
            plane.flights.clear()
    
    def check_flight_plan(self) -> List[str]:
        """Validiert Flugplan und gibt Probleme zurück"""
        issues = []
        
        for plane in self.planes:
            if not plane.flights:
                continue
                
            sorted_flights = sorted(plane.flights, key=lambda f: f.start.to_minutes())
            
            # Prüfe ersten Flug
            first_flight = sorted_flights[0]
            if plane.current_city and plane.current_city != first_flight.origin:
                issues.append(
                    f"⚠️  {plane.registration}: Flugzeug ist in {plane.current_city.name}, "
                    f"erster Flug startet aber in {first_flight.origin.name}"
                )
            
            for i in range(len(sorted_flights) - 1):
                current = sorted_flights[i]
                next_flight = sorted_flights[i + 1]
                
                # Prüfe ob Flugzeug rechtzeitig am nächsten Startort ist
                if current.destination != next_flight.origin:
                    issues.append(
                        f"⚠️  {plane.registration}: Flug {current} landet in {current.destination.name}, "
                        f"aber nächster Flug startet in {next_flight.origin.name}"
                    )
                
                # Prüfe Zeitüberschneidung
                if current.end.to_minutes() > next_flight.start.to_minutes():
                    issues.append(
                        f"⚠️  {plane.registration}: Flug {current} endet nach Start von {next_flight}"
                    )
        
        return issues
    
    def advance_week(self) -> dict:
        """Lässt eine Woche vergehen und berechnet Gewinn"""
        # Prüfe Flugplan
        issues = self.check_flight_plan()
        if issues:
            raise ValueError("Flugplan ist ungültig! Nutze 'check' um Probleme zu sehen.")
        
        # Berechne Gewinn
        total_revenue = 0
        total_cost = 0
        total_profit = 0
        flight_count = 0
        
        for flight in self.flights:
            revenue = flight.calculate_revenue()
            cost = flight.calculate_cost()
            profit = flight.calculate_profit()
            
            total_revenue += revenue
            total_cost += cost
            total_profit += profit
            flight_count += 1
            
            # Update Flugzeug Position
            flight.plane.current_city = flight.destination
        
        # Wartungskosten pro Flugzeug pro Woche
        maintenance = len(self.planes) * 500
        total_cost += maintenance
        total_profit -= maintenance
        
        self.money += total_profit
        self.week += 1
        
        # Lösche alte Flüge
        self.clear_flights()
        
        return {
            'week': self.week - 1,
            'flights': flight_count,
            'revenue': total_revenue,
            'cost': total_cost,
            'maintenance': maintenance,
            'profit': total_profit,
            'new_balance': self.money
        }


# ==================== CLI INTERFACE ====================

class CLI:
    """Command Line Interface für das Spiel"""
    
    def __init__(self, manager: AirlineManager):
        self.manager = manager
        self.mode = "def"
        self.running = True
    
    def run(self):
        """Hauptschleife"""
        print("╔════════════════════════════════════════╗")
        print("║    🛫 AIRLINE MANAGER SIMULATOR 🛬    ║")
        print("╚════════════════════════════════════════╝")
        print(f"\n💰 Startkapital: €{self.manager.money:,.2f}")
        print(f"✈️  Startflugzeug: {self.manager.planes[0]}")
        print(f"📍 Standort: {self.manager.planes[0].current_city}")
        print("\nTippe 'help' für Hilfe\n")
        
        while self.running:
            try:
                self.show_status_bar()
                command = input(f"{self.mode}> ").strip()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                print("\n\n👋 Auf Wiedersehen!")
                break
            except Exception as e:
                print(f"❌ Fehler: {e}")
    
    def show_status_bar(self):
        """Zeigt Status-Informationen"""
        print(f"\n📊 Woche {self.manager.week} | 💰 €{self.manager.money:,.2f} | ✈️  {len(self.manager.planes)} Flugzeuge")
    
    def process_command(self, command: str):
        """Verarbeitet Befehl basierend auf Modus"""
        parts = command.split()
        cmd = parts[0].lower()
        
        # Globale Befehle
        if cmd == "help":
            self.show_help()
        elif cmd == "status":
            self.show_detailed_status()
        elif cmd == "mode":
            print(f"Aktueller Modus: {self.mode}")
        elif cmd == "exit" or cmd == "quit":
            if self.mode == "def":
                self.running = False
            else:
                self.mode = "def"
        
        # Modus-spezifische Befehle
        elif self.mode == "def":
            self.process_default_mode(cmd, parts)
        elif self.mode == "lis":
            self.process_list_mode(cmd)
        elif self.mode == "cre":
            self.process_create_mode(command)
        elif self.mode == "shop":
            self.process_shop_mode(command)
    
    def process_default_mode(self, cmd: str, parts: list):
        """Befehle im Default-Modus"""
        if cmd == "list":
            self.mode = "lis"
        elif cmd == "create":
            self.mode = "cre"
        elif cmd == "shop":
            self.mode = "shop"
        elif cmd == "check":
            self.check_plan()
        elif cmd == "next":
            self.advance_week()
        else:
            print(f"❓ Unbekannter Befehl: {cmd}")
    
    def show_detailed_status(self):
        """Zeigt detaillierte Statusinformationen"""
        print(f"\n{'='*50}")
        print(f"📊 AIRLINE STATUS - WOCHE {self.manager.week}")
        print(f"{'='*50}")
        print(f"💰 Kontostand: €{self.manager.money:,.2f}")
        print(f"✈️  Flotte: {len(self.manager.planes)} Flugzeuge")
        print(f"📅 Geplante Flüge diese Woche: {len(self.manager.flights)}")
        
        if self.manager.flights:
            total_potential = sum(f.calculate_profit() for f in self.manager.flights)
            maintenance = len(self.manager.planes) * 500
            print(f"💵 Erwarteter Gewinn: €{total_potential - maintenance:,.2f}")
    
    def process_list_mode(self, cmd: str):
        """Befehle im List-Modus"""
        if cmd == "planes":
            planes = self.manager.get_all_planes()
            if not planes:
                print("❌ Keine Flugzeuge vorhanden")
                return
            print("\n✈️  FLOTTE:")
            for plane in planes:
                print(f"  {plane.info()}")
                if plane.current_city:
                    print(f"    📍 Position: {plane.current_city}")
                print(f"    📋 Flüge: {len(plane.flights)}")
        
        elif cmd == "flights":
            flights = self.manager.get_all_flights()
            if not flights:
                print("❌ Keine Flüge geplant")
                return
            print("\n📋 FLUGPLAN:")
            for flight in flights:
                print(f"  {flight} → €{flight.calculate_profit():.2f}")
        
        elif cmd == "cities":
            cities = self.manager.get_all_cities()
            print("\n🌍 STÄDTE:")
            for city in cities:
                print(f"  {city.short:4} {city.name:15} Pop: {city.population:>9,}")
        
        else:
            print(f"❓ Unbekannter Befehl: {cmd}")
    
    def process_create_mode(self, command: str):
        """Befehle im Create-Modus"""
        parts = command.split()
        
        if parts[0] == "flight":
            if len(parts) == 6:
                try:
                    start = Instant.from_string(parts[4])
                    passengers = int(parts[5])
                    flight = self.manager.create_flight(parts[1], parts[2], parts[3], start, passengers)
                    print(f"\n✓ Flug erstellt:")
                    print(flight.info())
                except ValueError as e:
                    print(f"❌ {e}")
            else:
                print("Syntax: flight <von> <nach> <flugzeug> <start(M-10-30)> <passagiere>")
        
        else:
            print(f"❓ Unbekannter Befehl: {parts[0]}")
    
    def process_shop_mode(self, command: str):
        """Befehle im Shop-Modus"""
        parts = command.split()
        
        if parts[0] == "list":
            models = self.manager.get_available_models()
            print("\n🛒 FLUGZEUG-SHOP:")
            print(f"{'Nr':<4} {'Modell':<25} {'Preis':<12} {'Kapazität':<10} {'Max-Dist':<10} {'Geschw.'}")
            print("-" * 75)
            for i, model in enumerate(models, 1):
                affordable = "✓" if self.manager.money >= model.price else "✗"
                print(f"{i:<4} {model.name:<25} €{model.price:<10,} {model.capacity:<10} {model.max_distance:<10} {model.velocity} {affordable}")
        
        elif parts[0] == "buy":
            if len(parts) == 2:
                try:
                    # Versuche erst nach Index
                    if parts[1].isdigit():
                        idx = int(parts[1]) - 1
                        models = self.manager.get_available_models()
                        if 0 <= idx < len(models):
                            model_name = models[idx].name
                        else:
                            print(f"❌ Ungültige Nummer")
                            return
                    else:
                        model_name = " ".join(parts[1:])
                    
                    plane = self.manager.buy_plane(model_name)
                    print(f"\n✓ Flugzeug gekauft: {plane}")
                    print(f"💰 Neuer Kontostand: €{self.manager.money:,.2f}")
                except ValueError as e:
                    print(f"❌ {e}")
            else:
                print("Syntax: buy <modell-name oder nummer>")
        
        else:
            print(f"❓ Unbekannter Befehl: {parts[0]}")
    
    def check_plan(self):
        """Prüft Flugplan auf Probleme"""
        issues = self.manager.check_flight_plan()
        if not issues:
            print("✅ Flugplan ist gültig!")
        else:
            print(f"\n❌ Probleme gefunden ({len(issues)}):")
            for issue in issues:
                print(f"  {issue}")
    
    def advance_week(self):
        """Lässt Woche vergehen"""
        if not self.manager.flights:
            print("⚠️  Keine Flüge geplant! Nutze 'create' um Flüge zu erstellen.")
            return
        
        try:
            result = self.manager.advance_week()
            
            print(f"\n{'='*50}")
            print(f"📊 WOCHENABSCHLUSS - WOCHE {result['week']}")
            print(f"{'='*50}")
            print(f"✈️  Flüge durchgeführt: {result['flights']}")
            print(f"💵 Einnahmen:          €{result['revenue']:>12,.2f}")
            print(f"💸 Flugkosten:         €{result['cost'] - result['maintenance']:>12,.2f}")
            print(f"🔧 Wartung:            €{result['maintenance']:>12,.2f}")
            print(f"{'─'*50}")
            
            profit_symbol = "📈" if result['profit'] >= 0 else "📉"
            print(f"{profit_symbol} Gewinn/Verlust:    €{result['profit']:>12,.2f}")
            print(f"💰 Neuer Kontostand:   €{result['new_balance']:>12,.2f}")
            print(f"{'='*50}\n")
            
            if result['new_balance'] < 0:
                print("⚠️  WARNUNG: Negatives Guthaben!")
            
        except ValueError as e:
            print(f"❌ {e}")
    
    def show_help(self):
        """Zeigt Hilfe an"""
        if self.mode == "def":
            print("""
╔═══════════════════════════════════════════════╗
║              HAUPTMENÜ BEFEHLE                ║
╚═══════════════════════════════════════════════╝
  status  - Zeige detaillierten Status
  list    - Wechsel zu List-Modus (Übersichten)
  create  - Wechsel zu Create-Modus (Flüge planen)
  shop    - Wechsel zu Shop-Modus (Flugzeuge kaufen)
  check   - Prüfe aktuellen Flugplan
  next    - Nächste Woche (führt Flugplan aus!)
  exit    - Programm beenden
            """)
        elif self.mode == "lis":
            print("""
╔═══════════════════════════════════════════════╗
║              LIST-MODUS BEFEHLE               ║
╚═══════════════════════════════════════════════╝
  planes  - Zeige alle Flugzeuge der Flotte
  flights - Zeige alle geplanten Flüge
  cities  - Zeige alle verfügbaren Städte
  quit    - Zurück zum Hauptmenü
            """)
        elif self.mode == "cre":
            print("""
╔═══════════════════════════════════════════════╗
║             CREATE-MODUS BEFEHLE              ║
╚═══════════════════════════════════════════════╝
  flight <von> <nach> <flugzeug> <start> <pax>
  
  Beispiel:
    flight BER MUC D-GAME1 M-8-0 45
    
  Start-Format: Tag-Stunde-Minute
    M=Montag, T=Dienstag, W=Mittwoch, H=Donnerstag
    F=Freitag, S=Samstag, U=Sonntag
  
  quit - Zurück zum Hauptmenü
            """)
        elif self.mode == "shop":
            print("""
╔═══════════════════════════════════════════════╗
║              SHOP-MODUS BEFEHLE               ║
╚═══════════════════════════════════════════════╝
  list       - Zeige verfügbare Flugzeuge
  buy <nr>   - Kaufe Flugzeug (z.B. buy 3)
  quit       - Zurück zum Hauptmenü
            """)


# ==================== MAIN ====================

if __name__ == "__main__":
    manager = AirlineManager()
    cli = CLI(manager)
    cli.run()