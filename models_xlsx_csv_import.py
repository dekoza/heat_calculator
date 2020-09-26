from datetime import date
from datetime import datetime
from pony.orm import *

db = Database()

db.bind(provider="sqlite", filename="heatcalc.sqlite", create_db=True)


class Material(db.Entity):
    name = Required(str, unique=True)
    coeff_a = Required(float, default=0)
    coeff_b = Required(float, default=0)
    coeff_c = Required(float, default=0)
    max_temp = Required(float)
    coeff_200 = Optional(float, default=None, nullable=True)
    coeff_400 = Optional(float, default=None, nullable=True)
    coeff_600 = Optional(float, default=None, nullable=True)
    coeff_800 = Optional(float, default=None, nullable=True)
    coeff_1000 = Optional(float, default=None, nullable=True)
    coeff_1200 = Optional(float, default=None, nullable=True)
    coeff_1400 = Optional(float, default=None, nullable=True)
    coeff_1600 = Optional(float, default=None, nullable=True)
    price = Optional(float, default=None, nullable=True)


db.generate_mapping(create_tables=True)

# ---------------------------------------------IMPORT DATA FROM XLSX TO CSV---------------------------------------------
import xlrd
import csv
import csv_to_sqlite


def csv_from_excel():
    wb = xlrd.open_workbook("Materials.xlsx")
    sh = wb.sheet_by_name("Materials")
    your_csv_file = open("Material.csv", "w")
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in range(sh.nrows):
        wr.writerow(sh.row_values(rownum))

    # your_csv_file.close()


# runs the csv_from_excel function:
csv_from_excel()

# ---------------------------------IMPORT A CSV FILE INTO A TABLE USING sqlite3 tool------------------------------------

filename = "Material.csv"
fields, rows = [], []

with open(filename, "r") as csvfile:
    csvreader = csv.reader(csvfile)
    fields = next(csvreader)

    for row in csvreader:
        rows.append(row)

    print(
        "Total no. of rows: %d" % (csvreader.line_num)
    )  # czyta ilosc danych wejsciowych


"""options = csv_to_sqlite.CsvOptions(typing_style="full", encoding="windows-1250")
input_files = ["Material.csv"] # pass in a list of CSV files
csv_to_sqlite.write_csv(input_files, "output.sqlite", options)



def read_file(Material):
    thefile = open('Material.csv', 'r')
    lines = []
    for line in thefile:
        lines.append(line)
    thefile.close()

    return lines
    print(lines)"""
