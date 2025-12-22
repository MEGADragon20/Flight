"""
Airline Manager - Flask Web Application
Installiere zuerst: pip install flask

Starte mit: python app.py
Dann öffne: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import math
from typing import List, Optional
import json
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ==================== MODEL CLASSES ====================

class Instant:
    DAYS = {'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday', 
            'H': 'Thursday', 'F': 'Friday', 'S': 'Saturday', 'U': 'Sunday'}
    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self, day: str, hour: int, minute: int):
        self.day = day
        self.hour = hour
        self.minute = minute
    
    def __str__(self):
        return f"{self.day}-{self.hour}-{self.minute}"
    
    def to_dict(self):
        return {'day': self.day, 'hour': self.hour, 'minute': self.minute}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['day'], data['hour'], data['minute'])
    
    @classmethod
    def from_string(cls, string: str):
        parts = string.split("-")
        return cls(parts[0], int(parts[1]), int(parts[2]))
    
    def to_minutes(self) -> int:
        day_index = list(self.DAYS.keys()).index(self.day)
        return day_index * 24 * 60 + self.hour * 60 + self.minute
    
    def add_minutes(self, minutes: int):
        total_minutes = self.to_minutes() + minutes
        day_index = (total_minutes // (24 * 60)) % 7
        remaining = total_minutes % (24 * 60)
        hour = remaining // 60
        minute = remaining % 60
        return Instant(list(self.DAYS.keys())[day_index], hour, minute)
    
    def format_time(self):
        return f"{self.hour:02d}:{self.minute:02d}"


class City:
    def __init__(self, name: str, population: int, x: int, y: int, short: str):
        self.name = name
        self.population = population
        self.x = x
        self.y = y
        self.short = short
    
    def to_dict(self):
        return {
            'name': self.name,
            'population': self.population,
            'x': self.x,
            'y': self.y,
            'short': self.short
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['population'], data['x'], data['y'], data['short'])
    
    def distance_to(self, other: 'City') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class PlaneModel:
    def __init__(self, name: str, capacity: int, max_distance: int, velocity: int, price: int):
        self.name = name
        self.capacity = capacity
        self.max_distance = max_distance
        self.velocity = velocity
        self.price = price
    
    def to_dict(self):
        return {
            'name': self.name,
            'capacity': self.capacity,
            'max_distance': self.max_distance,
            'velocity': self.velocity,
            'price': self.price
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['capacity'], data['max_distance'], 
                   data['velocity'], data['price'])


class Plane:
    def __init__(self, model: PlaneModel, registration: str):
        self.model = model
        self.registration = registration
        self.capacity = model.capacity
        self.max_distance = model.max_distance
        self.velocity = model.velocity
        self.current_city: Optional[City] = None
        self.flights: List['Flight'] = []
    
    def to_dict(self):
        return {
            'model': self.model.to_dict(),
            'registration': self.registration,
            'current_city': self.current_city.to_dict() if self.current_city else None,
            'flight_count': len(self.flights)
        }
    
    @classmethod
    def from_dict(cls, data, cities):
        model = PlaneModel.from_dict(data['model'])
        plane = cls(model, data['registration'])
        if data['current_city']:
            city_short = data['current_city']['short']
            plane.current_city = next((c for c in cities if c.short == city_short), None)
        return plane
    
    def can_fly(self, distance: float) -> bool:
        return distance <= self.max_distance


class Flight:
    PRICE_PER_KM = 0.15
    COST_PER_KM = 0.08
    
    def __init__(self, origin: City, destination: City, plane: Plane, start: Instant, passengers: int):
        self.origin = origin
        self.destination = destination
        self.plane = plane
        self.passengers = passengers
        self.distance = origin.distance_to(destination)
        self.duration = round(self.distance / plane.velocity)
        self.start = start
        self.end = start.add_minutes(self.duration)
    
    def to_dict(self):
        return {
            'origin': self.origin.to_dict(),
            'destination': self.destination.to_dict(),
            'plane_registration': self.plane.registration,
            'passengers': self.passengers,
            'start': self.start.to_dict(),
            'distance': self.distance,
            'duration': self.duration,
            'profit': self.calculate_profit()
        }
    
    @classmethod
    def from_dict(cls, data, cities, planes):
        origin = next(c for c in cities if c.short == data['origin']['short'])
        dest = next(c for c in cities if c.short == data['destination']['short'])
        plane = next(p for p in planes if p.registration == data['plane_registration'])
        start = Instant.from_dict(data['start'])
        return cls(origin, dest, plane, start, data['passengers'])
    
    def calculate_revenue(self) -> float:
        return self.passengers * self.distance * self.PRICE_PER_KM
    
    def calculate_cost(self) -> float:
        return self.distance * self.COST_PER_KM
    
    def calculate_profit(self) -> float:
        return self.calculate_revenue() - self.calculate_cost()


# ==================== GAME MANAGER ====================

class AirlineManager:
    def __init__(self):
        self.cities: List[City] = []
        self.planes: List[Plane] = []
        self.flights: List[Flight] = []
        self.money: float = 50000.0
        self.week: int = 1
        self.plane_counter: int = 1
        self.available_models: List[PlaneModel] = []
        self._initialize_game()
    
    def _initialize_game(self):
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
        
        starter_model = PlaneModel("Dash 8 Q200", 50, 2000, 40, 50000)
        self.available_models = [
            PlaneModel("Cessna 172", 4, 1200, 4, 15000),
            PlaneModel("DHC-6 Twin Otter", 19, 1400, 30, 35000),
            starter_model,
            PlaneModel("ATR 72", 70, 1500, 45, 80000),
            PlaneModel("Boeing 737", 180, 5500, 70, 250000),
            PlaneModel("Airbus A320", 180, 6100, 75, 280000),
            PlaneModel("Boeing 787", 330, 14000, 90, 650000),
            PlaneModel("Airbus A350", 350, 15000, 95, 700000),
        ]
        
        
        starter_plane = Plane(starter_model, f"D-GAME{self.plane_counter}")
        starter_plane.current_city = self.cities[0]
        self.planes.append(starter_plane)
        self.plane_counter += 1
    
    def to_dict(self):
        return {
            'cities': [c.to_dict() for c in self.cities],
            'planes': [p.to_dict() for p in self.planes],
            'flights': [f.to_dict() for f in self.flights],
            'money': self.money,
            'week': self.week,
            'plane_counter': self.plane_counter,
            'available_models': [m.to_dict() for m in self.available_models]
        }
    
    @classmethod
    def from_dict(cls, data):
        manager = cls.__new__(cls)
        manager.cities = [City.from_dict(c) for c in data['cities']]
        manager.available_models = [PlaneModel.from_dict(m) for m in data['available_models']]
        manager.planes = [Plane.from_dict(p, manager.cities) for p in data['planes']]
        manager.flights = [Flight.from_dict(f, manager.cities, manager.planes) 
                          for f in data['flights']]
        
        for plane in manager.planes:
            plane.flights = [f for f in manager.flights if f.plane.registration == plane.registration]
        
        manager.money = data['money']
        manager.week = data['week']
        manager.plane_counter = data['plane_counter']
        return manager
    
    def find_city(self, name: str) -> Optional[City]:
        for city in self.cities:
            if city.name.lower() == name.lower() or city.short.lower() == name.lower():
                return city
        return None
    
    def find_plane(self, registration: str) -> Optional[Plane]:
        for plane in self.planes:
            if plane.registration.lower() == registration.lower():
                return plane
        return None
    
    def buy_plane(self, model_name: str) -> Plane:
        model = None
        for m in self.available_models:
            if m.name.lower() == model_name.lower():
                model = m
                break
        
        if not model:
            raise ValueError(f"Flugzeugmodell '{model_name}' nicht gefunden")
        
        if self.money < model.price:
            raise ValueError(f"Nicht genug Geld!")
        
        self.money -= model.price
        registration = f"D-GAME{self.plane_counter}"
        self.plane_counter += 1
        
        plane = Plane(model, registration)
        plane.current_city = self.cities[0]
        self.planes.append(plane)
        
        return plane
    
    def create_flight(self, origin_name: str, dest_name: str, 
                     plane_reg: str, start: Instant, passengers: int) -> Flight:
        origin = self.find_city(origin_name)
        destination = self.find_city(dest_name)
        plane = self.find_plane(plane_reg)
        
        if not origin or not destination or not plane:
            raise ValueError("Stadt oder Flugzeug nicht gefunden")
        
        if passengers > plane.capacity:
            raise ValueError(f"Zu viele Passagiere! Max: {plane.capacity}")
        
        distance = origin.distance_to(destination)
        if not plane.can_fly(distance):
            raise ValueError(f"Flugzeug kann diese Distanz nicht fliegen")
        
        flight = Flight(origin, destination, plane, start, passengers)
        self.flights.append(flight)
        plane.flights.append(flight)
        return flight
    
    def delete_flight(self, plane_reg: str, start_str: str) -> bool:
        """Löscht einen Flug"""
        for i, flight in enumerate(self.flights):
            if (flight.plane.registration == plane_reg and 
                str(flight.start) == start_str):
                # Entferne von globaler Liste
                self.flights.pop(i)
                # Entferne von Flugzeug
                flight.plane.flights = [f for f in flight.plane.flights 
                                       if not (str(f.start) == start_str)]
                return True
        return False
    
    def check_flight_plan(self) -> List[str]:
        issues = []
        for plane in self.planes:
            if not plane.flights:
                continue
            sorted_flights = sorted(plane.flights, key=lambda f: f.start.to_minutes())
            
            first_flight = sorted_flights[0]
            if plane.current_city and plane.current_city != first_flight.origin:
                issues.append(f"{plane.registration}: Flugzeug ist in {plane.current_city.name}, erster Flug startet in {first_flight.origin.name}")
            
            for i in range(len(sorted_flights) - 1):
                current = sorted_flights[i]
                next_flight = sorted_flights[i + 1]
                
                if current.destination != next_flight.origin:
                    issues.append(f"{plane.registration}: Flug landet in {current.destination.name}, nächster startet in {next_flight.origin.name}")
                
                if current.end.to_minutes() > next_flight.start.to_minutes():
                    issues.append(f"{plane.registration}: Zeitüberschneidung")
        
        return issues
    
    def advance_week(self) -> dict:
        issues = self.check_flight_plan()
        if issues:
            raise ValueError("Flugplan ungültig!")
        
        total_revenue = 0
        total_cost = 0
        flight_count = len(self.flights)
        
        for flight in self.flights:
            total_revenue += flight.calculate_revenue()
            total_cost += flight.calculate_cost()
            flight.plane.current_city = flight.destination
        
        maintenance = len(self.planes) * 500
        total_cost += maintenance
        total_profit = total_revenue - total_cost
        
        self.money += total_profit
        self.week += 1
        
        # Lösche Flüge
        self.flights.clear()
        for plane in self.planes:
            plane.flights.clear()
        
        return {
            'week': self.week - 1,
            'flights': flight_count,
            'revenue': total_revenue,
            'cost': total_cost - maintenance,
            'maintenance': maintenance,
            'profit': total_profit,
            'new_balance': self.money
        }


# ==================== FLASK ROUTES ====================

def get_manager():
    """Holt oder erstellt Manager aus Session"""
    if 'game_data' not in session:
        manager = AirlineManager()
        session['game_data'] = manager.to_dict()
    else:
        manager = AirlineManager.from_dict(session['game_data'])
    return manager

def save_manager(manager):
    """Speichert Manager in Session"""
    session['game_data'] = manager.to_dict()
    session.modified = True

@app.route('/')
def index():
    manager = get_manager()
    
    # Berechne erwarteten Gewinn
    expected_profit = sum(f.calculate_profit() for f in manager.flights)
    expected_profit -= len(manager.planes) * 500
    
    issues = manager.check_flight_plan()

    return render_template("dashboard.html", manager=manager, expected_profit=expected_profit, issues=issues)

@app.route('/hangar')
def hangar():
    manager = get_manager()
    return render_template("hangar.html", manager=manager)

@app.route('/shop')
def shop():
    manager = get_manager()
    return render_template("shop.html", manager=manager)

@app.route('/shop/buy/<model_name>', methods=['POST'])
def buy_plane(model_name):
    manager = get_manager()
    try:
        manager.buy_plane(model_name)
        save_manager(manager)
        return redirect(url_for('hangar'))
    except ValueError as e:
        return render_template("shop.html", manager=manager, error=str(e))

@app.route('/cities')
def cities():
    manager = get_manager()
    return render_template("cities.html", manager=manager)

@app.route('/calendar')
@app.route('/calendar/<day>')
def calendar(day='M'):
    manager = get_manager()
    
    # Gruppiere Flüge nach Tag
    flights_by_day = {}
    for day_code in Instant.DAYS.keys():
        flights_by_day[day_code] = []
    
    for flight in manager.flights:
        flights_by_day[flight.start.day].append(flight)

    for day_code in flights_by_day:
        flights_by_day[day_code].sort(key=lambda f: f.start.to_minutes())
    day_flights = flights_by_day[day]
    day_profit = sum(f.calculate_profit() for f in day_flights)
    return render_template("calendar.html", manager=manager, current_day=day, flights_by_day=flights_by_day, day_profit=day_profit, days=Instant.DAYS)

@app.route('/calendar/add', methods=['POST'])
def add_flight():
    manager = get_manager()
    try:
        origin = request.form['origin']
        destination = request.form['destination']
        plane = request.form['plane']
        day = request.form['day']
        hour = int(request.form['hour'])
        minute = int(request.form['minute'])
        passengers = int(request.form['passengers'])
        
        start = Instant(day, hour, minute)
        manager.create_flight(origin, destination, plane, start, passengers)
        save_manager(manager)
        
        return redirect(url_for('calendar', day=day))
    except Exception as e:
        return redirect(url_for('calendar', error=str(e)))

@app.route('/calendar/delete', methods=['POST'])
def delete_flight():
    manager = get_manager()
    plane_reg = request.form['plane']
    start_str = request.form['start']
    day = request.form['day']
    
    manager.delete_flight(plane_reg, start_str)
    save_manager(manager)
    
    return redirect(url_for('calendar', day=day))

@app.route('/advance_week', methods=['POST'])
def advance_week():
    manager = get_manager()
    try:
        result = manager.advance_week()
        save_manager(manager)
        return render_template("week_result.html", result=result, manager=manager)
    except ValueError as e:
        return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("=" * 50)
    print("✈️  AIRLINE MANAGER - Web App")
    print("=" * 50)
    print("\n🚀 Server startet...")
    print("📱 Öffne im Browser: http://localhost:5000")
    print("🛑 Zum Beenden: Strg+C\n")
    app.run(debug=True)
