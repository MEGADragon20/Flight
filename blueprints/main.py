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
                    city = City(row[0], int(row[1]), float(row[2]), float(row[3]), row[4], float(row[5]))
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
    def __init__(self, name: str, population: int, x: int, y: int, short: str, timezone: float):
        self.name = name
        self.population = population
        self.x = x
        self.y = y
        self.short = short
        self.timezone = timezone
    
    def to_dict(self):
        return {
            'name': self.name,
            'population': self.population,
            'x': self.x,
            'y': self.y,
            'short': self.short,
            'timezone': self.timezone
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['name'], data['population'], data['x'], data['y'], data['short'], data['timezone'])
    
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

class Hub:
    LEVEL = {
        1: {
            "name": "Permission",
            "weekly_cost": 50,
        },
        2: {
            "name": "Access",
            "weekly_cost": 100,
        },
        3: {
            "name": "Outpost",
            "weekly_cost": 200,
        },
        4: {
            "name": "Link",
            "weekly_cost": 500,
        },
        5: {
            "name": "Base",
            "weekly_cost": 1000,
        },
        6: {
            "name": "Hublet",
            "weekly_cost": 2000,
        },
        7: {
            "name": "Gateway",
            "weekly_cost": 5000,
        },
        8: {
            "name": "Anchor",
            "weekly_cost": 10000,
        },
        9: {
            "name": "Hub",
            "weekly_cost": 20000    
        },
        10: {
            "name": "Main Hub",
            "weekly_cost": 50000
        }
    }
    def __init__(self, city: City, level: int = 1):
        self.city = city
        self.level = level
        self.passenger_bonus = 1 + round(0.025*level**2, 1)
        self.name = Hub.LEVEL[level]["name"]
        self.weekly_cost = Hub.LEVEL[level]["weekly_cost"]

    def upgrade(self):
        self.level += 1
        self.passenger_bonus += 0.1

    @classmethod
    def from_dict(cls, data: dict):
        cities = get_cities()
        city_short = data['city']
        city = next((c for c in cities if c.short == city_short), None)

        return cls(city, int(data['level']))

    def to_dict(self):
        return {
            'city': self.city.short,
            'level': self.level
        }


class PlaneModel:
    def __init__(self, name: str, capacity: int, range: int, velocity: int, price: int, maintenance: int, pilots: int):
        self.name = name
        self.capacity = capacity
        self.range = range
        self.velocity = velocity
        self.price = price
        self.maintenance = maintenance
        self.pilots = pilots
    
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
                   data['velocity'], data['price'], data['maintenance'], data['pilots'])


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
        self.pilots = model.pilots

    def to_dict(self):
        return {
            'model': self.model.name,
            'registration': self.registration,
            'current_city': self.current_city.short if self.current_city else None,
        }

    @classmethod
    def from_dict(cls, data):
        models = get_models()
        model = next((m for m in models if m.name == data['model']), None)

        plane = cls(model, data['registration'])
        cities = get_cities()
        if data['current_city']:
            city_short = data['current_city']
            plane.current_city = next((c for c in cities if c.short == city_short), None)

        return plane
    
    def can_fly(self, distance: float) -> bool:
        return distance <= self.range

    def sell(self) -> float:
        sell_price = self.model.price * 0.7
        return sell_price


class Flight:
    FUELCOST_PER_KM = 0.08
    PILOT_SALARY_PER_MINUTE = 0.67 # make this dependent of flight duration
    
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
            'origin': self.origin.short,
            'destination': self.destination.short,
            'plane_registration': self.plane.registration,
            'passengers': self.passengers,
            'start': self.start.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data, planes):
        cities = get_cities()
        origin = next(c for c in cities if c.short == data['origin'])
        dest = next(c for c in cities if c.short == data['destination'])
        plane = next(p for p in planes if p.registration == data['plane_registration'])
        start = Instant.from_dict(data['start'])
        return cls(origin, dest, plane, start, data['passengers'])
    
    def calculate_revenue(self) -> float:
        if self.distance < 500:
            ticket_price = 0.25
        elif self.distance < 1000:
            ticket_price = 0.2
        else:
            ticket_price = 0.15
        return self.passengers * ticket_price * self.distance

    def calculate_variable_cost(self) -> float:
        return self.distance * self.FUELCOST_PER_KM # make this model dependent

    def calculate_fixed_cost(self) -> float:
        return self.plane.maintenance + self.plane.pilots*self.PILOT_SALARY_PER_MINUTE*self.duration

    def calculate_profit(self) -> float:
        return self.calculate_revenue() - self.calculate_variable_cost() - self.calculate_fixed_cost()


