"""
Airline Manager - Flask Web Application
Installiere zuerst: pip install flask

Starte mit: python app.py
Dann öffne: http://localhost:5000
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
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
        
        self.available_models = [
            PlaneModel("Cessna 172", 4, 1200, 20, 15000),
            PlaneModel("DHC-6 Twin Otter", 19, 1400, 30, 35000),
            PlaneModel("ATR 72", 70, 1500, 45, 80000),
            PlaneModel("Boeing 737", 180, 5500, 70, 250000),
            PlaneModel("Airbus A320", 180, 6100, 75, 280000),
            PlaneModel("Boeing 787", 330, 14000, 90, 650000),
            PlaneModel("Airbus A350", 350, 15000, 95, 700000),
        ]
        
        starter_model = PlaneModel("Dash 8 Q200", 50, 2000, 40, 0)
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
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                 manager=manager,
                                 expected_profit=expected_profit,
                                 issues=issues)

@app.route('/hangar')
def hangar():
    manager = get_manager()
    return render_template_string(HANGAR_TEMPLATE, manager=manager)

@app.route('/shop')
def shop():
    manager = get_manager()
    return render_template_string(SHOP_TEMPLATE, manager=manager)

@app.route('/shop/buy/<model_name>', methods=['POST'])
def buy_plane(model_name):
    manager = get_manager()
    try:
        manager.buy_plane(model_name)
        save_manager(manager)
        return redirect(url_for('hangar'))
    except ValueError as e:
        return render_template_string(SHOP_TEMPLATE, manager=manager, error=str(e))

@app.route('/cities')
def cities():
    manager = get_manager()
    return render_template_string(CITIES_TEMPLATE, manager=manager)

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
    return render_template_string(CALENDAR_TEMPLATE, 
                                 manager=manager,
                                 current_day=day,
                                 flights_by_day=flights_by_day,
                                 day_profit=day_profit,
                                 days=Instant.DAYS)

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
        return render_template_string(WEEK_RESULT_TEMPLATE, result=result, manager=manager)
    except ValueError as e:
        return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    return redirect(url_for('index'))

# ==================== HTML TEMPLATES ====================

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Airline Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover:hover { transform: translateY(-2px); transition: all 0.3s; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    <nav class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-4">
            <div class="flex items-center justify-between py-4">
                <div class="flex items-center space-x-2">
                    <span class="text-3xl">✈️</span>
                    <span class="text-2xl font-bold">Airline Manager</span>
                </div>
                <div class="flex items-center space-x-6">
                    <div class="text-right">
                        <div class="text-sm opacity-90">Woche {{ manager.week }}</div>
                        <div class="text-2xl font-bold">€{{ "{:,.2f}".format(manager.money) }}</div>
                    </div>
                </div>
            </div>
            <div class="flex space-x-1 pb-3">
                <a href="{{ url_for('index') }}" class="px-4 py-2 rounded-t-lg hover:bg-white hover:bg-opacity-20 transition {% if request.endpoint == 'index' %}bg-white bg-opacity-20{% endif %}">📊 Dashboard</a>
                <a href="{{ url_for('calendar') }}" class="px-4 py-2 rounded-t-lg hover:bg-white hover:bg-opacity-20 transition {% if 'calendar' in request.endpoint %}bg-white bg-opacity-20{% endif %}">📅 Flugplan</a>
                <a href="{{ url_for('hangar') }}" class="px-4 py-2 rounded-t-lg hover:bg-white hover:bg-opacity-20 transition {% if request.endpoint == 'hangar' %}bg-white bg-opacity-20{% endif %}">✈️ Hangar ({{ manager.planes|length }})</a>
                <a href="{{ url_for('shop') }}" class="px-4 py-2 rounded-t-lg hover:bg-white hover:bg-opacity-20 transition {% if request.endpoint == 'shop' %}bg-white bg-opacity-20{% endif %}">🛒 Shop</a>
                <a href="{{ url_for('cities') }}" class="px-4 py-2 rounded-t-lg hover:bg-white hover:bg-opacity-20 transition {% if request.endpoint == 'cities' %}bg-white bg-opacity-20{% endif %}">🌍 Städte</a>
            </div>
        </div>
    </nav>

    <!-- Content -->
    <div class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
    """
