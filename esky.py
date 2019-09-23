from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import csv
from geopy.distance import great_circle
import sys

months_to_int = ['', 'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec', 'Sierpień', 'Wrzesień',
                 'Październik', 'Listopad', 'Grudzień']

class DateObj:
    def __init__(self, start, end, price, times, airline, start_pl, end_pl):
        self.start = start
        self.end = end
        self.price = int(price)
        self.times = times
        self.airline = airline
        self.start_pl = start_pl
        self.end_pl = end_pl

    def print(self):
        print('Places', self.start_pl, self.end_pl)
        print('Dates', self.start, self.end)
        print('Price', str(self.price))
        print('Length of flights', self.times)
        print('Airline', self.airline)


class AirportObj:
    def __init__(self, code, gps):
        self.code = code
        self.gps = gps
        self.neighbors = []


airports = []
# parse airport csv file to get airports IATA codes and gps locations
with open('airports.csv', encoding="utf8") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            if row[13] is not '' and 'large_airport' in row[2]:
                airport = AirportObj(row[13], (row[4], row[5]))
                airports.append(airport)
            line_count += 1

print('Large airports', len(airports))

# get neighbors beneath 300km to each airport
for air in airports:
    for airport in airports:
        if air is not airport:
            dist = great_circle(air.gps, airport.gps)
            if dist < int(sys.argv[7]):
                air.neighbors.append(airport.code)

# setting up chrome driver for selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('log-level=3')
browser = webdriver.Chrome(executable_path='C:\FlightsPython\chromedriver.exe', chrome_options=chrome_options)
browser.set_window_size(1920, 1080)


def dep_country_chooser(dep_country):
    fly_from = browser.find_element_by_xpath("//input[@id='departureRoundtrip0']")
    fly_from.clear()
    for i in range(30):
        fly_from.send_keys(Keys.BACKSPACE)
    # time.sleep(0.5)
    fly_from.send_keys(dep_country)


def arrival_country_chooser(arrival_country):
    fly_to = browser.find_element_by_xpath("//input[@id='arrivalRoundtrip0']")
    fly_to.clear()
    for i in range(30):
        fly_to.send_keys(Keys.BACKSPACE)
    # time.sleep(0.5)
    fly_to.send_keys(arrival_country)


def dep_date_chooser(day, month, year):
    print(day, month, year)
    curr_year = browser.find_element_by_xpath("//span[@class='ui-datepicker-year']")
    curr_year = int(curr_year.text)
    while curr_year < year:
        # next buttons
        next_button = browser.find_element_by_xpath("//a[@title='Następny']")
        next_button.click()
        # time.sleep(0.5)

        curr_year = browser.find_element_by_xpath("//span[@class='ui-datepicker-year']")
        curr_year = int(curr_year.text)

    curr_month = browser.find_element_by_xpath("//span[@class='ui-datepicker-month']")
    curr_month_int = 0
    for x in months_to_int:
        if curr_month.text == x:
            curr_month_int = months_to_int.index(x)

    while curr_month_int < month:
        next_button = browser.find_element_by_xpath("//a[@title='Następny']")
        next_button.click()
        # time.sleep(0.5)

        curr_month = browser.find_element_by_xpath("//span[@class='ui-datepicker-month']")
        for x in months_to_int:
            if curr_month.text == x:
                curr_month_int = months_to_int.index(x)

    days_items = browser.find_elements_by_xpath("//tbody/tr/td/a")
    for d in days_items:
        if d.text == str(day):
            actions = ActionChains(browser)
            actions.move_to_element(d).click().perform()
            # d.click()
            break


