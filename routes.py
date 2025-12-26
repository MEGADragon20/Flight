import secrets
from flask import Flask, render_template, session, redirect, url_for, request, app
from main import AirlineManager, Instant
from flask_session import Session


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # or redis
app.config['SESSION_PERMANENT'] = False
Session(app)
app.secret_key = secrets.token_hex(16)

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
    expected_profit -= manager.calculate_maintenance()
    
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


@app.route('/cities')
def cities():
    manager = get_manager()
    return render_template("cities.html", manager=manager)

@app.route('/cities/view/<city_name>')
def view_city(city_name):
    manager = get_manager()
    city = manager.find_city(city_name)
    if not city:
        return render_template("cities.html", manager=manager, error="Stadt nicht gefunden.")
    return render_template("view_city.html", manager=manager, city=city)

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