SHOP_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="bg-white rounded-lg shadow-md p-6">
    <h1 class="text-3xl font-bold mb-6">🛒 Flugzeug-Shop</h1>
    
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
        ❌ {{ error }}
    </div>
    {% endif %}
    
    <div class="mb-6 bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg">
        <p class="text-sm text-gray-600">Dein Budget</p>
        <p class="text-3xl font-bold text-blue-600">€{{ "{:,.2f}".format(manager.money) }}</p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for model in manager.available_models %}
        <div class="border-2 rounded-lg p-5 {% if manager.money >= model.price %}border-green-300 hover:shadow-xl{% else %}border-gray-200 opacity-60{% endif %} transition card-hover">
            <div class="flex items-start justify-between mb-3">
                <h3 class="text-lg font-bold">{{ model.name }}</h3>
                <span class="text-3xl">✈️</span>
            </div>
            
            <div class="mb-4">
                <p class="text-3xl font-bold text-blue-600">€{{ "{:,}".format(model.price) }}</p>
            </div>
            
            <div class="space-y-2 text-sm mb-4">
                <div class="flex items-center justify-between">
                    <span class="text-gray-600">👥 Kapazität:</span>
                    <span class="font-semibold">{{ model.capacity }}</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-gray-600">📏 Reichweite:</span>
                    <span class="font-semibold">{{ model.max_distance }} km</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-gray-600">⚡ Geschwindigkeit:</span>
                    <span class="font-semibold">{{ model.velocity }} km/min</span>
                </div>
            </div>
            
            <form method="POST" action="{{ url_for('buy_plane', model_name=model.name) }}">
                <button type="submit" 
                        class="w-full py-2 rounded-lg font-semibold transition
                        {% if manager.money >= model.price %}
                            bg-green-600 text-white hover:bg-green-700
                        {% else %}
                            bg-gray-300 text-gray-500 cursor-not-allowed
                        {% endif %}"
                        {% if manager.money < model.price %}disabled{% endif %}>
                    {% if manager.money >= model.price %}
                        💳 Kaufen
                    {% else %}
                        🔒 Zu teuer
                    {% endif %}
                </button>
            </form>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
""")    

CITIES_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="bg-white rounded-lg shadow-md p-6">
    <h1 class="text-3xl font-bold mb-6">🌍 Städte-Übersicht</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {% for city in manager.cities %}
        <div class="border rounded-lg p-4 hover:shadow-lg transition card-hover">
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-xl font-bold">{{ city.short }}</h3>
                <span class="text-2xl">🏙️</span>
            </div>
            <p class="text-lg font-semibold text-gray-700 mb-2">{{ city.name }}</p>
            <div class="text-sm text-gray-600">
                <p>👥 {{ "{:,}".format(city.population) }} Einwohner</p>
                <p class="text-xs mt-2">📍 Position: ({{ city.x }}, {{ city.y }})</p>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div class="mt-8 bg-blue-50 p-4 rounded-lg">
        <h3 class="font-bold mb-2">💡 Tipp</h3>
        <p class="text-sm text-gray-700">Größere Städte haben mehr potenzielle Passagiere. Plane deine Routen strategisch!</p>
    </div>
</div>
{% endblock %}
""")

