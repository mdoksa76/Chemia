# -*- coding: utf-8 -*-
"""
core/elements.py — podatkovni temelj kemijske ekstenzije.

Jedan izvor podataka o elementima za oba sloja:
  - PT sloj (pse/) crpi cijeli zapis (naziv, kategorija, konfiguracija, izotopi...)
  - MolViz sloj (molviz/mass.py) crpi atomske mase za M_r / M / m / masene udjele
  - renderi crpe CPK i kategorijske boje te VdW/kovalentne polumjere

Zapis elementa (Element namedtuple):
  z        atomski broj
  sym      simbol
  name     hrvatski naziv
  latin    latinski naziv
  mass     atomska masa kao string ('12.011' ili '(97)' za sintetske)
  category kategorija (alkali, alkaline, transition, post, metalloid,
           nonmetal, halogen, noble, lanthanide, actinide)
  period   perioda 1..7
  group    grupa 1..18 ili None (f-blok: lantanoidi/aktinoidi)
  config   elektronska konfiguracija (display string)
  shells   popis elektrona po ljusci [K, L, M, ...]
  state    agregatno stanje (kruto, kaplj, plin)
  eneg     elektronegativnost (Pauling) ili None
  radius   atomski polumjer u pm ili None
  oxid     oksidacijski brojevi (display string)
  isotopes popis [oznaka, udio, je_li_najzastupljeniji]
"""

from collections import namedtuple

Element = namedtuple(
    "Element",
    "z sym name latin mass category period group config shells state eneg radius oxid isotopes",
)

