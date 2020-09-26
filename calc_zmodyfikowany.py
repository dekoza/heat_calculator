# główny plik programu

# from numpy.matrixlib.defmatrix import mat
from models import Material
from pony.orm import select, db_session, commit
import numpy as np


class TooHighTempException(Exception):
    pass


def generate_data():
    iso140_08 = Material(
        name="ISO 140-0.8",
        max_temp=1400,
        coeff_400=0.27,
        coeff_800=0.31,
        coeff_1000=0.33,
        coeff_1200=0.36,
    )
    iso125_05 = Material(
        name="ISO 125-0.5",
        max_temp=1250,
        coeff_400=0.14,
        coeff_600=0.16,
        coeff_800=0.18,
        coeff_1000=0.2,
    )
    iso85_06 = Material(
        name="ISO 185-0.6", max_temp=850, coeff_400=0.14, coeff_600=0.16, coeff_800=0.19
    )
    microporus_1000 = Material(
        name="Microporous ISO 1000",
        max_temp=1000,
        coeff_200=0.022,
        coeff_400=0.025,
        coeff_600=0.035,
        coeff_800=0.044,
    )
    microporus_1200 = Material(
        name="Microporous ISO 1200",
        max_temp=1200,
        coeff_200=0.029,
        coeff_400=0.033,
        coeff_600=0.039,
        coeff_800=0.044,
    )
    materials = [iso140_08, iso125_05, iso85_06, microporus_1000, microporus_1200]

    for material in materials:
        x = []
        y = []
        for temp in range(200, 1601, 200):
            value = getattr(material, f"coeff_{temp}", None)
            if value is not None:
                x.append(temp)
                y.append(value)

        deg = 2
        k = np.polyfit(x, y, deg)
        print(k)
        curve = np.poly1d(k)

        print(f"Materiał {material.name} ma krzywą:\n{curve}")
        material.coeff_a = k[0]
        material.coeff_b = k[1]
        material.coeff_c = k[2]


def main():
    TEMP_START = 1360  # inner wall temp [C]
    TEMP_END = 70  # outer wall temp [C]
    Q = 750  # initial heat flux
    # Q = calculate_Q()

    wall_config = [
        # material name, thickness
        ("ISO 140-0.8", 0.065),
        ("ISO 125-0.5", 0.065),
        ("Microporous ISO 1200", 0.06),
    ]

    # główna funkcja programu
    with db_session:
        # 1. jeśli w bazie nie ma materiałów -> wczytaj i wygeneruj dane
        mat_testowy = select(m for m in Material).first()
        if mat_testowy is None:
            generate_data()
            commit()
        else:
            print("Dane już są w bazie!")

        temp = TEMP_START
        for name, thickness in wall_config:
            material = Material.get(name=name)
            if temp > material.max_temp:
                raise TooHighTempException(temp, name)
            # print("temp", temp)
            # print("a", material.coeff_a, "b", material.coeff_b, "c", material.coeff_c)
            layer_coeff = (
                material.coeff_a * (temp ** 2)
                + material.coeff_b * temp
                + material.coeff_c
            )
            print(f"Temperatura na warstwie {name} jest rowna {temp}")
            temp = temp - ((thickness * Q) / layer_coeff)

    if temp > TEMP_END:
        print(
            f"Mamy problem, temp końcowa: {round(temp, 2)}*C jest większa niż zakładana {TEMP_END}*C"
        )
    else:
        print(f"Wszystko dobrze, końcowa temperatura jest mniejsza niż 70*C.")


if __name__ == "__main__":
    # to się uruchomi przy odpaleniu programu z konsoli
    try:
        main()
    except TooHighTempException as e:
        print(f"Za wysoka temperatura dla materiału.")
