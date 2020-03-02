'''
Sergio Chairez
Maksym Sagadin
'''


import requests
import json
import os
import sys
import tkinter as tk
import tkinter.filedialog
from tkinter.ttk import Progressbar
import tkinter.messagebox as tkmb
import time
import threading
import queue


def gui2fg():
    """Brings tkinter GUI to foreground on Mac
       Call gui2fg() after creating main window and before mainloop() start
    """
    if sys.platform == 'darwin':
        tmpl = 'tell application "System Events" to set frontmost of every process whose unix id is %d to true'
        os.system("/usr/bin/osascript -e '%s'" % (tmpl % os.getpid()))


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('School Lookup')
        self.geometry("300x130")
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.grid_columnconfigure(0, weight=1)

        # self.container = tk.Frame(self)
        choice_label = tk.Label(background='blue',
                                text='Choose the type of school',
                                fg='white',

                                font=('Helvetica', 20)).grid(sticky='ew')
        # represents the URL path and endpoint to the schools dataset
        self._API_URL_ROOT_AND_ENDPOINT = "https://api.data.gov/ed/collegescorecard/v1/schools"
        API_KEY = "edT3yUyoeGnLT0mWh6o34mjlpdqeDoIH54p6Zanq"  # Sergio's
        # API KEY = "U3gvOjZeTT85LONZzqWHLsR56JqmaYgc55MQZlKe" # Maksym's
        self._s = requests.Session()
        # this ensures that the api key is appended for the entire session. no need to add the api_key every time xD
        self._s.auth = (API_KEY, '')

        self.buttons()
        self.percent_str = tk.StringVar(self, "In progress... ")
        self.percent = tk.Label(
            self, textvariable=self.percent_str,  anchor=tk.W).grid(row=2, column=0)

        self.progress = Progressbar(
            self, orient=tk.HORIZONTAL, maximum=100, mode='indeterminate')
        self.progress.grid(row=3, column=0, rowspan=True)
        self.progress.start()

        self.update()

        self._CA_colleges = self._get_CA_schools_thread()

        self.after(1000, self._close_progress_bar())
        self.update()

    def on_exit(self):
        '''
        This function opens a message box asking if the user wants to quit
        Then quits out of the program if the user clicks yes
        '''
        if tkmb.askyesno("Exit", "Do you want to quit the application?"):
            self.quit()

    def _get_CA_schools_thread(self):
        '''
        This function starts a thread to get the school API info
        '''
        q = queue.Queue()

        ca_schools_thread = threading.Thread(
            target=q.put(self._get_CA_college_schools()), name="ca_schools_thread")

        start = time.time()  # assigns the time we start thread of fetching schools
        ca_schools_thread.start()
        ca_schools_thread.join()
        print("Elapsed time : {:.10f}s".format(
            time.time() - start))

        return q.get()

    def _close_progress_bar(self):
        '''
        This function gets rid of the progress bar in the main
        and puts the state of the buttons back to normal
        '''
        self.progress.stop()
        # self.progress.pack_forget()
        self.progress.destroy()
        self.percent_str.set("Done ...")
        self.config(cursor="")
        self.by_public_button["state"] = "normal"
        self.by_private_button["state"] = "normal"
        self.by_both_botton["state"] = "normal"

    def _get_CA_college_schools(self):
        '''
        function call for the GET HTTP API Request to get all schools
        '''
        # start = time.perf_counter()
        parameters = {
            "school.state": "CA",
            "school.carnegie_size_setting__range": "12..17",
            "school.degrees_awarded.predominant": "3",
            "_fields": "id,school.name,school.city,school.ownership",
            "per_page": "75"

        }
        page = self._s.get(self._API_URL_ROOT_AND_ENDPOINT, params=parameters)
        return page.json()['results']

    def _get_one_school_info(self, school_id):
        '''
        function call for the GET HTTP API Request to get specific school
        '''
        parameters = {
            "id": school_id,
            "_fields": "school.name,latest.cost.tuition.in_state,latest.student.enrollment.all,latest.academics.program_percentage.computer,latest.academics.program_percentage.engineering",
        }
        page = self._s.get(self._API_URL_ROOT_AND_ENDPOINT, params=parameters)
        # print(page.url)
        return page.json()['results']

    def buttons(self):
        '''
        This function creates the buttons for the Main Window
        Buttons are intially disabled until the progressbar is
        destroyed
        '''
        buttons_frame = tk.Frame(self)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)

        buttons_frame.grid(
            row=1, column=0,  padx=10, pady=10)

        self.by_public_button = tk.Button(
            buttons_frame, text='Public',
            command=self._public_schools_logic, state="disabled")
        self.by_public_button.grid(
            row=0, column=1, sticky='ew', padx=15, pady=10)

        self.by_private_button = tk.Button(
            buttons_frame, text='Private', command=self._private_schools_logic, state="disabled")

        self.by_private_button.grid(
            row=0, column=2, sticky='ew', padx=15, pady=10)

        self.by_both_botton = tk.Button(buttons_frame, text="Both",
                                        command=self._by_both_school_types_logic, state="disabled")
        self.by_both_botton.grid(
            row=0, column=3, sticky='ew', padx=15, pady=10)

        self.but_about = tk.Button(buttons_frame, text="About",
                                   command=self._about_info)
        self.but_about.grid(
            row=0, column=4, sticky='ew', padx=15, pady=10)

    # button1 logic
    def _public_schools_logic(self):
        '''
        function call for public schools button
        '''
        self.by_public_button['state'] = 'disabled'

        self.config(cursor="wait")
        self.update()
        public_schools = [(str(i['school.name']) + ", " + str(i['school.city']), i['id'])
                          for i in self._CA_colleges if i['school.ownership'] == 1]

        public_schools = sorted(public_schools)
        # print(public_schools)
        # print(len(public_schools))  # 31
        dialogWin = DialogWin(self, *public_schools)
        self.wait_window(dialogWin)
        id_of_schools_list = dialogWin.buttonClick()

        if id_of_schools_list is not None:
            temp_list = self.school_threading(id_of_schools_list)
            displayWin = DisplayWin(self, *temp_list)
        self.config(cursor="")
        self.by_public_button['state'] = 'normal'
        


    # button2 logic

    def _private_schools_logic(self):
        '''
        function call for private schools button
        '''

        self.by_private_button['state'] = 'disabled'

        self.config(cursor="wait")
        self.update()

        private_schools = [(str(i['school.name']) + ", " + str(i['school.city']), i['id'])
                           for i in self._CA_colleges if i['school.ownership'] == 2]

        private_schools = sorted(private_schools)
        # print(private_schools)
        # print(len(private_schools))  # 22
        dialogWin = DialogWin(self, *private_schools)
        self.wait_window(dialogWin)
        id_of_schools_list = dialogWin.buttonClick()
        if id_of_schools_list is not None:
            temp_list = self.school_threading(id_of_schools_list)
            displayWin = DisplayWin(self, *temp_list)
        self.config(cursor="")
        self.by_private_button['state'] = 'normal'
        

    # button3 logic
    def _by_both_school_types_logic(self):
        '''
        function call for all schools button
        '''

        self.by_both_botton['state'] = 'disabled'
        self.config(cursor="wait")
        self.update()

        all_schools = [(str(i['school.name']) + ", " + str(i['school.city']), i['id'])
                       for i in self._CA_colleges]

        all_schools = sorted(all_schools)
        # print(all_schools)
        # print(len(all_schools))  # 58
        dialogWin = DialogWin(self, *all_schools)
        self.wait_window(dialogWin)
        id_of_schools_list = dialogWin.buttonClick()
        if id_of_schools_list is not None:
            temp_list = self.school_threading(id_of_schools_list)
            displayWin = DisplayWin(self, *temp_list)
        self.config(cursor="")
        self.by_both_botton['state'] = 'normal'

    # button4 logic
    def _about_info(self):
        '''
        button to credit the developers
        '''
        credits = "Credits:\nSergio Chairez\nMaksym Sagadin"
        tkmb.showinfo("Credits", credits)

    def school_threading(self, id_list):
        '''
         function that will thread the list of schools and add to a queu,
         append to a list and return a list of schools after being threaded
        '''
        tmp_q = queue.Queue()
        school_details = []
        if len(id_list) != 0:
            i = 1
            for val in id_list:
                t = threading.Thread(target=lambda arg: tmp_q.put(self._get_one_school_info(
                    arg)), name="single_school_thread" + str(i), args=(val,))
                i += 1
                school_details.append(t)

        for t in school_details:
            t.start()

        for t in school_details:
            t.join()

        temp_list = []
        for val in range(len(id_list)):
            temp_list.append(tmp_q.get(val))

        return temp_list


