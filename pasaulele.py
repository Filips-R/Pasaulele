import requests
import random
import math
from fuzzywuzzy import process

API_URL = "https://restcountries.com/v3.1/all"


# Aprēķina attālumu kilometros starp diviem punktiem izmantojot Harvesīna formulu.
# Funkcija iegūta izmantojot mākslīgo intelektu (ChatGPT).
def calculate_distance(start_coords, end_coords):

    lat1, lon1 = map(math.radians, start_coords)  # grādus pārvērš radiānos
    lat2, lon2 = map(math.radians, end_coords)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    A = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    C = 2 * math.atan2(math.sqrt(A), math.sqrt(1-A))
    return int(6371 * C)  # Zemes rādiuss ~6371 km


# Vienkāršs ģeogrāfiskā virziena aprēķins. Virziens tiek atgriezts kā divu burtu kods: 'N','S' + 'E','W'.
# N - North (Ziemeļi) | S - South (Dienvidi) | E - East (Austrumi) | W - West (Rietumi)
# Funkcija iegūta izmantojot mākslīgo intelektu (ChatGPT).
def calculate_direction(start_coords, end_coords):

    vertical = 'N' if end_coords[0] > start_coords[0] else 'S'
    horizontal = 'E' if end_coords[1] > start_coords[1] else 'W'
    return vertical + horizontal


# Galvenā spēles daļa
class CountryGuessingGame:
# Saglabā mērķvalsti, ievadītās atbildes un izvada atgriezenisko saiti.
    def __init__(self, country_list):
        # country_list - saraksts ar valstu datiem no API.
        self.country_list = country_list
        # Izmanto RANDOM funkciju lai nejauši izvēlētos mērķvalsti.
        self.target_country = random.choice(country_list)
        # Izveido sarakstu kurā atrodas ievadīto minējumu vēsture: katrs ieraksts = (nosaukums, attālums, virziens)
        self.guess_history = []


    # Galvenais spēles cikls.
    def play_game(self):

        print("\nEs domāju par kādu valsti. Mēģini uzminēt!")
        print("Ievadi valsts nosaukumu angliski vai raksti 'padodos' lai uzzinātu atbildi.")
        while True:
            user_input = input("Tava atbilde: ")  # spēlētāja minējums

            # 'padodos' komanda - izbeidz ciklu un atklāj mērķvalsti
            if user_input.lower() == 'padodos':
                print(f"Tu padevies! Tā bija {self.target_country['name']}.")
                print("")
                break


            # Mēģina atrast atbilstošu valsti ar FuzzyWuzzy matching metodi pat ja uzraksti ar pareizrakstības kļūdu
            matched_country = self.find_country(user_input)
            if not matched_country:
                print("Valsts nav atrasta. Mēģini vēlreiz.")
                continue  # ja nav atbilstošas valsts, turpina ciklu

            # Pārbauda, vai valsti jau neesi minējis
            # Saglabā minēto valstu nosaukumus already_guessed sarakstā, guess_history saraksts tiek saglabāt kā (country_name, distance, direction) tādēļ ņem pirmo elementu, jeb nosaukumu.
            already_guessed = [entry[0] for entry in self.guess_history]
            if matched_country['name'] in already_guessed:
                print("Tu šo valsti jau minēji. Izvēlies citu.")
                continue

            # Ja mērķvalsts un minējums robežojas, uzstāda, ka distance = 0 (km)
            if self.borders_target(matched_country):
                distance = 0
            else:
                # Citādi aprēķina patieso attālumu
                distance = calculate_distance(
                    matched_country['coords'], self.target_country['coords']
                )

            # Virziena aprēķins
            direction = calculate_direction(
                matched_country['coords'], self.target_country['coords']
            )

            # Saglabā minējumu atmiņā
            self.guess_history.append((matched_country['name'], distance, direction))

            # Sakārto minējumus pēc attāluma un izvada rezultātus
            # Ņem otro elementu (attālumu) no saraksta un izveido sakārtotu sarakstu. (Lambda ir kā mini funkcija)
            sorted_guesses = sorted(self.guess_history, key=lambda x: x[1])
            print("\nTavas līdzšinējās atbildes: ")
            # loops kurš izvada sakārtoto sarakstu sākot ar 1
            for n, (name, dist, dirc) in enumerate(sorted_guesses, 1):
                print(f" {n}. {name} — {dist} km {dirc}")
            print("")

            # Ja spēlētājs uzmin mērķvalsti, cikls (spēle) tiek izbeigta un izvada minējumu skaitu (minēto valstu saraksta garumu)
            if matched_country['name'] == self.target_country['name']:
                print(f"Apsveicam! Tu uzminēji pēc {len(self.guess_history)} mēģinājumiem!\n")
                break
            print(self.target_country['name'])


    # Meklē tuvāko atbilstību starp lietotāja ievadīto valsti un valstu nosaukumiem no API.
    # Izmanto FuzzyWuzzy bibliotēku, lai salīdzinātu līdzību.
    def find_country(self, user_input):

        names = [country['name'] for country in self.country_list]
        match, score = process.extractOne(user_input, names)
        if score >= 70:  # slieksnis atbilstībai
            for country in self.country_list:
                if country['name'] == match:
                    return country # atgriež pilno info par valsti (ieskaitot koordinātas, robežas, u.u.t.)
        return None


    # Pārbauda, vai spēlētāja minētā valsts robežojas ar mērķvalsti.
    # Valstis tiek norādītas pēc trīsburtu ISO kodeksem 'country_code', piemēram Latvia = LVA.
    def borders_target(self, country):

        return (
            country.get('borders') and self.target_country.get('country_code') in country['borders']
        ) or (
            self.target_country.get('borders') and country.get('country_code') in self.target_country['borders']
        )

# Nolasa JSON datus no REST API un izveido sarakstu ar valstu informāciju.
# Katram ierakstam: nosaukums, koordinātes, robežu saraksts, valsts kods.
def load_countries():

    response = requests.get(API_URL)
    countries = []
    for entry in response.json():
        countries.append({
            'name': entry['name']['common'],
            'coords': entry.get('latlng', [0, 0]),
            'borders': entry.get('borders', []),
            'country_code': entry.get('cca3', '')
        })
    return countries

# Main funkcija
def main():
    # Ielādē valstu datus
    country_list = load_countries()

    # Spēles instrukcijas
    print("Laipni lūdzam spēlē 'Pasaulele'!")
    print("Uzmini valsti pēc tās attāluma un virziena.")


    # Galvenais cikls, ļauj spēlēt vairākas reizes
    while True:
        game = CountryGuessingGame(country_list)
        game.play_game()
        again = input("Spēlēt vēlreiz? (ja/ne): ")
        if again.lower() != 'ja':
            print("Paldies par spēli! Uz redzēšanos.")
            break

if __name__ == '__main__':
    main()