CALENDAR_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="bg-white rounded-lg shadow-md p-6 mb-6">
    <h1 class="text-3xl font-bold mb-6">📅 Flugplan - Woche {{ manager.week }}</h1>
    
    <!-- Tag-Navigation -->
    <div class="flex space-x-2 mb-6 overflow-x-auto">
        {% for day_code, day_name in days.items() %}
        <a href="{{ url_for('calendar', day=day_code) }}" 
           class="px-4 py-2 rounded-lg font-semibold transition whitespace-nowrap
                  {% if current_day == day_code %}
                      bg-blue-600 text-white
                  {% else %}
                      bg-gray-100 text-gray-700 hover:bg-gray-200
                  {% endif %}">
            {{ day_name }}
            <span class="text-xs block">{{ flights_by_day[day_code]|length }} Flüge</span>
        </a>
        {% endfor %}
    </div>
    
    <!-- Flug hinzufügen -->
    <div class="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg mb-6">
        <h3 class="font-bold mb-3">✈️ Neuen Flug planen</h3>
        <form method="POST" action="{{ url_for('add_flight') }}" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <input type="hidden" name="day" value="{{ current_day }}">
            
            <select name="plane" required class="border rounded px-3 py-2 text-sm">
                <option value="">Flugzeug</option>
                {% for plane in manager.planes %}
                <option value="{{ plane.registration }}">{{ plane.registration }}</option>
                {% endfor %}
            </select>
            
            <select name="origin" required class="border rounded px-3 py-2 text-sm">
                <option value="">Von</option>
                {% for city in manager.cities %}
                <option value="{{ city.short }}">{{ city.short }}</option>
                {% endfor %}
            </select>
            
            <select name="destination" required class="border rounded px-3 py-2 text-sm">
                <option value="">Nach</option>
                {% for city in manager.cities %}
                <option value="{{ city.short }}">{{ city.short }}</option>
                {% endfor %}
            </select>
            
            <input type="number" name="hour" min="0" max="23" placeholder="Stunde" required class="border rounded px-3 py-2 text-sm">
            <input type="number" name="minute" min="0" max="59" step="5" placeholder="Min" required class="border rounded px-3 py-2 text-sm">
            <input type="number" name="passengers" min="1" placeholder="Pax" required class="border rounded px-3 py-2 text-sm">
            
            <button type="submit" class="col-span-2 bg-green-600 text-white rounded px-4 py-2 hover:bg-green-700 transition text-sm font-semibold">
                ➕ Flug hinzufügen
            </button>
        </form>
    </div>
</div>

<!-- Flugplan-Übersicht -->
<div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold mb-4">{{ days[current_day] }} - Flugübersicht</h2>
    
    {% if not flights_by_day[current_day] %}
        <p class="text-gray-500 text-center py-8">Keine Flüge für diesen Tag geplant.</p>
    {% else %}
        <!-- Gruppiere nach Flugzeug -->
        {% set ns = namespace(planes_with_flights=[]) %}
        {% for plane in manager.planes %}
            {% set plane_flights = [] %}
            {% for flight in flights_by_day[current_day] %}
                {% if flight.plane.registration == plane.registration %}
                    {% set _ = plane_flights.append(flight) %}
                {% endif %}
            {% endfor %}
            {% if plane_flights %}
                {% set _ = ns.planes_with_flights.append((plane, plane_flights)) %}
            {% endif %}
        {% endfor %}
        
        <div class="space-y-6">
            {% for plane, plane_flights in ns.planes_with_flights %}
            <div class="border-2 border-blue-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-blue-600">✈️ {{ plane.registration }} ({{ plane.model.name }})</h3>
                    <span class="text-sm text-gray-600">{{ plane_flights|length }} Flüge</span>
                </div>
                
                <div class="space-y-3">
                    {% for flight in plane_flights %}
                    <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <div class="flex items-center space-x-3 mb-2">
                                    <span class="text-2xl font-bold text-gray-700">{{ flight.start.format_time() }}</span>
                                    <span class="text-gray-400">→</span>
                                    <span class="text-lg font-semibold text-gray-600">{{ flight.end.format_time() }}</span>
                                    <span class="text-sm text-gray-500">({{ flight.duration }} min)</span>
                                </div>
                                <div class="flex items-center space-x-4 text-sm">
                                    <span class="font-semibold">{{ flight.origin.short }} → {{ flight.destination.short }}</span>
                                    <span class="text-gray-600">👥 {{ flight.passengers }}/{{ plane.capacity }}</span>
                                    <span class="text-gray-600">📏 {{ "%.0f"|format(flight.distance) }} km</span>
                                    <span class="font-semibold {% if flight.calculate_profit() >= 0 %}text-green-600{% else %}text-red-600{% endif %}">
                                        💰 €{{ "{:,.2f}".format(flight.calculate_profit()) }}
                                    </span>
                                </div>
                            </div>
                            <form method="POST" action="{{ url_for('delete_flight') }}" class="ml-4">
                                <input type="hidden" name="plane" value="{{ flight.plane.registration }}">
                                <input type="hidden" name="start" value="{{ flight.start }}">
                                <input type="hidden" name="day" value="{{ current_day }}">
                                <button type="submit" class="text-red-600 hover:text-red-800 font-bold text-xl" onclick="return confirm('Flug löschen?');">
                                    🗑️
                                </button>
                            </form>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="mt-6 bg-blue-50 p-4 rounded-lg">
    <div class="flex justify-between items-center">
        <span class="font-semibold">
            Tagesgewinn ({{ days[current_day] }}):
        </span>
        <span class="text-xl font-bold
            {% if day_profit >= 0 %}
                text-green-600
            {% else %}
                text-red-600
            {% endif %}
            ">
                €{{ "{:,.2f}".format(day_profit) }}
            </span>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