class DialogWin(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.grab_set()
        self.focus_set()
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._onCloseWindow)
        self.title("Choose up to 4 schools")
        self.schools_list = args

        # print(self.schools_list)

        self.displayFrame = tk.Frame(self)
        self.displayFrame.grid(
            row=40, column=0, sticky='nsew', padx=10, pady=20)

        self.listbox = tk.Listbox(
            self.displayFrame, selectmode=tk.MULTIPLE, width=60, height=10)

        scrollbar = tk.Scrollbar(
            self.displayFrame, orient="vertical", command=self.listbox.yview)

        scrollbar.pack(side="right", fill="y")

        self.listbox.config(yscrollcommand=scrollbar.set)

        for elem in range(len(self.schools_list) - 1):
            self.listbox.insert(
                tk.END, f'{self.schools_list[elem][0]}')

        self.listbox.pack(anchor=tk.W)

        self.listbox.bind('<<ListboxSelect>>', self.getSelected)
        btn = tk.Button(self.displayFrame, text='OK',
                        command=self.buttonClick).pack()

    def _onCloseWindow(self):
        '''
        [X] button clicked -> close dialog window, return to Main window
        sets the index of the selected listbox items to an empty string
        '''
        self.selection = ""
        self.destroy()

    def getSelected(self, event):
        ''' returns the index values of the selected listbox items as a tuple'''
        self.selection = self.listbox.curselection()

    def buttonClick(self):
        '''
        Takes the index values from self.selection and 
        returns a list of the school id's from the arg's id attribute valuse that were passed in when constructing the DialogWin
        '''
        self.destroy()
        self.returnlist = []
        if type(self.selection) == tuple:
            if len(self.selection) in range(1, 5):
                for i in self.selection:
                    self.returnlist.append(self.schools_list[i][1])

            elif len(self.selection) > 4:
                info = "More than 4 choices selected, only the first 4 colleges will be shown"
                tkmb.showinfo("Number of choices", info)
                for i in self.selection[:4]:
                    self.returnlist.append(self.schools_list[i][1])

            return self.returnlist
        return


