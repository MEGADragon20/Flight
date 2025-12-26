import random, math
from typing import List, Optional
from pathlib import Path
from flask import json
import csv

def load_cities() -> List['City']:
    cities = []
    with open("cities.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    city = City(row[0], int(row[1]), float(row[2]), float(row[3]), row[4])
                    cities.append(city)
    return cities

def load_models() -> List['PlaneModel']:
    models = []
    path = Path("planes")
    for json_file in path.glob("**/*.json"):
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            models.append(PlaneModel.from_dict(data))
    return models

GAME_WORLD = {
    "cities": load_cities(),
    "models": load_models()
}

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
        EARTH_RADIUS_KM = 6371.0

        lat1 = math.radians(self.x)
        lon1 = math.radians(self.y)
        lat2 = math.radians(other.x)
        lon2 = math.radians(other.y)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2)**2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return EARTH_RADIUS_KM * c


class PlaneModel:
    def __init__(self, name: str, capacity: int, range: int, velocity: int, price: int, maintenance: int):
        self.name = name
        self.capacity = capacity
        self.range = range
        self.velocity = velocity
        self.price = price
        self.maintenance = maintenance
    
    def to_dict(self):
        return {
            'name': self.name,
            'capacity': self.capacity,
            'range': self.range,
            'velocity': self.velocity,
            'price': self.price,
            'maintenance': self.maintenance
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['capacity'], data['range'], 
                   data['velocity'], data['price'], data['maintenance'])


class Plane:
    def __init__(self, model: PlaneModel, registration: str):
        self.model = model
        self.registration = registration
        self.capacity = model.capacity
        self.range = model.range
        self.velocity = model.velocity
        self.current_city: Optional[City] = None
        self.flights: List['Flight'] = []
        self.maintenance = model.maintenance
    
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
        return distance <= self.range


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
        self.demand: dict[str, dict[str, int]] = {}
        self.money: float = 50000.0
        self.week: int = 1
        self.plane_counter: int = 1
        self.available_models: List[PlaneModel] = []
        self._initialize_game()
    
    def _initialize_game(self):
        self.cities = GAME_WORLD["cities"]
        self.update_demand()

        # planes available
        starter_model = PlaneModel("Dash 8 Q200", 39, 2000, 3, 50000, 200)
        path = Path("planes")
        for json_file in path.glob("**/*.json"):
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                self.available_models.append(PlaneModel.from_dict(data))

        starter_plane = Plane(starter_model, f"Starter")
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
            'available_models': [m.to_dict() for m in self.available_models],
            'demand': self.demand
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
        manager.demand = data['demand']
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

    def find_model(self, name: str) -> Optional[PlaneModel]:
        for model in self.available_models:
            if model.name.lower() == name.lower():
                return model
        return None

    def buy_plane(self, model_name: str, registration: str, city: City) -> Plane:
        model = self.find_model(model_name)
        if not model:
            raise ValueError(f"Flugzeugmodell '{model_name}' nicht gefunden")

        if self.money < model.price:
            raise ValueError(f"Nicht genug Geld!")
        
        self.money -= model.price
        self.plane_counter += 1
        
        plane = Plane(model, registration)
        plane.current_city = city
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

    def update_demand(self):
        self.demand.clear()
        for i in self.cities:
            self.demand[i.short] = {}
            for j in self.cities:
                self.demand[i.short][j.short] = get_route_demand(i, j)

    def flights_for_plane(self, plane):
        return [f for f in self.flights if f.plane == plane]

    def calculate_maintenance(self) -> float:
        total_maintenance = 0
        for plane in self.planes:
            total_maintenance += plane.maintenance*(len(self.flights_for_plane(plane)) + 1)
        return total_maintenance

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
        maintenance = self.calculate_maintenance()
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


def get_route_demand(origin: City, destination: City) -> int | None:
    if origin == destination:
        return None

    o = origin.population
    p = destination.population

    d = origin.distance_to(destination)
    d = max(d, 1)

    peak = 3000      # km where demand is strongest
    width = 2000         # how wide the sweet spot is

    distance_factor = math.exp(-((d - peak)**2) / (2 * width**2))

    pop_factor = (math.sqrt(o) * math.sqrt(p)) / 1000

    demand = pop_factor * (1 + 2 * distance_factor)

    # Big hubs stay relevant even when far away
    if d > 6000:
        hub_bonus = math.log10(o * p) / 10
        demand *= (1 + hub_bonus)

    demand *= random.uniform(0.09, 0.11)

    return round(max(demand, 0))