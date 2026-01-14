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
 - [ ] Balance // improve after hubs

#### Lounges & Terminals
 - [x] City interface
 - [x] Reform city class // add Hub class
 - [x] Costs for presence in Airports
 - [x] Add Lounges to potential demand
 - [x] Make Cities Tab searchable

#### Gameplay
 - [x] "Next week" -> no reset
 - [x] "Next week" -> recalculate flights
 - [ ] Play it until week 20

#### Player & Tutorial
 - [ ] Starting Plane, Hubs, Money etc, select name of Enterprise
 - [x] Tutorial or small Documentation `/wiki/get_started`
 - [ ] create accounts, email, username etc
 - [x] Save data for multiple users. 
 - [ ] Login
 - [ ] **P**v**P** (?)

#### Balances
 - [ ] Max_passengers always max
 - [ ] "Guess the price" & "perfect-price"
 - [ ] Adapt Prices to make it more realistic (plane costs etc)
 - [ ] Maintenance time depending on flight lenght, passenger count

####  Crew
 - [x] pilots needed
 - [ ] crew needed
 - [ ] floor personel

some problem w 2 planes having same name
 