class DisplayWin(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.title("School Details")
        self.focus_set()
        self.TextArea = tk.Text(self, height=5, width=110)
        for arg in args:
            for argv in arg:
                line_str = str(argv['school.name']) + ": enrollment = " + \
                    str(argv['latest.student.enrollment.all']) + " tuition = " + \
                    str(argv['latest.cost.tuition.in_state']) + " tech degree = " + \
                    str(round((argv['latest.academics.program_percentage.computer'] +
                               argv['latest.academics.program_percentage.engineering']) * 100, 2)) + '%'

                self.TextArea.insert(tk.INSERT, line_str + '\n')

        self.TextArea.grid()
        btn = tk.Button(self, text='SAVE',
                        command=self._file_dialog).grid()

    def _file_dialog(self):
        '''
        This function opens a window to choose a directory to save 
        a text file with the school information
        '''
        # The initial directory of the filedialog window is set to the user's current directory.
        chosenpath = tk.filedialog.askdirectory(initialdir='.')
        print("Working directory:", chosenpath)

        file_w_path_to_write = os.path.join(chosenpath, "colleges.txt")
        print(file_w_path_to_write)
        lines_to_write = self.TextArea.get("1.0", tk.END)
        print(lines_to_write)
        with open(file_w_path_to_write, 'w') as f:
            f.write(lines_to_write)
            f.close()
        tkmb.showinfo(
            'Save', 'Your search result is saved in colleges.txt in ' + chosenpath)
        self.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
