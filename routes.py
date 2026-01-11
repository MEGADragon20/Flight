import os, redis
from flask import Flask, render_template, session, redirect, url_for, request, app
from main import AirlineManager, Instant, Hub, get_potential_passenger_demand, get_route_demand
from flask_session import Session
from dotenv import load_dotenv

load_dotenv()

USE_REDIS = os.getenv("USE_REDIS")
REDIS_URL = os.getenv("REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

def create_app():
    print(repr(USE_REDIS))
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['SESSION_TYPE'] = 'redis' if USE_REDIS == '1' else 'filesystem'
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL) if USE_REDIS == '1' else None
    app.config['SESSION_PERMANENT'] = False
    Session(app)

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
        expected_profit -= manager.calculate_weekly_maintenance()
        expected_profit -= manager.calculate_weekly_hub_cost()
        
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

    @app.route('/shop/view/<model_name>', methods=['POST','GET'])
    def view_plane(model_name):
        manager = get_manager()
        model = manager.find_model(model_name)
        if not model:
            return render_template("shop.html", manager=manager, error="Flugzeugmodell nicht gefunden.")
        return render_template("buy_plane.html", manager=manager, model=model)

    @app.route('/shop/buy/<model_name>', methods=['POST'])
    def buy_plane(model_name):
        manager = get_manager()
        try:
            manager.buy_plane(model_name, request.form['registration'], manager.find_city(request.form['city']))
            save_manager(manager)
            return redirect(url_for('hangar'))
        except ValueError as e:
            return render_template("shop.html", manager=manager, error=str(e))

    @app.route('/hangar/sell/<registration>')
    def sell_plane(registration):
        manager = get_manager()
        try:
            manager.sell_plane(registration)
            save_manager(manager)
            return redirect(url_for('hangar'))
        except ValueError as e:
            return render_template("hangar.html", manager=manager, error=str(e))

    @app.route('/cities')
    def cities():
        manager = get_manager()
        cities_with_hubs = [hub.city.short for hub in manager.hubs]
        return render_template("cities.html", manager=manager, cities_with_hubs=cities_with_hubs)

    @app.route('/cities/view/<city_name>')
    def view_city(city_name):
        manager = get_manager()
        city = manager.find_city(city_name)
        hub = manager.get_hub_in_city(city)
        if not city:
            return render_template("cities.html", manager=manager, error="Stadt nicht gefunden.")
        return render_template("view_city.html", manager=manager, city=city, hub=hub)

    @app.route('/upgrade_hub/<city_short>', methods=['POST'])
    def upgrade_hub(city_short):
        manager = get_manager()
        hub = manager.get_hub_in_city(manager.find_city(city_short))
        if not hub:
            manager.hubs.append(Hub(manager.find_city(city_short)))
            save_manager(manager)
            return redirect(url_for('view_city', city_name=city_short))
        hub.upgrade()
        save_manager(manager)
        return redirect(url_for('view_city', city_name=city_short))

    @app.route('/routes/<origin>/<destination>')
    def view_route(origin, destination):
        manager = get_manager()
        origin_city = manager.find_city(origin)
        destination_city = manager.find_city(destination)
        passenger_availability = {}
        total_demand = get_route_demand(origin_city, destination_city, manager.week)
        for i in range(24):
            passenger_availability[i] = get_potential_passenger_demand(total_demand, i, 0, origin_city.timezone)
        distance = round(origin_city.distance_to(destination_city))
        return render_template("route.html", manager=manager, passenger_availability=passenger_availability, origin=origin_city, destination=destination_city, total=total_demand, distance=distance)

    @app.route('/calendar')
    @app.route('/calendar/<day>')
    #@app.route('/calendar/<day>/<error>')
    def calendar(day='M', error = None):
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

        cities_with_hubs = [hub.city.short for hub in manager.hubs]

        if error:
            return render_template("calendar.html", manager=manager, current_day=day, flights_by_day=flights_by_day, day_profit=day_profit, days=Instant.DAYS, cities_with_hubs=cities_with_hubs, error=error)
        return render_template("calendar.html", manager=manager, current_day=day, flights_by_day=flights_by_day, day_profit=day_profit, days=Instant.DAYS, cities_with_hubs=cities_with_hubs)

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
            max_passengers = int(request.form['passengers'])
            start = Instant(day, hour, minute)
            
            manager.create_flight(origin, destination, plane, start, max_passengers)
            save_manager(manager)
            
            return redirect(url_for('calendar', day=day))
        except Exception as e:
            print(e)
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
        print("Advancing week...")
        manager = get_manager()
        try:
            result = manager.advance_week()
            save_manager(manager)
            return render_template("week_result.html", result=result, manager=manager)
        except ValueError as e:
            print("Error advancing week:", e)
            return redirect(url_for('index'))

    @app.route('/reset', methods=['POST'])
    def reset():
        session.clear()
        return redirect(url_for('index'))
    
    # wiki!

    @app.route('/wiki')
    @app.route('/wiki/<article>')
    def wiki(article=None):
        manager = get_manager()
        print("Wiki article requested:", article)
        if article:
            try:
                return render_template(f"wiki/{article}.html", manager=manager)
            except:
                return render_template("wiki/main.html", manager=manager, error="Seite nicht gefunden.")
        return render_template("wiki/main.html", manager=manager)

    @app.route('/wiki/plane/<planename>')
    def wiki_plane(planename):
        try:
            return render_template(f"wiki/planes/{planename}.html")
        except:
            return render_template("wiki/main.html", error="Seite nicht gefunden.")
    # some important routes for static files and browsers and stuff
    
    @app.route('/favicon.ico')
    def favicon():
        print("Favicon requested")
        return redirect(url_for('static', filename='favicon.png'))
    
    @app.route("/static/<path:filename>")
    def static_files(filename):
        print("Serving static file:", filename)
        return app.send_static_file(filename)

    return app