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
 - [ ] Save data for multiple users. 
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

 Okay so.
I have an app that works with flask. 
The game logic (classes etc) goes in main.py
This is imported by routes.py, that returns an app in a function that is later picked up by an vercel entry point. 
The thing is I want to change a bit how the game stores progress.
Currently I use Flask-Session with Redis for vercel. This is working great tbh! There are just two issues.
When I deploy the app locally (not vercel, usually for testing) every browser that accesses my page saves their information in a  session or smth like that. -> great!
When I access my vercel page there is like one big account that is stored. 

I would like to do the following if possible:
1. Keep redis.
2. Store the information locally and in vercel asociated with an account namae/id/email on redis, instead of browser depended
3. Somehow import all routes from the current game into another .py file where I manage the account and make paths like this domain/<name>/game/dashboard etc

if redis is not adequate for this I am willing to change to some other form of storing information that is compatible with vercel and is free (maybe supabase)
 