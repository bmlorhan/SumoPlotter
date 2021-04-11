""" Sumo win-lose web scraper """

import csv
from selenium import webdriver
import tkinter as tk
from tkinter import messagebox


class MainApplication:
    """ Application class """

    def __init__(self, master):
        self.master = master
        master.title('Sumo Scraper and Plotter')
        master.protocol('WM_DELETE_WINDOW', self.window_close)

        self.scrape = Scraper()

        self.bg_color = 'lightsteelblue2'
        self.button_font = ('helvetica', 12, 'bold')

        # Canvas
        self.main_canvas = tk.Canvas(master, width=450, height=450, bg=self.bg_color, relief='raised')
        self.main_canvas.pack()

        # Header label
        self.app_name_label = tk.Label(master, text='Sumo Plotter', bg=self.bg_color)
        self.app_name_label.config(font=('helvetica', 20))
        self.main_canvas.create_window(235, 40, window=self.app_name_label)

        # Web scrape button
        self.web_scrape_button = tk.Button(text='Get Sumo Stats', command=self.scrape.scraper,
                                           bg='green', fg='white', font=self.button_font)
        self.main_canvas.create_window(125, 140, window=self.web_scrape_button)

    def window_close(self):
        """ Window closes confirmation """
        if messagebox.askokcancel('Quit', 'Do you want to close to the application?'):
            self.master.destroy()


class Scraper:
    """ Class for web scraping """

    def __init__(self):
        self.rikishi_name_list = []
        self.registry_number_list = []
        self.basho_list = ['202009', '202011', '202101', '202103']
        self.results_list = []

    def scraper(self):
        """ Retrieve list of Rikishi in the Makuuchi Banzuke who participated in the latest Basho"""
        webpage = r'http://sumodb.sumogames.de/Default.aspx'
        driver = webdriver.Firefox()
        driver.get(webpage)

        # Finds link to Rikishi Profile.
        rikishi = driver.find_elements_by_css_selector('td.shikona>a')
        for element in rikishi:
            self.rikishi_name_list.append(element.get_attribute('innerHTML'))
            # Separate the registry number from the rest of the url.
            url, r_number = element.get_attribute('href').split('=')
            self.registry_number_list.append(r_number)

        # Dict for Rikishi name and respective registry number.
        rikishi_dict = dict(zip(self.rikishi_name_list, self.registry_number_list))

        # For each name, click their respective link and
        # run the function before going back to home page.
        for name in self.rikishi_name_list:
            print('Now scraping {}'.format(name))
            driver.find_element_by_link_text(name).click()
            self.results_list.append(self.win_lose_retrieval(driver, rikishi_dict.get(name)))
            driver.back()

        data_dictionary = self.data_dictionary_creation()
        self.create_csv_file(data_dictionary)

        driver.quit()

    def win_lose_retrieval(self, driver, registry_number):
        """ Scrape the Wins and Loses for each Rikishi """
        find_results = driver.find_elements_by_css_selector('td.wl>a')
        results = []
        for element in find_results:
            # Loops through each Basho date.
            for date in self.basho_list:
                # Used to compare to hrefs in the html
                # so that we get ones we want based on registry and basho.
                basho_href = r'http://sumodb.sumogames.de/Rikishi_basho.aspx?r={}&b={}'\
                            .format(registry_number, date)

                # If the href matches, get the innerHTML ( our results ) and append to results list.
                if element.get_attribute('href') == basho_href:
                    results.append(element.get_attribute('innerHTML'))

        # Return all results.
        return results

    def data_dictionary_creation(self):
        """ Takes the Rikishi names, results, and basho dates and creates a nested dictionary """
        results_dict = {}

        # Start indexing of Results at 0.
        list_index = 0
        while list_index != len(self.results_list):
            for name in self.rikishi_name_list:
                # Start indexing of nested lists at 0.
                result_index = 0
                # Create a nested dictionary for each Rikishi.
                results_dict[name] = {}
                for date in self.basho_list:
                    # Add key ( Basho Date ) and value ( Results ) pairs to each nested dictionary.
                    # Example: { RikishiName { Basho Date : Results }
                    results_dict[name][date] = self.results_list[list_index][result_index]
                    # Increase indexing of nested list by 1.
                    result_index += 1
                # Increase indexing of Results by 1.
                list_index += 1

        return results_dict

    def create_csv_file(self, data_dictionary):
        """ Creates a CSV file using the data in data_dictionary """
        csv_fields = ['name']
        for date in self.basho_list:
            csv_fields.append(date)

        with open('Sumo_Basho_Results.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, csv_fields)
            writer.writeheader()
            for k in data_dictionary:
                writer.writerow({field: data_dictionary[k].get(field) or k for field in csv_fields})


def main():
    root = tk.Tk()
    MainApplication(root)
    root.mainloop()


if __name__ == '__main__':
    main()