def iteration(start_date, end_date, prices_map, start_pl, end_pl):
    browser.get(link)
    # time.sleep(1)

    dep_country_chooser(start_pl)
    arrival_country_chooser(end_pl)

    dep_date_button = browser.find_element_by_xpath("//input[@id='departureDateRoundtrip0']")
    dep_date_button.click()
    dep_date_chooser(start_date.day, start_date.month, start_date.year)

    dep_date_button = browser.find_element_by_xpath("//input[@id='departureDateRoundtrip1']")
    dep_date_button.click()
    dep_date_chooser(end_date.day, end_date.month, end_date.year)

    # click on search button and wait for results
    search = browser.find_element_by_xpath("//button[@type='submit']")
    search.click()
    # time.sleep(20)

    try:
        temp = WebDriverWait(browser, 60).until(
            ec.visibility_of_element_located((By.XPATH, "//span[@class='current-price']/span[@class='amount']")))
    except:
        print("timeout")
        return

    prices_web = browser.find_elements_by_xpath("//span[@class='current-price']/span[@class='amount']")
    flight_times = browser.find_elements_by_xpath("//span[@class='flight-time']/span[@class='time']")
    airlines = browser.find_elements_by_xpath("//div[@class='logos-airline']/span/img")  # get alt

    for i in range(3):
        try:
            min_price = prices_web[i].text
            times = [flight_times[i * 2].text, flight_times[i * 2 + 1].text]
            airline = airlines[i].get_attribute("alt")
            obj = DateObj(start_date, end_date, min_price, times, airline, start_pl, end_pl)
            print(min_price)
            prices_map.append(obj)
        except:
            print("smth went wrong")


# main script
#parse user interface WAW SGN 26/12/19 15/02/20 21 3
start_place = sys.argv[1]#'WAW'
end_place = sys.argv[2]#'SGN'

increment_day = 1
plus_minus_end = int(sys.argv[6])#4
standard_length = int(sys.argv[5])#21
prices_map = []

start_places = [start_place]
end_places = [end_place]
for air in airports:
    if air.code == start_place:
        for neigh in air.neighbors:
            start_places.append(neigh)
    if air.code == end_place:
        for neigh in air.neighbors:
            end_places.append(neigh)

print("Flights search at selected airports")
print(start_places)
print(end_places)

link = 'https://www.esky.pl/'
start_date_init = sys.argv[3]#"26/12/19"  # it will start searching from next day
final_date_init = sys.argv[4] #"28/12/19"

for start_pl in start_places:
    for end_pl in end_places:
        print("Now searching for", start_pl, end_pl)
        start_date = pd.to_datetime(start_date_init, format="%d/%m/%y")
        final_date = pd.to_datetime(final_date_init, format="%d/%m/%y")

        while start_date < final_date:
            start_date = pd.to_datetime(start_date, format="%m/%d/%y") + pd.DateOffset(days=increment_day)
            end_date = pd.to_datetime(start_date, format="%m/%d/%y") + pd.DateOffset(days=standard_length)
            iteration(start_date, end_date, prices_map, start_pl, end_pl)

            for i in range(1, plus_minus_end):
                end_date = pd.to_datetime(start_date, format="%m/%d/%y") + pd.DateOffset(days=standard_length - i)
                iteration(start_date, end_date, prices_map, start_pl, end_pl)
            for i in range(1, plus_minus_end):
                end_date = pd.to_datetime(start_date, format="%m/%d/%y") + pd.DateOffset(days=standard_length + i)
                iteration(start_date, end_date, prices_map, start_pl, end_pl)

sort = sorted(prices_map, key=lambda x: x.price, reverse=False)
with open('results.txt', 'w') as file:
    counter = 0
    for p in sort:
        counter+=1
        file.write("["+str(counter)+"]")
        file.write('\n')
        file.write('Places '+ str(p.start_pl)+' '+ str(p.end_pl))
        file.write('\n')
        file.write('Dates '+ str(p.start)+ ' '+str(p.end))
        file.write('\n')
        file.write('Price '+ str(p.price))
        file.write('\n')
        file.write('Length of flights '+ str(p.times))
        file.write('\n')
        file.write('Airline '+ str(p.airline))
        file.write('\n')
        file.write("---------------------------")
        file.write('\n')
for p in sort:
    p.print()
    print(" ")
browser.close()
