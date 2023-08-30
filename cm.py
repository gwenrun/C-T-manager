import sys
import sqlite3
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLineEdit, QLabel, QFileDialog, QMessageBox
from PyQt5.QtGui import QClipboard, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize, QFile, QTextStream, QThread
import resources
import breeze_resources
import os, random, subprocess, time



class SubProcessThread(QThread):
    def __init__(self, clewd_path):
        super(SubProcessThread, self).__init__()
        self.clewd_path = clewd_path
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(['node', self.clewd_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            count_200 = 0
            error_found = False
            capabilities_found = False
            start_time = time.time()  # Record the start time

            while not (count_200 >= 5 or error_found):
                if self.process is None:
                    break

                output_line_bytes = self.process.stdout.readline()
                if not output_line_bytes:
                    break

                output_line = output_line_bytes.decode('utf-8')  # Convert bytes to string
                print(output_line, end='')  # Print the subprocess output
                
                if "200!" in output_line:
                    count_200 += 1
                
                if "Error" in output_line:
                    error_found = True
                
                if "capabilities" in output_line:
                    capabilities_found = True
                
                if not capabilities_found and time.time() - start_time > 3:
                    break

            # Terminate the subprocess
            print("count: ", count_200, "error found: ", error_found, "capabilities found: ", capabilities_found, "time elapsed: ", time.time()- start_time)
            if self.process is not None:
                self.process.terminate()
                self.process.wait()
        except Exception as e:
            print("Error occurred: ", e)
            if self.process:
                self.process.terminate()
                self.process = None

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
class CookieManager(QWidget):
    def __init__(self):
        super().__init__()
        self.listWidget = QApplication.instance()
        

        self.setWindowIcon(QIcon(':logo'))
        

        # Set window title with a cookie emoji
        self.setWindowTitle(' My Cookie Manager')

        # Main layout
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        # Top layout for list and input
        topLayout = QVBoxLayout()
        mainLayout.addLayout(topLayout)

        # Bottom layout for buttons and info
        bottomLayout = QHBoxLayout()
        mainLayout.addLayout(bottomLayout)

        # Left layout for info
        leftLayout = QVBoxLayout()
        bottomLayout.addLayout(leftLayout)

        # Right layout for buttons
        rightLayout = QVBoxLayout()
        bottomLayout.addLayout(rightLayout)

        # Widgets
        self.cookieDisplay = QLabel("Current JS Cookie:")
        self.lastUsedLabel = QLabel("Last Used: -")  # Added label for last used date
        self.copyMessageLabel = QLabel("")
        self.cookieList = QListWidget()
        self.cookieInput = QLineEdit()
        self.cookieDisplay.setFixedWidth(200)
        self.cookieDisplay.setFixedHeight(200)
        self.cookieDisplay.setWordWrap(True)

        # Add widgets to layout
        topLayout.addWidget(self.cookieList)
        topLayout.addWidget(self.cookieInput)
        leftLayout.addWidget(self.cookieDisplay)
        leftLayout.addWidget(self.lastUsedLabel)  # Added last used date label
        leftLayout.addWidget(self.copyMessageLabel)
        # Buttons
        addButton = QPushButton("Add")
        removeButton = QPushButton("Remove")
        copyButton = QPushButton("Copy")
        importButton = QPushButton("Import")
        selectFileButton = QPushButton("Select JS File")
        insertToFileButton = QPushButton("Insert to JS File")
        self.darkModeButton = QPushButton('Toggle Dark Mode')
        self.darkModeButton.clicked.connect(self.toggleDarkMode)
        self.clewd_button = QPushButton("Off", self)
        self.clewd_button.clicked.connect(self.toggle_clewd)


        rightLayout.addWidget(addButton)
        rightLayout.addWidget(removeButton)
        rightLayout.addWidget(copyButton)
        rightLayout.addWidget(importButton)
        rightLayout.addWidget(selectFileButton)
        rightLayout.addWidget(insertToFileButton)
        topLayout.addWidget(self.darkModeButton)
        rightLayout.addWidget(self.clewd_button)
        
        # Define the Shuffler button
        self.shufflerButton = QPushButton("Shuffler")
        self.shufflerButton.setStyleSheet('QPushButton {background-color: red;}')
        # QTimer Object for shuffle function
        self.shuffleTimer = QTimer()
        self.shuffleTimer.setInterval(1*1000)  # Set interval to 30 seconds
        self.shuffleTimer.timeout.connect(self.timerEvent)
        # Connect the Shuffler button to start or stop the operation
        self.shufflerButton.clicked.connect(self.toggleShuffle)
        self.initTime = 30 # The time your timer starts from
        self.remainingTime = self.initTime
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTimerButton)
        # Add it to the layout
        rightLayout.addWidget(self.shufflerButton)
        
        # Step 1: Create a new QPushButton and add it to your layout
        exportButton = QPushButton("Export")
        rightLayout.addWidget(exportButton)
        # Step 2: Connect the button's clicked signal to a new method
        exportButton.clicked.connect(self.exportCookies)
        # Connect to the SQLite database (it will be created if it doesn't exist)
        self.conn = sqlite3.connect('cookies.db')

        # Create a cursor object
        self.c = self.conn.cursor()

                    # Create table
        self.c.executescript('''
            CREATE TABLE IF NOT EXISTS cookies
            (id INTEGER PRIMARY KEY,
            value TEXT NOT NULL UNIQUE,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            
            CREATE TRIGGER IF NOT EXISTS prevent_empty_insert
            BEFORE INSERT ON cookies
            FOR EACH ROW
            BEGIN
                DELETE FROM cookies WHERE value = "";
            END;
            
            CREATE TRIGGER IF NOT EXISTS replace_cookie
            BEFORE INSERT ON cookies
            FOR EACH ROW
            BEGIN
                DELETE FROM cookies WHERE value = NEW.value;
            END;
        ''')
        self.conn.commit()

        # Load cookies from the database
        self.loadCookies()

        # Connect the buttons to the functions
        addButton.clicked.connect(self.addCookie)
        removeButton.clicked.connect(self.removeCookie)
        copyButton.clicked.connect(self.copyCookie)
        importButton.clicked.connect(self.importCookies)
        selectFileButton.clicked.connect(self.selectJSFile)
        insertToFileButton.clicked.connect(self.insertToJSFile)

        # Connect the list widget to the function
        self.cookieList.itemClicked.connect(self.updateLastUsedLabel)

    def loadCookies(self):
        # Clear the list widget
        self.cookieList.clear()

        # Get all cookies from the database, sorted by last used timestamp in descending order
        self.c.execute("SELECT value FROM cookies ORDER BY last_used ASC")
        cookies = self.c.fetchall()
        


        # Add cookies to the list widget and store the last cookie value
        self.last_cookie_value = None
        for cookie in cookies:
            self.cookieList.addItem(cookie[0])
            self.last_cookie_value = cookie[0]
    def fetchCookieValues(self):
        # Get all cookies from the database, sorted by last used timestamp in descending order
        self.c.execute("SELECT value FROM cookies ORDER BY last_used ASC")
        cookies = self.c.fetchall()

        # Create a list of cookie values
        cookie_values = [cookie[0] for cookie in cookies]

        # Shuffle the cookie values
        random.shuffle(cookie_values)

        return cookie_values

    def addCookie(self):
        # Get the cookie value from the input field
        cookie = self.cookieInput.text()

        # Insert the cookie into the database
        self.c.execute("INSERT INTO cookies (value) VALUES (?)", (cookie,))

        # Save (commit) the changes
        self.conn.commit()

        # Clear the input field
        self.cookieInput.clear()

        # Reload the cookies in the list widget
        self.loadCookies()

    def removeCookie(self):
                # Ask for confirmation before removing the cookie
        reply = QMessageBox.question(self, 'Confirmation', "Are you sure you want to remove the cookie?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        # Get the selected cookie from the list widget
        selectedCookie = self.cookieList.currentItem()

        if selectedCookie is not None:
            # Get the value of the selected cookie
            cookieValue = selectedCookie.text()

            # Remove the cookie from the database
            self.c.execute("DELETE FROM cookies WHERE value = ?", (cookieValue,))

            # Save (commit) the changes
            self.conn.commit()

            # Reload the cookies in the list widget
            self.loadCookies()

    def copyCookie(self):
        # Get the selected cookie from the list widget
        selectedCookie = self.cookieList.currentItem()

        if selectedCookie is not None:
            # Get the value of the selected cookie
            cookieValue = selectedCookie.text()

            # Copy the cookie value to the clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(cookieValue)
            self.copyMessageLabel.setText("Cookie copied successfully")
            # Update the 'last_used' value in the database
            self.c.execute("UPDATE cookies SET last_used = CURRENT_TIMESTAMP WHERE value = ?", (cookieValue,))

            # Save (commit) the changes
            self.conn.commit()

            # Reload the cookies in the list widget
            self.loadCookies()

    def importCookies(self):
        # Open a file dialog to select the JSON file
        dialog = QFileDialog()
        filePaths, _ = dialog.getOpenFileNames(self, "Select JSON Files", "", "JSON Files (*.json)")
        for filePath in filePaths:
         if filePath:
            # Load the cookies from the JSON file
            with open(filePath) as file:
                data = json.load(file)

            if "cookies" in data:
                cookieList = data["cookies"]

                # Insert the cookies into the database
                for cookie in cookieList:
                    self.c.execute("INSERT INTO cookies (value) VALUES (?)", (cookie,))

                # Save (commit) the changes
                self.conn.commit()

                # Reload the cookies in the list widget
                self.loadCookies()

    def selectJSFile(self):
        # Open a file dialog to select the JavaScript file
        dialog = QFileDialog()
        filePath, _ = dialog.getOpenFileName(self, "Select JavaScript File", "", "JavaScript Files (*.js)")

        if filePath:
            # Read the JavaScript file
            with open(filePath) as file:
                javascript = file.read()

            # Extract the cookie value from the JavaScript file
            cookieValue = javascript.split('"Cookie": "')[1].split('"')[0]

            # Update the display with the cookie value and file name
            self.cookieDisplay.setText(f"Current JS Cookie:\n{cookieValue}")
            self.cookieDisplay.setToolTip(f"File: {filePath}")
            self.currentJSFile = filePath

    def insertToJSFile(self):
     # Get the selected cookie from the list widget
       selectedCookie = self.cookieList.currentItem()

       if selectedCookie is not None:
        # Get the value of the selected cookie
           cookieValue = selectedCookie.text()
                   # Update the last used value in the database
           self.c.execute("UPDATE cookies SET last_used = CURRENT_TIMESTAMP WHERE value = ?", (selectedCookie.text(),))
           self.conn.commit()
           self.loadCookies()

           if hasattr(self, 'currentJSFile'):
            # Read the JavaScript file
            with open(self.currentJSFile) as file:
                javascript = file.read()

            # Modify the JavaScript file to replace the cookie value
            start = javascript.find('"Cookie": "') + len('"Cookie": "')
            end = javascript.find('"', start)
            modifiedJS = javascript[:start] + cookieValue + javascript[end:]

            # Write the modified JavaScript file
            with open(self.currentJSFile, "w") as file:
                file.write(modifiedJS)
                # Update the cookie display with the new cookie value
            self.cookieDisplay.setText(f"Current JS Cookie:\n{cookieValue}")
                        # Update the 'last_used' value in the database
            self.copyMessageLabel.setText("Inserted to JS file")
            self.c.execute("UPDATE cookies SET last_used = CURRENT_TIMESTAMP WHERE value = ?", (cookieValue,))

    def updateLastUsedLabel(self, item):
        # Get the value of the selected cookie
        cookieValue = item.text()

        # Update the last used label with the timestamp of the selected cookie
        self.c.execute("SELECT last_used FROM cookies WHERE value = ?", (cookieValue,))
        
        
        lastUsed = self.c.fetchone()[0]
        self.c.execute("SELECT last_used FROM cookies WHERE value = ?", (self.last_cookie_value,))
        last_used_timestamp = self.c.fetchone()[0]
        self.lastUsedLabel.setText(f"Last Used: {lastUsed}")
        self.copyMessageLabel.setText(f"Last used cookie: {self.truncate_cookie(self.last_cookie_value)}, last used at: {last_used_timestamp}")
     
        

        # Step 3: Define the new method
    def exportCookies(self):
     # Fetch all cookies from the database
       self.c.execute("SELECT value FROM cookies")
       cookies = self.c.fetchall()

      # Convert the list of tuples to a list of strings
       cookies = [cookie[0] for cookie in cookies]

       # Convert the list to JSON
       cookies_json = json.dumps({"cookies": cookies})

        # Open a file dialog to select the JSON file
       dialog = QFileDialog()
       filePath, _ = dialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json)")
     
       if filePath:
        # Write the JSON to the file
          with open(filePath, 'w') as file:
            file.write(cookies_json)
    def insertFromTopToJS(self):
       if hasattr(self, 'currentJSFile'):
        # Get the first cookie from the list widget
           firstCookie = self.cookieList.item(0)

           
            # Get the value of the first cookie
           cookieValue = firstCookie.text()
                               # Update the last used value in the database
           self.c.execute("UPDATE cookies SET last_used = CURRENT_TIMESTAMP WHERE value = ?", (firstCookie.text(),))
           self.conn.commit()
           self.loadCookies()
           
            # Read the JavaScript file
           with open(self.currentJSFile) as file:
                javascript = file.read()

            # Modify the JavaScript file to replace the cookie value
           start = javascript.find('"Cookie": "') + len('"Cookie": "')
           end = javascript.find('"', start)
           modifiedJS = javascript[:start] + cookieValue + javascript[end:]

            # Write the modified JavaScript file
           with open(self.currentJSFile, "w") as file:
            file.write(modifiedJS)
                # Update the cookie display with the new cookie value
            self.cookieDisplay.setText(f"Current JS Cookie:\n{cookieValue}")
                        # Update the 'last_used' value in the database
            self.c.execute("UPDATE cookies SET last_used = CURRENT_TIMESTAMP WHERE value = ?", (cookieValue,))
            self.copyMessageLabel.setText("Inserted to JS file")

    def timerEvent(self):
      self.remainingTime -= 1 
      if self.remainingTime <= 0:  
          self.remainingTime = self.initTime  # or whatever you want it to be at the end of the time.
          self.insertFromTopToJS()

    def updateTimerButton(self): 
      self.shufflerButton.setText(f'Shuffle ({self.remainingTime})')       
    def toggleShuffle(self):
        if self.shuffleTimer.isActive():
            self.shuffleTimer.stop()
            self.timer.stop()
            self.shufflerButton.setStyleSheet('QPushButton {background-color: red;}')
            self.shufflerButton.setText('Shuffle')
        else:
            self.shuffleTimer.start()
            self.timer.start(1000)
            self.shufflerButton.setStyleSheet('QPushButton {background-color: green;}')
            self.shufflerButton.setText(f'Shuffle ({self.remainingTime})') 
    def truncate_cookie(self, cookie):
        if len(cookie) > 40:  # Change this number to the maximum length you want
            return cookie[:20] + '...' + cookie[-20:]  # Change these numbers to control how many characters to show at the beginning and end
        else:
            return cookie
    def toggleDarkMode(self):
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("No Qt Application found.")
        if self.darkModeButton.text() == 'Toggle Dark Mode':
            file = QFile(":/dark/stylesheet.qss")
            self.setStyleSheet("")
            self.darkModeButton.setText('Toggle Light Mode')
        else:
            file = QFile(":/light/stylesheet.qss")
            self.setStyleSheet("background-image: url(:/background);")
            self.darkModeButton.setText('Toggle Dark Mode')
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())

        
    def toggle_clewd(self):
        print("toggle_clewd method called")
        if self.clewd_button.text() == "Off":
            if not hasattr(self, 'clewd_path') or not self.clewd_path:
                self.clewd_path, _ = QFileDialog.getOpenFileName(self, "Open clewd.js", "", "JavaScript Files (*.js)")
            
            if self.clewd_path:
                self.process_thread = SubProcessThread(self.clewd_path)
                self.process_thread.start()
                self.clewd_button.setText("On")
                print("Button text set to On")
        else:
            if self.process_thread and self.process_thread.isRunning():
                self.process_thread.stop()
                print("SubProcessThread stopped")
                self.process_thread = None
                self.clewd_button.setText("Off")
                print("Button text set to Off")
            else:
                print("SubProcessThread already stopped")
                self.process_thread = None
                self.clewd_button.setText("Off")
                print("Button text set to Off")
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    cookieManager = CookieManager()
    cookieManager.toggleDarkMode()
    cookieManager.show()
    sys.exit(app.exec_())
