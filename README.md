# Flight
### This is an open-source flask-based vercel-supported airline siulation

## Content:
- main.py -> contains game classes etc
- routes -> routes for web-app
    - mode for local hosting
    - mode for vercel with redis
- app.py -> game instance (used by both local and vercel)
- start.py -> starts the game locally if venv exists, else crashes
- app/index.py -> entry point for vercel
- requirements.txt 
- planes:
    - contains, obviously, planes.
    - json format, check existing ones if you want to add own ones
    - ordered by manifacturer
- cities.csv -> city information, check existing ones

## Try it out!
The game is simple but fun. It's hosted (for free) as a vercel deployment using (free) redis from Upstash. 

Visit it [here](https://flight-snowy.vercel.app)

## Host it yourself!
The game is not very resource intensive and saves your session for you, so you can run it on your own device.

Simply clone the repo.

make sure you have python3 > 3.8 installed then run `python3 -m .venv venv` to create a virtual environment.

Activate the venv, on Linux/MacOS with `source .venv/bin/activate` and on Windows with `.\.venv\Scripts\activate`.

After that, install all dependencies running `pip install -r requirements.txt`.

then simply run `python3 start.py` and visit the game on <localhost:5000>!


## TODO's
#### Time & Demand
 - [x] hour-depending demand -> when are people willing to come to the airport
 - [x] UTC, cities have timezones(constant)
 - [x] Flights are filled depending on demand
 - [x] Flight rentablility (aprox 80% of pax) (needs to be tested)
 - [ ] Display pax transported in route

#### Lounges & Terminals
 - [x] City interface
 - [ ] Reform city class // add Hub class
 - [ ] Add Lounges to profitability

#### Player & Tutorial
 - [ ] Starting Plane, Hubs, Money etc, select name of Enterprise
 - [ ] Tutorial or small Documentation `/wiki/get_started`
 - [ ] create accounts, email, username etc
 - [ ] Save data for multiple users. 
 - [ ] **P**v**P** (?)