""")

WEEK_RESULT_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="bg-white rounded-lg shadow-xl p-8">
        <div class="text-center mb-6">
            <h1 class="text-4xl font-bold mb-2">📊 Wochenabschluss</h1>
            <p class="text-gray-600">Woche {{ result.week }}</p>
        </div>
        
        <div class="space-y-4 mb-6">
            <div class="flex justify-between items-center py-3 border-b">
                <span class="text-gray-700">✈️ Flüge durchgeführt:</span>
                <span class="text-xl font-bold">{{ result.flights }}</span>
            </div>
            
            <div class="flex justify-between items-center py-3 border-b">
                <span class="text-gray-700">💵 Einnahmen:</span>
                <span class="text-xl font-bold text-green-600">€{{ "{:,.2f}".format(result.revenue) }}</span>
            </div>
            
            <div class="flex justify-between items-center py-3 border-b">
                <span class="text-gray-700">💸 Flugkosten:</span>
                <span class="text-xl font-bold text-red-600">-€{{ "{:,.2f}".format(result.cost) }}</span>
            </div>
            
            <div class="flex justify-between items-center py-3 border-b">
                <span class="text-gray-700">🔧 Wartung:</span>
                <span class="text-xl font-bold text-red-600">-€{{ "{:,.2f}".format(result.maintenance) }}</span>
            </div>
            
            <div class="flex justify-between items-center py-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg px-4 mt-4">
                <span class="text-lg font-bold">{% if result.profit >= 0 %}📈{% else %}📉{% endif %} Gewinn/Verlust:</span>
                <span class="text-3xl font-bold {% if result.profit >= 0 %}text-green-600{% else %}text-red-600{% endif %}">
                    €{{ "{:,.2f}".format(result.profit) }}
                </span>
            </div>
            
            <div class="flex justify-between items-center py-4 bg-blue-600 text-white rounded-lg px-4">
                <span class="text-lg font-bold">💰 Neuer Kontostand:</span>
                <span class="text-3xl font-bold">€{{ "{:,.2f}".format(result.new_balance) }}</span>
            </div>
        </div>
        
        {% if result.new_balance < 0 %}
        <div class="bg-red-50 border-l-4 border-red-600 p-4 mb-6">
            <p class="font-bold text-red-700">⚠️ WARNUNG: Negatives Guthaben!</p>
            <p class="text-red-600 text-sm">Du musst profitabler wirtschaften!</p>
        </div>
        {% endif %}
        
        <div class="text-center space-x-4">
            <a href="{{ url_for('calendar') }}" class="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition font-semibold">
                📅 Flüge planen
            </a>
            <a href="{{ url_for('index') }}" class="inline-block bg-gray-600 text-white px-8 py-3 rounded-lg hover:bg-gray-700 transition font-semibold">
                🏠 Dashboard
            </a>
        </div>
    </div>
</div>
{% endblock %}
""")

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
    <div class="bg-white rounded-lg shadow-md p-6 card-hover">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-600 text-sm">Kontostand</p>
                <p class="text-3xl font-bold text-green-600">€{{ "{:,.2f}".format(manager.money) }}</p>
            </div>
            <div class="text-5xl">💰</div>
        </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-md p-6 card-hover">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-600 text-sm">Flotte</p>
                <p class="text-3xl font-bold text-blue-600">{{ manager.planes|length }}</p>
            </div>
            <div class="text-5xl">✈️</div>
        </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-md p-6 card-hover">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-600 text-sm">Geplante Flüge</p>
                <p class="text-3xl font-bold text-purple-600">{{ manager.flights|length }}</p>
            </div>
            <div class="text-5xl">📋</div>
        </div>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-bold mb-4">📈 Wochenprognose</h2>
        <div class="space-y-3">
            <div class="flex justify-between">
                <span class="text-gray-600">Erwarteter Gewinn:</span>
                <span class="font-bold {% if expected_profit >= 0 %}text-green-600{% else %}text-red-600{% endif %}">
                    €{{ "{:,.2f}".format(expected_profit) }}
                </span>
            </div>
            <div class="flex justify-between text-sm">
                <span class="text-gray-500">Wartungskosten:</span>
                <span class="text-gray-700">€{{ "{:,.2f}".format(manager.planes|length * 500) }}</span>
            </div>
        </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-bold mb-4">⚠️ Flugplan-Status</h2>
        {% if issues %}
            <div class="space-y-2">
                {% for issue in issues %}
                <div class="text-sm text-red-600 bg-red-50 p-2 rounded">{{ issue }}</div>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-green-600 bg-green-50 p-3 rounded flex items-center">
                <span class="text-2xl mr-2">✅</span>
                <span>Flugplan ist gültig!</span>
            </div>
        {% endif %}
    </div>
