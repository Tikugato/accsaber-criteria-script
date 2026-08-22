# accsaber-ranking-script

This project now includes a desktop app for running the ranking criteria checker.

## Run the app

First-time setup from the `Accsaber` repo root:
```
/usr/bin/python3 -m venv .checker-venv
source .checker-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy pandas
```

Each time before running the app, go to the Accsaber folder and then activate the virtual environment:
```
source .checker-venv/bin/activate
```

Then run the app from the `Accsaber` repo root with:
```
python accsaber_complexity_script/main.py
```

Or, if you are already inside the `accsaber_complexity_script` folder:
```
source ../.checker-venv/bin/activate
python main.py
```

## Using the app

1. Click `Choose Folder`
2. Select a Beat Saber map folder that contains `Info.dat`
3. Choose a difficulty from the dropdown
4. Choose `Standard`, `Tech`, or `True`
5. Click `Run Criteria Check`

The results panel will show:
- a summary
- any failed criteria
- the raw script output from the checker
