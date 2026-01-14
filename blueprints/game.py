from flask import Blueprint, json, render_template, g, redirect, url_for, request, app
import redis, os
from main import AirlineManager, Instant, Hub, get_potential_passenger_demand, get_route_demand
from dotenv import load_dotenv


def return_game_blueprint():
    r = redis.from_url(os.getenv("REDIS_URL"))

    game_bp = Blueprint('game', __name__)

    @game_bp.before_request
    def load_user():
        from flask import request, abort
        username = request.view_args.get("username") or "demo"
        if not username:
            abort(404)
        g.user_id = username

    def get_manager():
        user_id = g.user_id
        key = f"game:{user_id}"

        data = r.get(key)
        if data is None:
            manager = AirlineManager()
            save_manager(manager)
            return manager

        return AirlineManager.from_dict(json.loads(data))


    def save_manager(manager):
        user_id = g.user_id
        key = f"game:{user_id}"
        r.set(key, json.dumps(manager.to_dict()))


    @game_bp.route('/')
    def index(username):
        manager = get_manager()

        # Berechne erwarteten Gewinn
        expected_profit = sum(f.calculate_profit() for f in manager.flights)
        expected_profit -= manager.calculate_weekly_maintenance()
        expected_profit -= manager.calculate_weekly_hub_cost()
        
        issues = manager.check_flight_plan()

        return render_template("dashboard.html", manager=manager, expected_profit=expected_profit, issues=issues)

    @game_bp.route('/hangar')
    def hangar(username):
        manager = get_manager()
        return render_template("hangar.html", manager=manager)

    @game_bp.route('/shop')
    def shop(username):
        manager = get_manager()
        return render_template("shop.html", manager=manager)

    @game_bp.route('/shop/view/<model_name>', methods=['POST','GET'])
    def view_plane(model_name, username):
        manager = get_manager()
        model = manager.find_model(model_name)
        if not model:
            return render_template("shop.html", manager=manager, error="Flugzeugmodell nicht gefunden.")
        return render_template("buy_plane.html", manager=manager, model=model)

    @game_bp.route('/shop/buy/<model_name>', methods=['POST'])
    def buy_plane(model_name, username):
        manager = get_manager()
        try:
            manager.buy_plane(model_name, request.form['registration'], manager.find_city(request.form['city']))
            save_manager(manager)
            return redirect(url_for('game.hangar', username=username))
        except ValueError as e:
            return render_template("shop.html", manager=manager, error=str(e))

    @game_bp.route('/hangar/sell/<registration>')
    def sell_plane(registration, username):
        manager = get_manager()
        try:
            manager.sell_plane(registration)
            save_manager(manager)
            return redirect(url_for('game.hangar', username=username))
        except ValueError as e:
            return render_template("hangar.html", manager=manager, error=str(e))

    @game_bp.route('/cities')
    def cities(username):
        manager = get_manager()
        cities_with_hubs = [hub.city.short for hub in manager.hubs]
        return render_template("cities.html", manager=manager, cities_with_hubs=cities_with_hubs)

    @game_bp.route('/cities/view/<city_name>')
    def view_city(city_name, username):
        manager = get_manager()
        city = manager.find_city(city_name)
        hub = manager.get_hub_in_city(city)
        if not city:
            return render_template("cities.html", manager=manager, error="Stadt nicht gefunden.")
        return render_template("view_city.html", manager=manager, city=city, hub=hub)

    @game_bp.route('/upgrade_hub/<city_short>', methods=['POST'])
    def upgrade_hub(city_short, username):
        manager = get_manager()
        hub = manager.get_hub_in_city(manager.find_city(city_short))
        if not hub:
            manager.hubs.append(Hub(manager.find_city(city_short)))
            save_manager(manager)
            return redirect(url_for('game.view_city', username=username, city_name=city_short))
        hub.upgrade()
        save_manager(manager)
        return redirect(url_for('game.view_city', username=username, city_name=city_short))

    @game_bp.route('/routes/<origin>/<destination>')
    def view_route(origin, destination, username):
        manager = get_manager()
        origin_city = manager.find_city(origin)
        destination_city = manager.find_city(destination)
        passenger_availability = {}
        total_demand = get_route_demand(origin_city, destination_city, manager.week)
        for i in range(24):
            passenger_availability[i] = get_potential_passenger_demand(total_demand, i, 0, origin_city.timezone)
        distance = round(origin_city.distance_to(destination_city))
        return render_template("route.html", manager=manager, passenger_availability=passenger_availability, origin=origin_city, destination=destination_city, total=total_demand, distance=distance)

    @game_bp.route('/calendar')
    @game_bp.route('/calendar/<day>')
    def calendar(username, day='M', error = None):
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

    @game_bp.route('/calendar/add', methods=['POST'])
    def add_flight(username):
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
            
            return redirect(url_for('game.calendar', username=username, day=day))
        except Exception as e:
            print(e)
            return redirect(url_for('game.calendar', username=username, error=str(e)))

    @game_bp.route('/calendar/delete', methods=['POST'])
    def delete_flight(username):
        manager = get_manager()
        plane_reg = request.form['plane']
        start_str = request.form['start']
        day = request.form['day']
        
        manager.delete_flight(plane_reg, start_str)
        save_manager(manager)

        return redirect(url_for('game.calendar', username=username, day=day))

    @game_bp.route('/advance_week', methods=['POST'])
    def advance_week(username):
        print("Advancing week...")
        manager = get_manager()
        try:
            result = manager.advance_week()
            save_manager(manager)
            return render_template("week_result.html", result=result, manager=manager)
        except ValueError as e:
            print("Error advancing week:", e)
            return redirect(url_for('game.index', username=username))

    @game_bp.route('/reset', methods=['POST'])
    def reset(username):
        r.delete(f"game:{g.user_id}")
        return redirect(url_for('game.index', username=username))

    
    # wiki!

    @game_bp.route('/wiki')
    @game_bp.route('/wiki/<article>')
    def wiki(username, article=None):
        manager = get_manager()
        print("Wiki article requested:", article)
        if article:
            try:
                return render_template(f"wiki/{article}.html", manager=manager)
            except:
                return render_template("wiki/main.html", manager=manager, error="Seite nicht gefunden.")
        return render_template("wiki/main.html", manager=manager)

    @game_bp.route('/wiki/plane/<planename>')
    def wiki_plane(planename, username):
        try:
            return render_template(f"wiki/planes/{planename}.html")
        except:
            return render_template("wiki/main.html", error="Seite nicht gefunden.")
    # some important routes for static files and browsers and stuff
    
    @game_bp.route('/favicon.ico')
    def favicon(username):
        print("Favicon requested")
        return redirect(url_for('game.static', username = username, filename='favicon.png'))
    
    @game_bp.route("/static/<path:filename>")
    def static_files(filename, username):
        print("Serving static file:", filename)
        return app.send_static_file(filename)

    return game_bp