</div>

<div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-bold mb-4">🎮 Aktionen</h2>
    <div class="flex space-x-4">
        <a href="{{ url_for('calendar') }}" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition">
            📅 Flüge planen
        </a>
        <form method="POST" action="{{ url_for('advance_week') }}" onsubmit="return confirm('Woche vergehen lassen?');">
            <button type="submit" class="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition" {% if not manager.flights or issues %}disabled class="bg-gray-400 cursor-not-allowed"{% endif %}>
                ⏭️ Nächste Woche
            </button>
        </form>
        <form method="POST" action="{{ url_for('reset') }}" onsubmit="return confirm('Spiel wirklich zurücksetzen?');">
            <button type="submit" class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition">
                🔄 Neustart
            </button>
        </form>
    </div>
</div>
{% endblock %}
""")

HANGAR_TEMPLATE = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', """
{% block content %}
<div class="bg-white rounded-lg shadow-md p-6">
    <h1 class="text-3xl font-bold mb-6">✈️ Hangar - Deine Flotte</h1>
    
    {% if not manager.planes %}
        <p class="text-gray-600">Keine Flugzeuge vorhanden.</p>
    {% else %}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {% for plane in manager.planes %}
            <div class="border rounded-lg p-5 hover:shadow-lg transition card-hover">
                <div class="flex items-start justify-between mb-3">
                    <h3 class="text-xl font-bold">{{ plane.registration }}</h3>
                    <span class="text-3xl">✈️</span>
                </div>
                <p class="text-gray-700 font-semibold mb-3">{{ plane.model.name }}</p>
                
                <div class="space-y-2 text-sm mb-4">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Kapazität:</span>
                        <span class="font-semibold">{{ plane.capacity }} Passagiere</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Max. Reichweite:</span>
                        <span class="font-semibold">{{ plane.max_distance }} km</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Geschwindigkeit:</span>
                        <span class="font-semibold">{{ plane.velocity }} km/min</span>
                    </div>
                </div>
                
                {% if plane.current_city %}
                <div class="bg-blue-50 p-3 rounded mb-3">
                    <p class="text-sm text-gray-600">Aktueller Standort:</p>
                    <p class="font-semibold">{{ plane.current_city.name }}</p>
                </div>
                {% endif %}
                
                <div class="bg-purple-50 p-3 rounded">
                    <p class="text-sm text-gray-600">Geplante Flüge:</p>
                    <p class="font-bold text-purple-600">{{ plane.flights|length }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    {% endif %}
</div>
{% endblock %}
""")                     
if __name__ == '__main__':
    print("=" * 50)
    print("✈️  AIRLINE MANAGER - Web App")
    print("=" * 50)
    print("\n🚀 Server startet...")
    print("📱 Öffne im Browser: http://localhost:5000")
    print("🛑 Zum Beenden: Strg+C\n")
    app.run(debug=True)
