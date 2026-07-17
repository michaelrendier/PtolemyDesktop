#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import tkinter
from tkinter.filedialog import (askdirectory,
                                askopenfilename)
from tkinter.messagebox import showerror, showinfo

import pandas as pd


########################################################################
class AppRoot:
    """"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.file_name = "settings.dat"
        self.kpi = ""
        self.region = ""
        self.data_source = ""

        self.kpis = ["KPI1", "KPI2", "KPI3", "KPI4", "KPI5", "KPI6", "KPI7", "KPI8", "KPI9", "KPI10"]
        self.regions = ["ASP", "EUROPE", "AMERICA", "EUROPE", "ASP", "NAN", "ASP", "EUROPE", "NAN", "EUROPE"]
        self.data_sources = ["HELIOS", "NAN", "FRAUD", "DCT", "CONSILIUM", "DCT", "NAN",  "DCT", "CONSILIUM", "DCT"]
        self.folders = ["KPI OUTPUT", "KPI OUTPUT1", "KPI OUTPUT2", "KPI OUTPUT3", "KPI OUTPUT4", "KPI OUTPUT5",
                        "KPI OUTPUT6", "KPI OUTPUT7", "KPI OUTPUT8", "KPI OUTPUT9"]
        self.file_names = ["BOOK7", "BOOK30", "BOOK31", "BOOK32", "BOOK33", "BOOK34", "BOOK35", "BOOK36", "BOOK37",
                           "BOOK38"]
        self.sheet_names = ["HELLO", "SUNNY", "123", "REQ", "RAJ", "DDD", "HELLO", "RISHI", "345", "REQ"]
        self.file_types = ["EXCEL", "CSV", "EXCEL", "EXCEL", "CSV", "EXCEL", "CSV", "CSV", "EXCEL", "CSV"]

        self.mappings = {}
        self.data = {}

        self.data_frame = None
        self.CSV = ".csv"
        self.XL = ".xlsx"

        root = tkinter.Tk()
        self.root = root
        self.root.title("UI")
        self.root.geometry("500x500")

        top = tkinter.Frame(self.root)
        top.pack(fill=tkinter.BOTH, expand=tkinter.YES)

        bottom = tkinter.Frame(self.root)
        bottom.pack(expand=tkinter.YES, fill=tkinter.X)

        self.btn = tkinter.Button(bottom, width=15, text="Upload File", bg="black", fg="white",
                                  command=self.select_file, font=('Helvetica', 12, 'bold'))
        self.btn.pack(pady=10)
        label = tkinter.Label(bottom, width=450, wraplength=365)
        label.pack(fill=tkinter.X, expand=tkinter.YES)
        self.imported_files_label = label
        tkinter.Button(bottom, width=15, text="Save Selection", bg="white", fg="black",
                       command=self.save_to_file, font=('Helvetica', 12, 'bold')).pack(pady=10)
tkinter.
        f1 = tkinter.Frame(top)
        f2 = tkinter.Frame(top)
        f3 = tkinter.Frame(top)

        f1.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
        f2.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
        f3.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)

        tkinter.Label(f1, text="KPI").pack()
        self.listbox1 = tkinter.Listbox(f1, selectmode=tkinter.SINGLE)
        self.listbox1.pack(fill=tkinter.X)
        self.listbox1.bind("<Double-1>", lambda e: self.capture_kpi())
        self.lb = tkinter.Label(f1)
        self.lb.pack()

        tkinter.Label(f2, text="REGION").pack()
        self.listbox2 = tkinter.Listbox(f2, selectmode=tkinter.SINGLE)
        self.listbox2.pack(fill=tkinter.X)
        self.listbox2.bind("<Double-1>", lambda e: self.capture_region())
        self.lb2 = tkinter.Label(f2)
        self.lb2.pack()

        tkinter.Label(f3, text="DATA SOURCES").pack()
        self.listbox3 = tkinter.Listbox(f3, selectmode=tkinter.SINGLE)
        self.listbox3.pack(fill=tkinter.X)
        self.listbox3.bind("<Double-1>", lambda e: self.capture_data_sources())
        self.lb3 = tkinter.Label(f3)
        self.lb3.pack()

        items = ["NAN", "KPI1", "KPI2", "KPI3", "KPI4", "KPI5", "KPI6"]
        for item in items:
            self.listbox1.insert(tkinter.END, item)
        self.listbox1.selection_set(3)
        self.items = items

        items2 = ["NAN", "America", "Asia", "ASP", "Europe", "Menat"]
        for item in items2:
            self.listbox2.insert(tkinter.END, item)
        self.listbox2.selection_set(3)
        self.item2 = items2

        items3 = ["NAN", "HELIOS", "FRAUD", "DCT", "CONSILIUM", "ALL"]  # edit these items accordingly
        for item in items3:
            self.listbox3.insert(tkinter.END, item)
        self.listbox3.selection_set(3)
        self.item3 = items3

        self.DATA_DIR = "./v3data/"
        self.main_dir = None
        if not os.path.exists(self.DATA_DIR):
            os.mkdir(self.DATA_DIR)
        self.get_root_folder()
        self.load_data()

        self.root.mainloop()

    # ----------------------------------------------------------------------
    def get_root_folder(self):
        """"""
        try:
            file = open(f"{self.DATA_DIR}{self.file_name}", "r")
            self.main_dir = file.readline()
            file.close()
        except FileNotFoundError:
            self.main_dir = askdirectory(title="Select Folder to Save Files")
            if self.main_dir:
                file = open(f"{self.DATA_DIR}{self.file_name}", "w")
                file.write(self.main_dir)
                file.close()
            else:
                self.root.quit()

    # ----------------------------------------------------------------------
    def capture_kpi(self):
        """"""
        self.kpi = self.listbox1.get(tkinter.ACTIVE)
        self.lb.config(text=self.kpi)

    # ----------------------------------------------------------------------
    def capture_region(self):
        """"""
        self.region = self.listbox2.get(tkinter.ACTIVE)
        self.lb2.config(text=self.region)

    # ----------------------------------------------------------------------
    def capture_data_sources(self):
        """"""
        self.data_source = self.listbox3.get(tkinter.ACTIVE)
        self.lb3.config(text=self.data_source)

    # ----------------------------------------------------------------------
    def save_to_file(self):
        """"""
        if self.data_frame is None:
            showerror("ERROR", "Please select output file before you continue.")
            return
        if self.kpi == "" or self.region == "" or self.data_source == "":
            showerror("Error", "Please select one item in each of the three columns")
            return

        comb = f"{self.kpi.lower()}{self.region.lower()}{self.data_source.lower()}"
        # print("combination", comb)
        try:
            index = self.mappings[comb]
            self.save_file(index)
        except KeyError:
            showerror("ERROR", "No value in mapping file")
            return

    # ----------------------------------------------------------------------
    def load_data(self):
        """self.kpis, self.regions, self.data_sources, self.folders,
            self.filenames, self.sheet_names, self.file_types;
            Must have the same number of content, else we risk an index error here."""
        c = Constants
        kpis = {}
        regions = {}
        data_sources = {}
        folders = {}
        file_names = {}
        sheet_names = {}
        file_types = {}
        for i in range(len(self.kpis)):
            kpi = self.kpis[i]
            region = self.regions[i]
            data_source = self.data_sources[i]
            key = f"{kpi.lower()}{region.lower()}{data_source.lower()}"
            # print(key)
            self.mappings[key] = i

            kpis[i] = kpi
            regions[i] = region
            data_sources[i] = data_source
            folders[i] = self.folders[i]
            file_names[i] = self.file_names[i]
            sheet_names[i] = self.sheet_names[i]
            file_types[i] = self.file_types[i]

        self.data[c.KPI] = kpis
        self.data[c.REGION] = regions
        self.data[c.DATA_SOURCE] = data_sources
        self.data[c.OUTPUT_FOLDER] = folders
        self.data[c.FILE_NAME] = file_names
        self.data[c.SHEET_NAME] = sheet_names
        self.data[c.FILE_TYPE] = file_types

    # ----------------------------------------------------------------------
    def save_file(self, index: int):
        """"""
        c = Constants
        folder = self.data[c.OUTPUT_FOLDER][index]
        filename = self.data[c.FILE_NAME][index]
        sheet_name = str(self.data[c.SHEET_NAME][index])
        file_type = self.data[c.FILE_TYPE][index]
        file_type = file_type.lower()
        p1 = os.path.join(self.main_dir, folder)
        if not os.path.exists(p1):
            os.mkdir(p1)
        if file_type == c.EXCEL:
            ext = ".xlsx"
            path = os.path.join(p1, f"{filename}{ext}")
            if sheet_name == "":
                self.data_frame.to_excel(path)
            else:
                self.data_frame.to_excel(path, sheet_name=sheet_name)
        elif file_type == c.CSV:
            ext = ".csv"
            path = os.path.join(p1, f"{filename}{ext}")
            self.data_frame.to_csv(path)
        else:
            raise Exception  # or showerror() and return, we fail for now, no-time
        showinfo("SUCCESS", f"Selection was successfully saved in {filename}{ext}")

    # ----------------------------------------------------------------------
    def select_file(self):
        """select file, convert it's content into a data_frame"""
        f = askopenfilename(filetypes=["Excel *.xlsx;*.csv"])
        if f:
            self.btn.config(state=tkinter.DISABLED)
            if f.endswith(self.XL):
                self.data_frame = pd.read_excel(f)
            else:
                self.data_frame = pd.read_csv(f)


class Constants:
    KPI = "KPI"
    REGION = "REGION"
    DATA_SOURCE = "DATA SOURCES"
    OUTPUT_FOLDER = "OUTPUT FOLDER LOCATION"
    FILE_NAME = "FILE NAME"
    SHEET_NAME = "SHEET NAME"
    FILE_TYPE = "FILE TYPE"
    EXCEL = "excel"
    CSV = "csv"
    SAVE_AS_UPPER = True


if __name__ == "__main__":
    AppRoot()