# ---------------------------------------------------------------------------
#  Podaci (118 elemenata). Red = jedan Element(...).
# ---------------------------------------------------------------------------
_RAW = [
    (1,  'H',  'Vodik',       'Hydrogen',      '1.008',  'nonmetal',   1, 1,  '1s¹',                     [1],              'plin',  2.20, 53,   '+1, -1',   [['¹H','99.98%',True],['²H','0.02%',False],['³H','tragovi',False]]),
    (2,  'He', 'Helij',       'Helium',        '4.003',  'noble',      1, 18, '1s²',                     [2],              'plin',  None, 31,   '0',        [['⁴He','99.99%',True],['³He','0.01%',False]]),
    (3,  'Li', 'Litij',       'Lithium',       '6.941',  'alkali',     2, 1,  '[He] 2s¹',                [2,1],            'kruto', 0.98, 167,  '+1',       [['⁶Li','7.5%',False],['⁷Li','92.5%',True]]),
    (4,  'Be', 'Berilij',     'Beryllium',     '9.012',  'alkaline',   2, 2,  '[He] 2s²',                [2,2],            'kruto', 1.57, 112,  '+2',       [['⁹Be','100%',True]]),
    (5,  'B',  'Bor',         'Boron',         '10.811', 'metalloid',  2, 13, '[He] 2s² 2p¹',            [2,3],            'kruto', 2.04, 87,   '+3',       [['¹⁰B','20%',False],['¹¹B','80%',True]]),
    (6,  'C',  'Ugljik',      'Carbon',        '12.011', 'nonmetal',   2, 14, '[He] 2s² 2p²',            [2,4],            'kruto', 2.55, 77,   '+4,+2,-4', [['¹²C','98.9%',True],['¹³C','1.1%',False],['¹⁴C','tragovi',False]]),
    (7,  'N',  'Dušik',       'Nitrogen',      '14.007', 'nonmetal',   2, 15, '[He] 2s² 2p³',            [2,5],            'plin',  3.04, 75,   '+5,+3,-3', [['¹⁴N','99.6%',True],['¹⁵N','0.4%',False]]),
    (8,  'O',  'Kisik',       'Oxygen',        '15.999', 'nonmetal',   2, 16, '[He] 2s² 2p⁴',            [2,6],            'plin',  3.44, 73,   '-2',       [['¹⁶O','99.8%',True],['¹⁷O','0.04%',False],['¹⁸O','0.2%',False]]),
    (9,  'F',  'Fluor',       'Fluorine',      '18.998', 'halogen',    2, 17, '[He] 2s² 2p⁵',            [2,7],            'plin',  3.98, 72,   '-1',       [['¹⁹F','100%',True]]),
    (10, 'Ne', 'Neon',        'Neon',          '20.180', 'noble',      2, 18, '[He] 2s² 2p⁶',            [2,8],            'plin',  None, 71,   '0',        [['²⁰Ne','90.5%',True],['²²Ne','9.3%',False]]),
    (11, 'Na', 'Natrij',      'Sodium',        '22.990', 'alkali',     3, 1,  '[Ne] 3s¹',                [2,8,1],          'kruto', 0.93, 190,  '+1',       [['²³Na','100%',True]]),
    (12, 'Mg', 'Magnezij',    'Magnesium',     '24.305', 'alkaline',   3, 2,  '[Ne] 3s²',                [2,8,2],          'kruto', 1.31, 160,  '+2',       [['²⁴Mg','79%',True],['²⁵Mg','10%',False],['²⁶Mg','11%',False]]),
    (13, 'Al', 'Aluminij',    'Aluminium',     '26.982', 'post',       3, 13, '[Ne] 3s² 3p¹',            [2,8,3],          'kruto', 1.61, 143,  '+3',       [['²⁷Al','100%',True]]),
    (14, 'Si', 'Silicij',     'Silicon',       '28.086', 'metalloid',  3, 14, '[Ne] 3s² 3p²',            [2,8,4],          'kruto', 1.90, 118,  '+4,-4',    [['²⁸Si','92.2%',True],['²⁹Si','4.7%',False],['³⁰Si','3.1%',False]]),
    (15, 'P',  'Fosfor',      'Phosphorus',    '30.974', 'nonmetal',   3, 15, '[Ne] 3s² 3p³',            [2,8,5],          'kruto', 2.19, 110,  '+5,+3,-3', [['³¹P','100%',True]]),
    (16, 'S',  'Sumpor',      'Sulfur',        '32.065', 'nonmetal',   3, 16, '[Ne] 3s² 3p⁴',            [2,8,6],          'kruto', 2.58, 103,  '+6,+4,-2', [['³²S','95%',True],['³³S','0.75%',False],['³⁴S','4.25%',False]]),
    (17, 'Cl', 'Klor',        'Chlorine',      '35.453', 'halogen',    3, 17, '[Ne] 3s² 3p⁵',            [2,8,7],          'plin',  3.16, 99,   '+7,-1',    [['³⁵Cl','75.8%',True],['³⁷Cl','24.2%',False]]),
    (18, 'Ar', 'Argon',       'Argon',         '39.948', 'noble',      3, 18, '[Ne] 3s² 3p⁶',            [2,8,8],          'plin',  None, 98,   '0',        [['⁴⁰Ar','99.6%',True],['³⁶Ar','0.3%',False]]),
    (19, 'K',  'Kalij',       'Potassium',     '39.098', 'alkali',     4, 1,  '[Ar] 4s¹',                [2,8,8,1],        'kruto', 0.82, 243,  '+1',       [['³⁹K','93.3%',True],['⁴¹K','6.7%',False]]),
    (20, 'Ca', 'Kalcij',      'Calcium',       '40.078', 'alkaline',   4, 2,  '[Ar] 4s²',                [2,8,8,2],        'kruto', 1.00, 194,  '+2',       [['⁴⁰Ca','97%',True],['⁴⁴Ca','2.1%',False]]),
    (21, 'Sc', 'Skandij',     'Scandium',      '44.956', 'transition', 4, 3,  '[Ar] 3d¹ 4s²',            [2,8,9,2],        'kruto', 1.36, 184,  '+3',       [['⁴⁵Sc','100%',True]]),
    (22, 'Ti', 'Titanij',     'Titanium',      '47.867', 'transition', 4, 4,  '[Ar] 3d² 4s²',            [2,8,10,2],       'kruto', 1.54, 176,  '+4,+3',    [['⁴⁸Ti','73.7%',True],['⁴⁶Ti','8%',False]]),
    (23, 'V',  'Vanadij',     'Vanadium',      '50.942', 'transition', 4, 5,  '[Ar] 3d³ 4s²',            [2,8,11,2],       'kruto', 1.63, 171,  '+5,+4,+3', [['⁵¹V','99.75%',True],['⁵⁰V','0.25%',False]]),
    (24, 'Cr', 'Krom',        'Chromium',      '51.996', 'transition', 4, 6,  '[Ar] 3d⁵ 4s¹',            [2,8,13,1],       'kruto', 1.66, 166,  '+6,+3,+2', [['⁵²Cr','83.8%',True],['⁵³Cr','9.5%',False]]),
    (25, 'Mn', 'Mangan',      'Manganese',     '54.938', 'transition', 4, 7,  '[Ar] 3d⁵ 4s²',            [2,8,13,2],       'kruto', 1.55, 161,  '+7,+4,+2', [['⁵⁵Mn','100%',True]]),
    (26, 'Fe', 'Željezo',     'Iron',          '55.845', 'transition', 4, 8,  '[Ar] 3d⁶ 4s²',            [2,8,14,2],       'kruto', 1.83, 156,  '+3,+2',    [['⁵⁴Fe','5.8%',False],['⁵⁶Fe','91.7%',True],['⁵⁷Fe','2.2%',False],['⁵⁸Fe','0.3%',False]]),
    (27, 'Co', 'Kobalt',      'Cobalt',        '58.933', 'transition', 4, 9,  '[Ar] 3d⁷ 4s²',            [2,8,15,2],       'kruto', 1.88, 152,  '+3,+2',    [['⁵⁹Co','100%',True]]),
    (28, 'Ni', 'Nikal',       'Nickel',        '58.693', 'transition', 4, 10, '[Ar] 3d⁸ 4s²',            [2,8,16,2],       'kruto', 1.91, 149,  '+2,+3',    [['⁵⁸Ni','68.1%',True],['⁶⁰Ni','26.2%',False]]),
    (29, 'Cu', 'Bakar',       'Copper',        '63.546', 'transition', 4, 11, '[Ar] 3d¹⁰ 4s¹',           [2,8,18,1],       'kruto', 1.90, 145,  '+2,+1',    [['⁶³Cu','69.2%',True],['⁶⁵Cu','30.8%',False]]),
    (30, 'Zn', 'Cink',        'Zinc',          '65.380', 'transition', 4, 12, '[Ar] 3d¹⁰ 4s²',           [2,8,18,2],       'kruto', 1.65, 142,  '+2',       [['⁶⁴Zn','48.6%',True],['⁶⁶Zn','27.9%',False]]),
    (31, 'Ga', 'Galij',       'Gallium',       '69.723', 'post',       4, 13, '[Ar] 3d¹⁰ 4s² 4p¹',       [2,8,18,3],       'kruto', 1.81, 136,  '+3',       [['⁶⁹Ga','60.1%',True],['⁷¹Ga','39.9%',False]]),
    (32, 'Ge', 'Germanij',    'Germanium',     '72.640', 'metalloid',  4, 14, '[Ar] 3d¹⁰ 4s² 4p²',       [2,8,18,4],       'kruto', 2.01, 125,  '+4,+2',    [['⁷⁴Ge','36.7%',True],['⁷²Ge','27.4%',False]]),
    (33, 'As', 'Arsen',       'Arsenic',       '74.922', 'metalloid',  4, 15, '[Ar] 3d¹⁰ 4s² 4p³',       [2,8,18,5],       'kruto', 2.18, 114,  '+5,+3,-3', [['⁷⁵As','100%',True]]),
    (34, 'Se', 'Selenij',     'Selenium',      '78.960', 'nonmetal',   4, 16, '[Ar] 3d¹⁰ 4s² 4p⁴',       [2,8,18,6],       'kruto', 2.55, 103,  '+6,-2',    [['⁸⁰Se','49.8%',True],['⁷⁸Se','23.8%',False]]),
    (35, 'Br', 'Brom',        'Bromine',       '79.904', 'halogen',    4, 17, '[Ar] 3d¹⁰ 4s² 4p⁵',       [2,8,18,7],       'kaplj', 2.96, 114,  '+5,-1',    [['⁷⁹Br','50.7%',True],['⁸¹Br','49.3%',False]]),
    (36, 'Kr', 'Kripton',     'Krypton',       '83.798', 'noble',      4, 18, '[Ar] 3d¹⁰ 4s² 4p⁶',       [2,8,18,8],       'plin',  None, 112,  '0',        [['⁸⁴Kr','57%',True],['⁸⁶Kr','17.3%',False]]),
    (37, 'Rb', 'Rubidij',     'Rubidium',      '85.468', 'alkali',     5, 1,  '[Kr] 5s¹',                [2,8,18,8,1],     'kruto', 0.82, 265,  '+1',       [['⁸⁵Rb','72.2%',True],['⁸⁷Rb','27.8%',False]]),
    (38, 'Sr', 'Stroncij',    'Strontium',     '87.620', 'alkaline',   5, 2,  '[Kr] 5s²',                [2,8,18,8,2],     'kruto', 0.95, 219,  '+2',       [['⁸⁸Sr','82.6%',True],['⁸⁶Sr','9.9%',False]]),
    (39, 'Y',  'Itrij',       'Yttrium',       '88.906', 'transition', 5, 3,  '[Kr] 4d¹ 5s²',            [2,8,18,9,2],     'kruto', 1.22, 212,  '+3',       [['⁸⁹Y','100%',True]]),
    (40, 'Zr', 'Cirkonij',    'Zirconium',     '91.224', 'transition', 5, 4,  '[Kr] 4d² 5s²',            [2,8,18,10,2],    'kruto', 1.33, 206,  '+4',       [['⁹⁰Zr','51.5%',True],['⁹²Zr','17.2%',False]]),
    (41, 'Nb', 'Niobij',      'Niobium',       '92.906', 'transition', 5, 5,  '[Kr] 4d⁴ 5s¹',            [2,8,18,12,1],    'kruto', 1.60, 198,  '+5',       [['⁹³Nb','100%',True]]),
    (42, 'Mo', 'Molibden',    'Molybdenum',    '95.960', 'transition', 5, 6,  '[Kr] 4d⁵ 5s¹',            [2,8,18,13,1],    'kruto', 2.16, 190,  '+6,+4',    [['⁹⁸Mo','24.1%',True],['⁹⁶Mo','16.7%',False]]),
    (43, 'Tc', 'Tehnecij',    'Technetium',    '(97)',   'transition', 5, 7,  '[Kr] 4d⁵ 5s²',            [2,8,18,13,2],    'kruto', 1.90, 183,  '+7,+4',    [['⁹⁸Tc','—',True]]),
    (44, 'Ru', 'Rutenij',     'Ruthenium',     '101.07', 'transition', 5, 8,  '[Kr] 4d⁷ 5s¹',            [2,8,18,15,1],    'kruto', 2.20, 178,  '+4,+3',    [['¹⁰²Ru','31.6%',True],['¹⁰⁴Ru','18.6%',False]]),
    (45, 'Rh', 'Rodij',       'Rhodium',       '102.91', 'transition', 5, 9,  '[Kr] 4d⁸ 5s¹',            [2,8,18,16,1],    'kruto', 2.28, 173,  '+3',       [['¹⁰³Rh','100%',True]]),
    (46, 'Pd', 'Paladij',     'Palladium',     '106.42', 'transition', 5, 10, '[Kr] 4d¹⁰',               [2,8,18,18],      'kruto', 2.20, 169,  '+4,+2',    [['¹⁰⁸Pd','26.5%',True],['¹⁰⁶Pd','27.3%',False]]),
    (47, 'Ag', 'Srebro',      'Silver',        '107.87', 'transition', 5, 11, '[Kr] 4d¹⁰ 5s¹',           [2,8,18,18,1],    'kruto', 1.93, 165,  '+1',       [['¹⁰⁷Ag','51.8%',True],['¹⁰⁹Ag','48.2%',False]]),
    (48, 'Cd', 'Kadmij',      'Cadmium',       '112.41', 'transition', 5, 12, '[Kr] 4d¹⁰ 5s²',           [2,8,18,18,2],    'kruto', 1.69, 161,  '+2',       [['¹¹⁴Cd','28.7%',True],['¹¹²Cd','24.1%',False]]),
    (49, 'In', 'Indij',       'Indium',        '114.82', 'post',       5, 13, '[Kr] 4d¹⁰ 5s² 5p¹',       [2,8,18,18,3],    'kruto', 1.78, 156,  '+3',       [['¹¹⁵In','95.7%',True],['¹¹³In','4.3%',False]]),
    (50, 'Sn', 'Kositar',     'Tin',           '118.71', 'post',       5, 14, '[Kr] 4d¹⁰ 5s² 5p²',       [2,8,18,18,4],    'kruto', 1.96, 145,  '+4,+2',    [['¹²⁰Sn','32.6%',True],['¹¹⁸Sn','24.2%',False]]),
    (51, 'Sb', 'Antimon',     'Antimony',      '121.76', 'metalloid',  5, 15, '[Kr] 4d¹⁰ 5s² 5p³',       [2,8,18,18,5],    'kruto', 2.05, 133,  '+5,+3,-3', [['¹²¹Sb','57.2%',True],['¹²³Sb','42.8%',False]]),
    (52, 'Te', 'Telur',       'Tellurium',     '127.60', 'metalloid',  5, 16, '[Kr] 4d¹⁰ 5s² 5p⁴',       [2,8,18,18,6],    'kruto', 2.10, 123,  '+6,-2',    [['¹³⁰Te','34.1%',True],['¹²⁸Te','31.7%',False]]),
    (53, 'I',  'Jod',         'Iodine',        '126.90', 'halogen',    5, 17, '[Kr] 4d¹⁰ 5s² 5p⁵',       [2,8,18,18,7],    'kruto', 2.66, 133,  '+7,-1',    [['¹²⁷I','100%',True]]),
    (54, 'Xe', 'Ksenon',      'Xenon',         '131.29', 'noble',      5, 18, '[Kr] 4d¹⁰ 5s² 5p⁶',       [2,8,18,18,8],    'plin',  None, 131,  '0',        [['¹³²Xe','26.9%',True],['¹²⁹Xe','26.4%',False]]),
    (55, 'Cs', 'Cezij',       'Caesium',       '132.91', 'alkali',     6, 1,  '[Xe] 6s¹',                [2,8,18,18,8,1],  'kruto', 0.79, 298,  '+1',       [['¹³³Cs','100%',True]]),
    (56, 'Ba', 'Barij',       'Barium',        '137.33', 'alkaline',   6, 2,  '[Xe] 6s²',                [2,8,18,18,8,2],  'kruto', 0.89, 253,  '+2',       [['¹³⁸Ba','71.7%',True],['¹³⁷Ba','11.2%',False]]),
    (57, 'La', 'Lantan',      'Lanthanum',     '138.91', 'lanthanide', 6, 3,  '[Xe] 5d¹ 6s²',            [2,8,18,18,9,2],  'kruto', 1.10, 195,  '+3',       [['¹³⁹La','99.9%',True]]),
    (58, 'Ce', 'Cerij',       'Cerium',        '140.12', 'lanthanide', 6, None,'[Xe] 4f¹ 5d¹ 6s²',       [2,8,18,19,9,2],  'kruto', 1.12, 185,  '+4,+3',    [['¹⁴⁰Ce','88.5%',True]]),
    (59, 'Pr', 'Prazeodim',   'Praseodymium',  '140.91', 'lanthanide', 6, None,'[Xe] 4f³ 6s²',           [2,8,18,21,8,2],  'kruto', 1.13, 185,  '+3',       [['¹⁴¹Pr','100%',True]]),
    (60, 'Nd', 'Neodim',      'Neodymium',     '144.24', 'lanthanide', 6, None,'[Xe] 4f⁴ 6s²',           [2,8,18,22,8,2],  'kruto', 1.14, 185,  '+3',       [['¹⁴²Nd','27.2%',True],['¹⁴⁴Nd','23.8%',False]]),
    (61, 'Pm', 'Prometij',    'Promethium',    '(145)',  'lanthanide', 6, None,'[Xe] 4f⁵ 6s²',           [2,8,18,23,8,2],  'kruto', None, 185,  '+3',       [['¹⁴⁵Pm','—',True]]),
    (62, 'Sm', 'Samarij',     'Samarium',      '150.36', 'lanthanide', 6, None,'[Xe] 4f⁶ 6s²',           [2,8,18,24,8,2],  'kruto', 1.17, 185,  '+3,+2',    [['¹⁵²Sm','26.7%',True],['¹⁵⁴Sm','22.7%',False]]),
    (63, 'Eu', 'Europij',     'Europium',      '151.96', 'lanthanide', 6, None,'[Xe] 4f⁷ 6s²',           [2,8,18,25,8,2],  'kruto', None, 185,  '+3,+2',    [['¹⁵³Eu','52.2%',True],['¹⁵¹Eu','47.8%',False]]),
    (64, 'Gd', 'Gadolinij',   'Gadolinium',    '157.25', 'lanthanide', 6, None,'[Xe] 4f⁷ 5d¹ 6s²',       [2,8,18,25,9,2],  'kruto', 1.20, 180,  '+3',       [['¹⁵⁸Gd','24.8%',True],['¹⁶⁰Gd','21.9%',False]]),
    (65, 'Tb', 'Terbij',      'Terbium',       '158.93', 'lanthanide', 6, None,'[Xe] 4f⁹ 6s²',           [2,8,18,27,8,2],  'kruto', None, 175,  '+3',       [['¹⁵⁹Tb','100%',True]]),
    (66, 'Dy', 'Disprozij',   'Dysprosium',    '162.50', 'lanthanide', 6, None,'[Xe] 4f¹⁰ 6s²',          [2,8,18,28,8,2],  'kruto', 1.22, 175,  '+3',       [['¹⁶⁴Dy','28.2%',True],['¹⁶²Dy','25.5%',False]]),
    (67, 'Ho', 'Holmij',      'Holmium',       '164.93', 'lanthanide', 6, None,'[Xe] 4f¹¹ 6s²',          [2,8,18,29,8,2],  'kruto', 1.23, 175,  '+3',       [['¹⁶⁵Ho','100%',True]]),
    (68, 'Er', 'Erbij',       'Erbium',        '167.26', 'lanthanide', 6, None,'[Xe] 4f¹² 6s²',          [2,8,18,30,8,2],  'kruto', 1.24, 175,  '+3',       [['¹⁶⁶Er','33.5%',True],['¹⁶⁸Er','27%',False]]),
    (69, 'Tm', 'Tulij',       'Thulium',       '168.93', 'lanthanide', 6, None,'[Xe] 4f¹³ 6s²',          [2,8,18,31,8,2],  'kruto', 1.25, 175,  '+3',       [['¹⁶⁹Tm','100%',True]]),
    (70, 'Yb', 'Iterbij',     'Ytterbium',     '173.04', 'lanthanide', 6, None,'[Xe] 4f¹⁴ 6s²',          [2,8,18,32,8,2],  'kruto', None, 175,  '+3,+2',    [['¹⁷⁴Yb','31.8%',True],['¹⁷²Yb','21.9%',False]]),
    (71, 'Lu', 'Lutecij',     'Lutetium',      '174.97', 'lanthanide', 6, None,'[Xe] 4f¹⁴ 5d¹ 6s²',      [2,8,18,32,9,2],  'kruto', 1.27, 175,  '+3',       [['¹⁷⁵Lu','97.4%',True],['¹⁷⁶Lu','2.6%',False]]),
    (72, 'Hf', 'Hafnij',      'Hafnium',       '178.49', 'transition', 6, 4,  '[Xe] 4f¹⁴ 5d² 6s²',       [2,8,18,32,10,2], 'kruto', 1.30, 167,  '+4',       [['¹⁸⁰Hf','35.1%',True],['¹⁷⁸Hf','27.3%',False]]),
    (73, 'Ta', 'Tantal',      'Tantalum',      '180.95', 'transition', 6, 5,  '[Xe] 4f¹⁴ 5d³ 6s²',       [2,8,18,32,11,2], 'kruto', 1.50, 149,  '+5',       [['¹⁸¹Ta','99.99%',True]]),
    (74, 'W',  'Volfram',     'Tungsten',      '183.84', 'transition', 6, 6,  '[Xe] 4f¹⁴ 5d⁴ 6s²',       [2,8,18,32,12,2], 'kruto', 2.36, 141,  '+6,+4',    [['¹⁸⁴W','30.6%',True],['¹⁸⁶W','28.4%',False]]),
    (75, 'Re', 'Renij',       'Rhenium',       '186.21', 'transition', 6, 7,  '[Xe] 4f¹⁴ 5d⁵ 6s²',       [2,8,18,32,13,2], 'kruto', 1.90, 137,  '+7,+4',    [['¹⁸⁷Re','62.6%',True],['¹⁸⁵Re','37.4%',False]]),
    (76, 'Os', 'Osmij',       'Osmium',        '190.23', 'transition', 6, 8,  '[Xe] 4f¹⁴ 5d⁶ 6s²',       [2,8,18,32,14,2], 'kruto', 2.20, 135,  '+4,+3',    [['¹⁹²Os','41%',True],['¹⁹⁰Os','26.4%',False]]),
    (77, 'Ir', 'Iridij',      'Iridium',       '192.22', 'transition', 6, 9,  '[Xe] 4f¹⁴ 5d⁷ 6s²',       [2,8,18,32,15,2], 'kruto', 2.20, 136,  '+4,+3',    [['¹⁹³Ir','62.7%',True],['¹⁹¹Ir','37.3%',False]]),
    (78, 'Pt', 'Platina',     'Platinum',      '195.08', 'transition', 6, 10, '[Xe] 4f¹⁴ 5d⁹ 6s¹',       [2,8,18,32,17,1], 'kruto', 2.28, 138,  '+4,+2',    [['¹⁹⁵Pt','33.8%',True],['¹⁹⁴Pt','32.9%',False]]),
    (79, 'Au', 'Zlato',       'Gold',          '196.97', 'transition', 6, 11, '[Xe] 4f¹⁴ 5d¹⁰ 6s¹',      [2,8,18,32,18,1], 'kruto', 2.54, 144,  '+3,+1',    [['¹⁹⁷Au','100%',True]]),
    (80, 'Hg', 'Živa',        'Mercury',       '200.59', 'transition', 6, 12, '[Xe] 4f¹⁴ 5d¹⁰ 6s²',      [2,8,18,32,18,2], 'kaplj', 2.00, 160,  '+2,+1',    [['²⁰²Hg','29.7%',True],['²⁰⁰Hg','23.1%',False]]),
    (81, 'Tl', 'Talij',       'Thallium',      '204.38', 'post',       6, 13, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p¹',  [2,8,18,32,18,3], 'kruto', 1.62, 170,  '+3,+1',    [['²⁰⁵Tl','70.5%',True],['²⁰³Tl','29.5%',False]]),
    (82, 'Pb', 'Olovo',       'Lead',          '207.20', 'post',       6, 14, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p²',  [2,8,18,32,18,4], 'kruto', 2.33, 175,  '+4,+2',    [['²⁰⁸Pb','52.4%',True],['²⁰⁶Pb','24.1%',False]]),
    (83, 'Bi', 'Bizmut',      'Bismuth',       '208.98', 'post',       6, 15, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p³',  [2,8,18,32,18,5], 'kruto', 2.02, 156,  '+5,+3',    [['²⁰⁹Bi','100%',True]]),
    (84, 'Po', 'Polonij',     'Polonium',      '(209)',  'metalloid',  6, 16, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁴',  [2,8,18,32,18,6], 'kruto', 2.00, 167,  '+4,+2',    [['²¹⁰Po','—',True]]),
    (85, 'At', 'Astat',       'Astatine',      '(210)',  'halogen',    6, 17, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁵',  [2,8,18,32,18,7], 'kruto', 2.20, None, '+7,-1',    [['²¹⁰At','—',True]]),
    (86, 'Rn', 'Radon',       'Radon',         '(222)',  'noble',      6, 18, '[Xe] 4f¹⁴ 5d¹⁰ 6s² 6p⁶',  [2,8,18,32,18,8], 'plin',  None, None, '0',        [['²²²Rn','—',True]]),
    (87, 'Fr', 'Francij',     'Francium',      '(223)',  'alkali',     7, 1,  '[Rn] 7s¹',                [2,8,18,32,18,8,1],   'kruto', 0.70, None, '+1',    [['²²³Fr','—',True]]),
    (88, 'Ra', 'Radij',       'Radium',        '(226)',  'alkaline',   7, 2,  '[Rn] 7s²',                [2,8,18,32,18,8,2],   'kruto', 0.90, None, '+2',    [['²²⁶Ra','—',True]]),
    (89, 'Ac', 'Aktinij',     'Actinium',      '(227)',  'actinide',   7, 3,  '[Rn] 6d¹ 7s²',            [2,8,18,32,18,9,2],   'kruto', 1.10, 195,  '+3',    [['²²⁷Ac','—',True]]),
    (90, 'Th', 'Torij',       'Thorium',       '232.04', 'actinide',   7, None,'[Rn] 6d² 7s²',           [2,8,18,32,18,10,2],  'kruto', 1.30, 179,  '+4',    [['²³²Th','100%',True]]),
    (91, 'Pa', 'Protaktinij', 'Protactinium',  '231.04', 'actinide',   7, None,'[Rn] 5f² 6d¹ 7s²',       [2,8,18,32,20,9,2],   'kruto', 1.50, 163,  '+5,+4', [['²³¹Pa','100%',True]]),
    (92, 'U',  'Uran',        'Uranium',       '238.03', 'actinide',   7, None,'[Rn] 5f³ 6d¹ 7s²',       [2,8,18,32,21,9,2],   'kruto', 1.38, 156,  '+6,+4,+3', [['²³⁸U','99.27%',True],['²³⁵U','0.72%',False],['²³⁴U','0.006%',False]]),
    (93, 'Np', 'Neptunij',    'Neptunium',     '(237)',  'actinide',   7, None,'[Rn] 5f⁴ 6d¹ 7s²',       [2,8,18,32,22,9,2],   'kruto', 1.36, None, '+5,+4', [['²³⁷Np','—',True]]),
    (94, 'Pu', 'Plutonij',    'Plutonium',     '(244)',  'actinide',   7, None,'[Rn] 5f⁶ 7s²',           [2,8,18,32,24,8,2],   'kruto', 1.28, None, '+4,+3', [['²⁴⁴Pu','—',True]]),
    (95, 'Am', 'Americij',    'Americium',     '(243)',  'actinide',   7, None,'[Rn] 5f⁷ 7s²',           [2,8,18,32,25,8,2],   'kruto', 1.30, None, '+3',    [['²⁴³Am','—',True]]),
    (96, 'Cm', 'Kurij',       'Curium',        '(247)',  'actinide',   7, None,'[Rn] 5f⁷ 6d¹ 7s²',       [2,8,18,32,25,9,2],   'kruto', 1.30, None, '+3',    [['²⁴⁷Cm','—',True]]),
    (97, 'Bk', 'Berkelij',    'Berkelium',     '(247)',  'actinide',   7, None,'[Rn] 5f⁹ 7s²',           [2,8,18,32,27,8,2],   'kruto', 1.30, None, '+3',    [['²⁴⁷Bk','—',True]]),
    (98, 'Cf', 'Kalifornij',  'Californium',   '(251)',  'actinide',   7, None,'[Rn] 5f¹⁰ 7s²',          [2,8,18,32,28,8,2],   'kruto', 1.30, None, '+3',    [['²⁵¹Cf','—',True]]),
    (99, 'Es', 'Ajnštajnij',  'Einsteinium',   '(252)',  'actinide',   7, None,'[Rn] 5f¹¹ 7s²',          [2,8,18,32,29,8,2],   'kruto', 1.30, None, '+3',    [['²⁵²Es','—',True]]),
    (100,'Fm', 'Fermij',      'Fermium',       '(257)',  'actinide',   7, None,'[Rn] 5f¹² 7s²',          [2,8,18,32,30,8,2],   'kruto', 1.30, None, '+3',    [['²⁵⁷Fm','—',True]]),
    (101,'Md', 'Mendeljevij', 'Mendelevium',   '(258)',  'actinide',   7, None,'[Rn] 5f¹³ 7s²',          [2,8,18,32,31,8,2],   'kruto', 1.30, None, '+3',    [['²⁵⁸Md','—',True]]),
    (102,'No', 'Nobelij',     'Nobelium',      '(259)',  'actinide',   7, None,'[Rn] 5f¹⁴ 7s²',          [2,8,18,32,32,8,2],   'kruto', 1.30, None, '+2,+3', [['²⁵⁹No','—',True]]),
    (103,'Lr', 'Lorencij',    'Lawrencium',    '(262)',  'actinide',   7, None,'[Rn] 5f¹⁴ 7s² 7p¹',      [2,8,18,32,32,8,3],   'kruto', None, None, '+3',    [['²⁶²Lr','—',True]]),
    (104,'Rf', 'Raderfordij', 'Rutherfordium', '(265)',  'transition', 7, 4,  '[Rn] 5f¹⁴ 6d² 7s²',       [2,8,18,32,32,10,2],  'kruto', None, None, '+4',    [['²⁶⁵Rf','—',True]]),
    (105,'Db', 'Dubnij',      'Dubnium',       '(268)',  'transition', 7, 5,  '[Rn] 5f¹⁴ 6d³ 7s²',       [2,8,18,32,32,11,2],  'kruto', None, None, '+5',    [['²⁶⁸Db','—',True]]),
    (106,'Sg', 'Siborgij',    'Seaborgium',    '(271)',  'transition', 7, 6,  '[Rn] 5f¹⁴ 6d⁴ 7s²',       [2,8,18,32,32,12,2],  'kruto', None, None, '+6',    [['²⁶⁹Sg','—',True]]),
    (107,'Bh', 'Borij',       'Bohrium',       '(270)',  'transition', 7, 7,  '[Rn] 5f¹⁴ 6d⁵ 7s²',       [2,8,18,32,32,13,2],  'kruto', None, None, '+7',    [['²⁷⁰Bh','—',True]]),
    (108,'Hs', 'Hasij',       'Hassium',       '(277)',  'transition', 7, 8,  '[Rn] 5f¹⁴ 6d⁶ 7s²',       [2,8,18,32,32,14,2],  'kruto', None, None, '+8',    [['²⁷⁰Hs','—',True]]),
    (109,'Mt', 'Majtnerij',   'Meitnerium',    '(276)',  'transition', 7, 9,  '[Rn] 5f¹⁴ 6d⁷ 7s²',       [2,8,18,32,32,15,2],  'kruto', None, None, '?',     [['²⁷⁸Mt','—',True]]),
    (110,'Ds', 'Darmštatij',  'Darmstadtium',  '(281)',  'transition', 7, 10, '[Rn] 5f¹⁴ 6d⁹ 7s¹',       [2,8,18,32,32,17,1],  'kruto', None, None, '?',     [['²⁸¹Ds','—',True]]),
    (111,'Rg', 'Rendgenij',   'Roentgenium',   '(280)',  'transition', 7, 11, '[Rn] 5f¹⁴ 6d¹⁰ 7s¹',      [2,8,18,32,32,18,1],  'kruto', None, None, '?',     [['²⁸⁰Rg','—',True]]),
    (112,'Cn', 'Kopernicij',  'Copernicium',   '(285)',  'transition', 7, 12, '[Rn] 5f¹⁴ 6d¹⁰ 7s²',      [2,8,18,32,32,18,2],  'kaplj', None, None, '+2',    [['²⁸⁵Cn','—',True]]),
    (113,'Nh', 'Nihonij',     'Nihonium',      '(284)',  'post',       7, 13, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p¹',  [2,8,18,32,32,18,3],  'kruto', None, None, '+3',    [['²⁸⁴Nh','—',True]]),
    (114,'Fl', 'Flerovij',    'Flerovium',     '(289)',  'post',       7, 14, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p²',  [2,8,18,32,32,18,4],  'kruto', None, None, '+2',    [['²⁸⁹Fl','—',True]]),
    (115,'Mc', 'Moskovij',    'Moscovium',     '(288)',  'post',       7, 15, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p³',  [2,8,18,32,32,18,5],  'kruto', None, None, '+3',    [['²⁸⁸Mc','—',True]]),
    (116,'Lv', 'Livermorij',  'Livermorium',   '(293)',  'post',       7, 16, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁴',  [2,8,18,32,32,18,6],  'kruto', None, None, '+2',    [['²⁹³Lv','—',True]]),
    (117,'Ts', 'Tenes',       'Tennessine',    '(294)',  'halogen',    7, 17, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁵',  [2,8,18,32,32,18,7],  'kruto', None, None, '-1',    [['²⁹⁴Ts','—',True]]),
    (118,'Og', 'Oganeson',    'Oganesson',     '(294)',  'noble',      7, 18, '[Rn] 5f¹⁴ 6d¹⁰ 7s² 7p⁶',  [2,8,18,32,32,18,8],  'plin',  None, None, '0',     [['²⁹⁴Og','—',True]]),
]

ELEMENTS = [Element(*row) for row in _RAW]

# ---------------------------------------------------------------------------
#  Lookup indeksi
# ---------------------------------------------------------------------------
_BY_Z     = {e.z: e for e in ELEMENTS}
_BY_SYM   = {e.sym: e for e in ELEMENTS}
_BY_NAME  = {e.name.lower(): e for e in ELEMENTS}
_BY_LATIN = {e.latin.lower(): e for e in ELEMENTS}


def by_z(z):
    """Element po atomskom broju (1..118) ili None."""
    return _BY_Z.get(int(z))


def by_symbol(sym):
    """Element po simbolu ('Fe'); case-insensitive uz normalizaciju (fe -> Fe)."""
    if not sym:
        return None
    s = sym.strip()
    return _BY_SYM.get(s) or _BY_SYM.get(s.capitalize())


def by_name(name):
    """Element po hrvatskom ili latinskom nazivu (case-insensitive) ili None."""
    if not name:
        return None
    k = name.strip().lower()
    return _BY_NAME.get(k) or _BY_LATIN.get(k)


def period(p):
    """Svi elementi zadane periode (1..7), poredani po grupi/Z."""
    return [e for e in ELEMENTS if e.period == int(p)]


def group(g):
    """Svi elementi zadane grupe (1..18), poredani po periodi."""
    return [e for e in ELEMENTS if e.group == int(g)]


def lanthanides():
    return [e for e in ELEMENTS if e.category == 'lanthanide']


def actinides():
    return [e for e in ELEMENTS if e.category == 'actinide']


def parse_mass(mass):
    """
    Atomska masa kao float. Za sintetske elemente ('(97)') vraća maseni
    broj najstabilnijeg izotopa. Prima string ili Element.
    """
    if isinstance(mass, Element):
        mass = mass.mass
    return float(str(mass).strip().strip('()'))


def atomic_mass(sym):
    """Atomska masa (float) za simbol; KeyError ako element ne postoji."""
    e = by_symbol(sym)
    if e is None:
        raise KeyError("Nepoznat element: %r" % (sym,))
    return parse_mass(e.mass)


def neutrons(e):
    """Broj neutrona najzastupljenijeg izotopa (A - Z), zaokruženo."""
    return round(parse_mass(e.mass)) - e.z


# ---------------------------------------------------------------------------
#  Boje i polumjeri (dijele PT i MolViz renderi)
# ---------------------------------------------------------------------------

# CPK boje po elementu (za MolViz prikaz atoma)
CPK = {
    'H': '#f5f5f5', 'C': '#404040', 'N': '#4169e1', 'O': '#e03030',
    'F': '#40c040', 'Cl': '#30c030', 'Br': '#8b3000', 'I': '#580089',
    'S': '#d0d000', 'P': '#e06020', 'Na': '#a020f0', 'Mg': '#228b22',
    'Ca': '#808080', 'Fe': '#d04000', 'Zn': '#8b8baf', 'Cu': '#c88000',
}
CPK_DEFAULT = '#d0a0a0'

# Van der Waalsovi polumjeri (pm) — space-filling prikaz
VDW = {
    'H': 120, 'C': 170, 'N': 155, 'O': 152, 'F': 147, 'Cl': 175,
    'Br': 185, 'I': 198, 'S': 180, 'P': 180,
}
VDW_DEFAULT = 170

# Kovalentni polumjeri (pm) — ball & stick prikaz
COV = {
    'H': 31, 'C': 77, 'N': 75, 'O': 73, 'F': 71, 'Cl': 99,
    'Br': 114, 'I': 133, 'S': 103, 'P': 106,
}
COV_DEFAULT = 80

# Kategorijske boje (PT prikaz)
CATEGORY_COLORS = {
    'alkali': '#c0392b', 'alkaline': '#e67e22', 'transition': '#f39c12',
    'post': '#27ae60', 'metalloid': '#16a085', 'nonmetal': '#2980b9',
    'halogen': '#8e44ad', 'noble': '#7f8c9a', 'lanthanide': '#c0392b',
    'actinide': '#e74c3c',
}

# Hrvatski nazivi kategorija (za legendu / karticu)
CATEGORY_NAMES = {
    'alkali': 'Alkalijski metal', 'alkaline': 'Zemnoalkalijski metal',
    'transition': 'Prijelazni metal', 'post': 'Post-prijelazni metal',
    'metalloid': 'Metaloid', 'nonmetal': 'Nemetal', 'halogen': 'Halogeni element',
    'noble': 'Plemeniti plin', 'lanthanide': 'Lantanoid', 'actinide': 'Aktinoid',
}

# Boje i oznake elektronskih ljusaka (K, L, M, ...)
SHELL_COLORS = ['#378ADD', '#1D9E75', '#639922', '#BA7517', '#D85A30', '#534AB7', '#993556']
SHELL_NAMES = ['K', 'L', 'M', 'N', 'O', 'P', 'Q']

# Fizikalne konstante
U_KG = 1.66053906660e-27   # atomska jedinica mase (kg)
N_A = 6.02214076e23        # Avogadrova konstanta (1/mol)


def cpk_color(sym):
    """CPK boja elementa (fallback za nepoznate)."""
    return CPK.get(sym, CPK_DEFAULT)


if __name__ == "__main__":
    # Brza samoprovjera
    assert len(ELEMENTS) == 118, len(ELEMENTS)
    assert all(ELEMENTS[i].z == i + 1 for i in range(118)), "Z nije poredan"
    assert by_symbol('fe').name == 'Željezo'
    assert by_name('kisik').z == 8
    assert by_name('oxygen').z == 8
    assert abs(atomic_mass('C') - 12.011) < 1e-9
    assert parse_mass('(97)') == 97.0
    assert neutrons(by_z(6)) == 6
    assert len(period(2)) == 8
    assert [e.sym for e in group(1)][:3] == ['H', 'Li', 'Na']
    assert len(lanthanides()) == 15 and len(actinides()) == 15
    print("elements.py OK — 118 elemenata, lookup i mase rade.")
