# poetry - manager virtualenv (opcjonalne)

# plan programu (wersja tekstowa / konsolowa):
#  1. Tworzenie szablonu pliku z danymi materiałów
#     a) Zapisz nagłówek tabeli i jedną przykładową linijkę
#     b) Jeśli w bazie są materiały - wypełnij nimi tabelę
#        (zamiast przykładowej linijki)
#  2. Aktualizacja danych w bazie na podstawie pliku z tabelką
#     a) Obsługa zarówno CSV jak i XLS/XLSX
#  3. Podczas aktualizacji - wyliczanie brakujących współczynników
#     a) pamiętamy, żeby nie wyliczać powyżej temp_max
#  4. Wczytanie danych dot. ściany z parametrów.
#  5. Wyeksportowanie wykresu

import csv
from typing import Dict, List
from models import Material
from pony.orm import db_session
import numpy as np
import click

headers = [
    "name",
    "max_temp",
    "price",
    "coeff_200",
    "coeff_400",
    "coeff_600",
    "coeff_800",
    "coeff_1000",
    "coeff_1200",
    "coeff_1400",
    "coeff_1600",
]


@db_session
def create_example_input_file():
    if Material.exists():
        data = (m.to_dict(only=headers) for m in Material.select())
    else:
        data = [
            {
                "name": "Microporous ISO 1200",
                "max_temp": 1200.0,
                "coeff_200": 0.029,
                "coeff_400": 0.033,
                "coeff_600": 0.039,
                "coeff_800": 0.044,
                "coeff_1000": None,
                "coeff_1200": None,
                "coeff_1400": None,
                "coeff_1600": None,
                "price": None,
            }
        ]
    with open("example.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


@db_session
def update_database(input_data):  # type: (List[Dict]) -> None
    for entry in input_data:
        name = entry["name"]
        # zabezpieczyć przed brakiem elementu
        db_obj = Material.get(name=name)
        if db_obj:
            db_obj.set(**entry)
        else:
            db_obj = Material(**entry)

        # tutaj możemy operować na db_obj, żeby wyliczyć współczynniki
        # kod napisany na jednym z poprzednich spotkań:
        x = []
        y = []
        missing_temps = []
        max_temp = db_obj.max_temp or 2000
        for temp in range(200, 1601, 200):
            value = getattr(db_obj, f"coeff_{temp}", None)
            if value is not None:
                x.append(temp)
                y.append(value)
            elif temp < max_temp:
                missing_temps.append(temp)
        deg = 2
        k = np.polyfit(x, y, deg)
        db_obj.coeff_a = k[0]
        db_obj.coeff_b = k[1]
        db_obj.coeff_c = k[2]
        curve = np.poly1d(k)

        # teraz wypadałoby policzyć współczynnik dla tych temperatur,
        # które są mniejsze niż max_temp (patrz linia 79 oraz 85)

        for temp in missing_temps:
            value = ..... # <- tutaj formułka wyliczająca
            setattr(db_obj, f"coeff_{temp}", value)
        # koniec :)


def read_csv():
    pass


def read_excel():
    "xls / xlsx"
    pass