# ==================== GAME MANAGER ====================
GAME_WORLD = {
    "cities": load_cities(),
    "models": [PlaneModel("Dash 8 Q200", 39, 2000, 3, 50000, 200, 2)] + load_models()
}

def get_cities() -> List[City]:
    if GAME_WORLD is not None:
        return GAME_WORLD["cities"]
    GAME_WORLD["cities"] = load_cities()
    GAME_WORLD["models"] = [PlaneModel("Dash 8 Q200", 39, 2000, 3, 50000, 200)] + load_models()
    return GAME_WORLD["cities"]

def get_models() -> List[PlaneModel]:
    if GAME_WORLD is not None:
        return GAME_WORLD["models"]
    GAME_WORLD["cities"] = load_cities()
    GAME_WORLD["models"] = [PlaneModel("Dash 8 Q200", 39, 2000, 3, 50000, 200)] + load_models()
    return GAME_WORLD["models"]

class AirlineManager:
    def __init__(self):
        self.cities: List[City] = []
        self.planes: List[Plane] = []
        self.flights: List[Flight] = []
        self.hubs: List[Hub] = []
        self.demand: dict[str, dict[str, int]] = {}
        self.money: float = 50000000.0
        self.week: int = 1
        self.plane_counter: int = 1
        self.available_models: List[PlaneModel] = []
        self._initialize_game()
    
    def _initialize_game(self):
        self.cities = get_cities()
        self.update_demand()
        self.available_models = get_models()

        starter_plane = Plane(self.available_models[0], f"Starter")
        starter_plane.current_city = self.cities[0]
        
        self.planes.append(starter_plane)
        self.plane_counter += 1
        self.hubs = [Hub(starter_plane.current_city)] + [Hub(city) for city in self.cities[1:11]]

    def to_dict(self):
        return {
            'planes': [p.to_dict() for p in self.planes],
            'flights': [f.to_dict() for f in self.flights],
            'hubs': [h.to_dict() for h in self.hubs],
            'money': self.money,
            'week': self.week,
        }
    
    @classmethod
    def from_dict(cls, data):
        manager = cls.__new__(cls)
        manager.cities = get_cities()
        manager.available_models = get_models()
        manager.planes = [Plane.from_dict(p) for p in data['planes']]
        manager.flights = [Flight.from_dict(f, manager.planes) for f in data['flights']]
        manager.hubs = [Hub.from_dict(h) for h in data['hubs']]

        for plane in manager.planes:
            plane.flights = [f for f in manager.flights if f.plane.registration == plane.registration]
        
        manager.money = data['money']
        manager.week = data['week']
        manager.plane_counter = len(manager.planes)
        manager.demand = {}
        manager.update_demand()
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
    
    def get_hub_in_city(self, city: City) -> Optional[Hub]:
        for hub in self.hubs:
            if hub.city == city:
                return hub
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
    
    def sell_plane(self, registration: str) -> float:
        plane = self.find_plane(registration)
        if not plane:
            raise ValueError(f"Flugzeug mit Registrierung '{registration}' nicht gefunden")
        
        if any(f for f in self.flights if f.plane == plane):
            raise ValueError(f"Flugzeug '{registration}' hat noch geplante Flüge und kann nicht verkauft werden")
        
        sell_price = plane.sell()
        self.money += sell_price
        self.planes.remove(plane)
        
        return sell_price

    def create_flight(self, origin_name: str, dest_name: str, plane_reg: str, start: Instant, max_passengers: int) -> Flight:
        origin = self.find_city(origin_name)
        destination = self.find_city(dest_name)
        plane = self.find_plane(plane_reg)
        distance = origin.distance_to(destination)

        if not origin or not destination or not plane:
            raise ValueError("Stadt oder Flugzeug nicht gefunden")
        if max_passengers > plane.capacity:
            raise ValueError(f"Zu viele Passagiere! Max: {plane.capacity}")
        if not plane.can_fly(distance):
            raise ValueError(f"Flugzeug kann diese Distanz nicht fliegen")
        if self.get_hub_in_city(origin) is None:
            raise ValueError(f"Kein Hub in der Abflugstadt")
        if self.get_hub_in_city(destination) is None:
            raise ValueError(f"Kein Hub in der Ankunftsstadt")
        
        origin_hub = self.get_hub_in_city(origin)
        
        # Problem with boost due to no recalculation of older flights before building hub also make function for recalculating all flights when a week passes
        # also some problem with the "there will always be someone flying" part when there are too many flights on the route

        pot_passengers = get_potential_passenger_demand(get_route_demand(origin, destination, self.week), start.hour, start.minute, origin.timezone)* origin_hub.passenger_bonus
        currently_flewn_passengers_in_time = self.check_route_usage(origin.short, destination.short, start)
        currently_flewn_passengers = self.check_route_usage(origin.short, destination.short, None)
        available_demand = round((pot_passengers - currently_flewn_passengers_in_time) * 0.8) # 80% because always someone flys
        weekly_max = round(get_route_demand(origin, destination, self.week) - currently_flewn_passengers)
        passengers = min(max_passengers, available_demand, weekly_max)



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

    def check_route_usage(self, origin: str, destination: str, time: Instant) -> int:
        """Überprüft die Nutzung der Routen"""
        route_usage = 0
        for flight in self.flights:
            if flight.origin.short == origin and flight.destination.short == destination:
                if time is not None:
                    if flight.start.to_minutes() == time.to_minutes():
                        route_usage += flight.passengers
                else:
                    route_usage += flight.passengers

        return route_usage

    def update_demand(self):
        if self.demand != {}:
            self.demand.clear()
        for i in self.cities:
            self.demand[i.short] = {}
            for j in self.cities:
                self.demand[i.short][j.short] = get_route_demand(i, j, self.week)

    def flights_for_plane(self, plane):
        return [f for f in self.flights if f.plane == plane]

    def calculate_weekly_maintenance(self) -> float:
        total_weekly_maintenance = 0
        for plane in self.planes:
            total_weekly_maintenance += plane.maintenance
        return total_weekly_maintenance
    
    def calculate_weekly_hub_cost(self) -> float:
        hub_weekly_cost = 0
        for hub in self.hubs:
            hub_weekly_cost += hub.weekly_cost
        return hub_weekly_cost
    
    def recalculate_flights(self): #! TODO
        for flight in self.flights:
            self.create_flight(flight.origin.short, flight.destination.short, flight.plane.registration, flight.start, flight.passengers)
            self.flights.remove(flight)

    def advance_week(self) -> dict:
        print("Checkpint C")
        issues = self.check_flight_plan()
        if issues:
            raise ValueError("Flugplan ungültig!")

        total_revenue = 0
        total_cost = 0
        flight_count = len(self.flights)
        
        for flight in self.flights:
            total_revenue += flight.calculate_revenue()
            total_cost += flight.calculate_fixed_cost() + flight.calculate_variable_cost()
            flight.plane.current_city = flight.destination

        maintenance = self.calculate_weekly_maintenance()
        hub_weekly_cost = self.calculate_weekly_hub_cost()
        

        total_cost += maintenance
        total_cost += hub_weekly_cost
        total_profit = total_revenue - total_cost
        
        self.money += total_profit
        self.week += 1
        
        # Lösche Flüge

        for plane in self.planes:
            plane.flights.clear()

        self.update_demand()
        self.recalculate_flights()

        for plane in self.planes:
            if plane.flights:
                plane.current_city = plane.flights[-1].destination


        return {
            'week': self.week - 1,
            'flights': flight_count,
            'revenue': total_revenue,
            'cost': total_cost - maintenance,
            'maintenance': maintenance,
            'profit': total_profit,
            'new_balance': self.money
        }


def get_route_demand(origin: City, destination: City, week: int) -> int | None:
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

    random.seed(hash(origin.name + destination.name + str(week)))
    demand *= random.uniform(0.09, 0.11)

    return round(max(demand, 0))


def get_potential_passenger_demand(demand: int, hours: int, minutes: int, timezone: float) -> int:
    def distribution_for_time(t):
        if t > 23:
            t -= 24
        elif t < 0:
            t += 24
        a = 0.4
        d1 = 1.5
        d2 = 4
        d3 = 2
        b1 = math.exp(-((t - 7) ** 2) / (2 * d1 ** 2)) # Früh peak
        b2 = math.exp(-((t - 12) ** 2) / (2 * d2 ** 2)) # Mittag peak
        b3 = math.exp(-((t - 18) ** 2) / (2 * d3 ** 2)) # Abend peak
        return a/math.sqrt(math.pi)*(b1 + b2 + b3)+0.1
    total_minutes = hours * 60 + minutes
    exact_hours = total_minutes / 60
    potential_demand = demand * (distribution_for_time(exact_hours-timezone) + distribution_for_time((exact_hours - timezone - 1))) + 0.2
    return round(potential_demand)
