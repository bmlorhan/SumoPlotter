""" Sumo win-lose web scraper """

# Standard libraries.
import csv
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

# Third Party libraries.
from selenium import webdriver


class MainApplication:
    """ GUI class """

    def __init__(self, master):
        """ GUI construction """
        self.master = master
        master.title('Sumo Scraper and Plotter')
        master.protocol('WM_DELETE_WINDOW', self.window_close)

        # Creates instance of Scraper class.
        self.scrape = Scraper()
        self.file_path = None

        # Styling variables.
        bg_color = 'lightsteelblue2'
        button_font = ('helvetica', 12, 'bold')

        # Canvas.
        self.main_canvas = tk.Canvas(master, width=450, height=450, bg=bg_color, relief='raised')
        self.main_canvas.pack()

        # Header label.
        self.app_name_label = tk.Label(master, text='Sumo Plotter', bg=bg_color)
        self.app_name_label.config(font=('helvetica', 20))
        self.main_canvas.create_window(235, 40, window=self.app_name_label)

        # Web scrape button. Returns file path of created CSV
        self.web_scrape_button = tk.Button(text='Get Sumo Stats', command=self.scrape.web_scraper,
                                           bg='green', fg='white', font=button_font)
        self.main_canvas.create_window(125, 140, window=self.web_scrape_button)

        # Import CSV file button
        self.import_csv_button = tk.Button(text='Import CSV File', command=self.import_csv_file,
                                           bg='green', fg='white', font=button_font)
        self.main_canvas.create_window(125, 210, window=self.import_csv_button)

    def run_web_scraper(self):
        """ Runs scraper and returns the CSV file path """
        self.file_path = self.scrape.web_scraper()
        return self.file_path

    def import_csv_file(self):
        """ User can import their own CSV file """
        self.file_path = filedialog.askopenfilename()
        return self.file_path

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

    def web_scraper(self):
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

        print('Finished scraping')

        data_dictionary = self.data_dictionary_creation()
        csv_file_path = self.create_csv_file(data_dictionary)

        driver.quit()
        return csv_file_path

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

        # Return all results as a nested list.
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
                    # Example: { 'Hakuho': { '202103' : '2-1-12' }}.
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

        # Allows user to designate file name and location.
        file_path = filedialog.asksaveasfilename(defaultextension='csv')
        with open(file_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, csv_fields)
            writer.writeheader()
            for k in data_dictionary:
                writer.writerow({field: data_dictionary[k].get(field) or k for field in csv_fields})

        return file_path


def main():
    """ Application loop function """
    root = tk.Tk()
    MainApplication(root)
    root.mainloop()


if __name__ == '__main__':
    main()
