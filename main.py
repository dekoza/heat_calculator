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

from click.exceptions import FileError
from pony.orm.core import commit, select
from models import Material
from pony.orm import db_session
import numpy as np
import click

import csv
import pandas as pd
import random


class TooHighTempException(Exception):
    pass


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
    """
    Format danych przyjmowanych przez tę funkcję:
    [
        {
            "name": "Nazwa materiału",
            "max_temp": 1200,
            "price": 15.0,
            "coeff_200": 3.4,
            "coeff_400": 3.6,
            "coeff_600": 3.6,
            "coeff_800": 3.6,
            "coeff_1000": 3.4,
            "coeff_1200": None,
            "coeff_1400": None,
            "coeff_1600": None,
        },
        {...}

    ]

    """

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


def read_csv(file_name):
    """
    Musi zwrócić dane w formacie akceptowanym przez funkcję `update_database`.
    Nie musi zwracać listy, może zwracać iterator.
    """
    with open(file_name, "r") as f:
        reader = csv.DictReader(f, fieldnames=headers)
        next(reader)
        return [o for o in reader]


def read_excel(file_name):
    "xls / xlsx"
    data = pd.read_excel(file_name, names=headers)
    return [
        dict(zip(data.columns, r)) for r in data.where(pd.notnull(data), None).values
    ]


# CLICK interface
# https://click.palletsprojects.com/en/7.x/commands/


@click.group()
def cli():
    pass


@cli.command()
def example():
    """
    Tworzy przykładowy plik
    """
    create_example_input_file()
    print("Utworzono plik example.csv")


@cli.command()
@click.argument("file_name")
def import_file(
    file_name,
):
    """
    Importuje dane z pliku do bazy
    """

    # rozpoznanie formatu
    if file_name.endswith(".csv"):
        importer = read_csv
    elif file_name.endswith(".xlsx"):
        importer = read_excel
    else:
        raise FileError("Nieprawidłowy format pliku")

    data = importer(file_name)
    update_database(data)
    print("Program zakończył działanie.")


# TODO: Dołożyć tworzenie przykładowej konfiguracji ściany (np. wall-example ?)
@cli.command()
def example_wall_config():
    """
    Tworzy przykładowy plik zawierajacy konfiguracje
    """

    """wall_config = [
        # material name, thickness
        ("ISO 140-0.8", 0.065),
        ("ISO 125-0.5", 0.065),
        ("Microporous ISO 1200", 0.06),
    ]"""

    # TODO: do poprawy - niech tworzy plik z przykładową konfiguracją.

    accetable_thickness = np.arange(0.05, 0.5, 0.01).tolist()
    number_of_example_layers = 3
    example_wall_config = dict(
        zip(
            random.sample(wall_config_material, number_of_example_layers),
            random.sample(accetable_thickness, number_of_example_layers),
        )
    )
    print(example_wall_config)


@cli.command()
@click.option("--start-temp", default=1360)
@click.option("--end-temp", default=70)
def calc_temps(start_temp, end_temp):
    """
    Oblicza zmianę temperatur
    """
    TEMP_START = start_temp  # inner wall temp [C]
    TEMP_END = end_temp  # outer wall temp [C]
    Q = 750  # initial heat flux
    # Q = calculate_Q()

    read_wall_config = pd.read_excel("wall_config.xlsx")
    wall_config_material = read_wall_config["material"].tolist()
    wall_config_thickness = read_wall_config["thickness"].tolist()
    wall_config = dict(zip(wall_config_material, wall_config_thickness))

    # główna funkcja programu
    with db_session:
        query = Material.select(lambda m: m.name in wall_config_material)
        if set(wall_config_material) - set(m.name for m in query):
            raise ValueError("Nie wszystkie materiały znajdują się w bazie!")

        temp = TEMP_START
        for name, thickness in wall_config:
            material = Material.get(name=name)
            if temp > material.max_temp:
                raise TooHighTempException(temp, name)

            layer_coeff = (
                material.coeff_a * (temp ** 2)
                + material.coeff_b * temp
                + material.coeff_c
            )
            print(f"Temperatura na warstwie {name} jest rowna {temp}")
            temp = temp - ((thickness * Q) / layer_coeff)
    if temp > end_temp:
        print("Wszystko okej, obliczenia wykonane poprawnie")
    raise ValueError(f"Niepoprawnie przepriwadzone obliczenia temp koncowa {temp}")

    # TODO: wygenerowanie wykresu (np. podać nazwę pliku przez parametr)


@cli.command()
@click.argument("pdf_name")
def generate_plot(pdf_name):
    """
    Generuje wykres i zapisuje do pdf
    """
    plot = plt.plot(x, y)
    plt.savefig(f"{pdf_name}.pdf")


if __name__ == "__main__":
    cli()
