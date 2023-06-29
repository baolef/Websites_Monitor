import datetime
import sys
import sqlite3
from urllib.request import urlopen

import pyperclip
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import QTimer

import Screen1


class MainCode(QMainWindow, Screen1.Ui_MainWindow):
    def __init__(self):
        self.timer = QTimer()
        conn = sqlite3.connect("Database.db")
        c = conn.cursor()
        QMainWindow.__init__(self)
        Screen1.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.Refresh.clicked.connect(self.refresh)
        self.Check_all.clicked.connect(self.check_all)
        self.Add.clicked.connect(self.add)
        self.checkBox.stateChanged.connect(self.auto_check)
        row = ''
        try:
            cursor = c.execute("SELECT *  from Settings")
        except:
            self.database_initialize()
        cursor = c.execute("SELECT *  from Settings")
        row = list(cursor)[0]
        self.address = row[0]
        self.time_interval = row[1] * 60
        self.timeout = row[2]
        conn.close()
        self.Check.clicked.connect(self.check)
        self.checkBox.setText('Auto check (' + str(int(self.time_interval / 60)) + ' min)')
        self.checkBox.adjustSize()
        self.listWidget.itemDoubleClicked.connect(self.list_double_clicked)
        self.listWidget.itemClicked.connect(self.list_clicked)
        self.Delete.clicked.connect(self.list_delete)
        self.listWidget.itemSelectionChanged.connect(self.delete_enable)
        self.Input_dialog = QInputDialog(self.centralwidget)
        self.Url.textChanged.connect(self.add_enable)
        self.Duplicate.clicked.connect(self.duplicate)
        self.Clear.clicked.connect(self.clear)
        self.Message_box = QMessageBox(self.centralwidget)
        self.actionAbout_Author.triggered.connect(self.about_author)
        self.actionAbout.triggered.connect(self.about)
        self.actionHelp.triggered.connect(self.help)
        self.actionSet_time_interval.triggered.connect(self.set_time_interval)
        self.actionSet_timeout_value.triggered.connect(self.set_timeout)
        self.actionRestore_Default_Settings.triggered.connect(self.database_initialize)
        self.websites_list = []
        self.log_list = []
        self.log_text = ''
        self.timer.setInterval(self.time_interval * 1000)
        self.timer.timeout.connect(self.auto_check_helper)
        self.refresh()

    def database_initialize(self):
        conn = sqlite3.connect("Database.db")
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS Settings")
        c.execute('''CREATE TABLE IF NOT EXISTS Settings 
               (ADDRESS           TEXT    NOT NULL,
               TIME_INTERVAL      INT     NOT NULL,
               TIMEOUT            INT);''')
        c.execute('''CREATE TABLE IF NOT EXISTS Websites
               (Website_name           TEXT    NOT NULL);''')
        c.execute("INSERT INTO Settings (ADDRESS, TIME_INTERVAL, TIMEOUT) VALUES ('Websites.txt',5,4)")
        self.time_interval = 5 * 60
        self.checkBox.setText('Auto check (' + str(int(self.time_interval / 60)) + ' min)')
        self.checkBox.adjustSize()
        self.timer.setInterval(self.time_interval * 1000)
        self.timeout = 4
        conn.commit()
        conn.close()
        self.statusbar.showMessage('Settings initialize successfully', 5000)

    def refresh(self):
        self.listWidget.clear()
        conn = sqlite3.connect('Database.db')
        c = conn.cursor()
        cursor = c.execute("SELECT * from Websites")
        self.websites_list.clear()
        for row in cursor:
            self.websites_list.append(row[0])
            item = QListWidgetItem(row[0])
            item.setToolTip('Double clicked to edit')
            self.listWidget.addItem(item)
        conn.close()
        self.statusbar.showMessage('Refresh successfully', 5000)

    def check_all(self):
        self.Log.clear()
        with open('Log.txt', 'a') as output_file:
            self.progressBar.setMaximum(self.listWidget.count())
            self.progressBar.setValue(0)
            for index in range(0, self.websites_list.__len__()):
                try:
                    url = self.websites_list[index]
                    resp = urlopen(url, timeout=self.timeout)
                    code = resp.getcode()
                    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if code == 200:
                        output_file.write('Time: ' + time + '\n')
                        output_file.write('Url: ' + url + '\n')
                        self.Log.append('Time: ' + time)
                        self.Log.append('Url: ' + url)
                        output_file.write('OK' + '\n\n')
                        self.Log.append('OK' + '\n')
                    else:
                        raise Exception(code)
                except Exception as e:
                    output_file.write('Time: ' + time + '\n')
                    output_file.write('Url: ' + url + '\n')
                    self.Log.append('Time: ' + time)
                    self.Log.append('Url: ' + url)
                    output_file.write('Error: ' + str(e) + '\n\n')
                    self.Log.append('Error: ' + str(e) + '\n')
                self.progressBar.setValue(index + 1)
        self.statusbar.showMessage('Check all successfully', 5000)

    def add(self):
        self.url_correct()
        if self.Url.text() != '':
            conn = sqlite3.connect('Database.db')
            c = conn.cursor()
            cmd = "INSERT INTO Websites (Website_name) VALUES ('" + self.Url.text() + "')"
            c.execute(cmd)
            conn.commit()
            conn.close()
            self.statusbar.showMessage('Add successfully', 5000)
        self.refresh()
        self.add_enable()

    def auto_check(self):
        if self.checkBox.checkState():
            self.auto_check_helper()
            self.timer.start()
        else:
            self.timer.stop()
            self.Check_time.setText('Next check time: None')

    def auto_check_helper(self):
        self.check_all()
        next_time = datetime.datetime.now() + datetime.timedelta(seconds=self.time_interval)
        self.Check_time.setText('Next check time: ' + next_time.strftime('%Y-%m-%d %H:%M:%S'))

    def set_time_interval(self):
        result, ok = self.Input_dialog.getInt(self, 'Set time interval', 'Time Interval (min):',
                                              int(self.time_interval / 60), min=1)
        if ok:
            self.time_interval = result * 60
            conn = sqlite3.connect('Database.db')
            c = conn.cursor()
            c.execute("UPDATE Settings set TIME_INTERVAL = " + str(result) + " where 1=1")
            conn.commit()
            conn.close()
            self.checkBox.setText('Auto check (' + str(int(self.time_interval / 60)) + ' min)')
            self.checkBox.adjustSize()
            self.timer.setInterval(self.time_interval * 1000)

    def set_timeout(self):
        result, ok = self.Input_dialog.getInt(self, 'Set time out value', 'Timeout value (sec):',
                                              int(self.timeout), min=1)
        if ok:
            self.timeout = result
            conn = sqlite3.connect('Database.db')
            c = conn.cursor()
            c.execute("UPDATE Settings set TIMEOUT = " + str(result) + " where 1=1")
            conn.commit()
            conn.close()

    def url_correct(self):
        url = self.Url.text()
        if not url.startswith('https://') and not url.startswith('http://') and url != '':
            self.Url.setText('http://' + url)

    def check(self):
        self.url_correct()
        url = self.Url.text()
        try:
            resp = urlopen(url, timeout=self.timeout)
            code = resp.getcode()
            if code != 200:
                raise Exception(code)
        except Exception as e:
            self.Url_status.setText('Error: ' + str(e))
            self.Url_status.adjustSize()
        else:
            self.Url_status.setText('OK')
            self.Url_status.adjustSize()

    def list_double_clicked(self):
        text = self.listWidget.currentItem().text()
        result, ok = self.Input_dialog.getText(self, 'Rewrite url', 'Please enter new url here: ', text=text)
        if ok:
            conn = sqlite3.connect('Database.db')
            c = conn.cursor()
            c.execute("UPDATE Websites set Website_name = '" + result + "' where Website_name = '" + text + "'")
            conn.commit()
            conn.close()
            self.statusbar.showMessage('Edit successfully', 5000)
        self.refresh()

    def list_clicked(self):
        self.Url.setText(self.listWidget.currentItem().text())

    def list_delete(self):
        text = self.listWidget.currentItem().text()
        conn = sqlite3.connect('Database.db')
        c = conn.cursor()
        c.execute("DELETE from Websites where Website_name='" + text + "'")
        conn.commit()
        conn.close()
        self.statusbar.showMessage('Delete successfully', 5000)
        self.refresh()

    def delete_enable(self):
        self.Delete.setEnabled(self.listWidget.selectedItems().__len__() != 0)

    def add_enable(self):
        if self.Url.text() == '':
            self.Check.setEnabled(False)
            self.Add.setEnabled(False)
        else:
            self.Check.setEnabled(True)
            self.Add.setEnabled(self.Url.text() not in self.websites_list)

    def duplicate(self):
        pyperclip.copy(self.Log.toPlainText())
        self.statusbar.showMessage('Copy successfully', 5000)

    def clear(self):
        self.Log.clear()

    def about(self):
        self.Message_box.about(self, "About Websites Monitor",
                               "This is a program developed by Fang Baole to automatically check whether the "
                               "connection every website in the list is good. If not, the error will be recorded in "
                               "the error log.\n\nVersion: V3.0\nUpdate time: 2020-1-15")

    def about_author(self):
        self.Message_box.about(self, "About Author", "中远海运科技股份有限公司 云数据中心 方宝乐\n联系方式：fbl718@sjtu.edu.cn")

    def help(self):
        self.Message_box.about(self, "Help",
                               '1. When the program is launched, website list is automatically refreshed.\n2. Click '
                               '"Refresh" button to refresh the website list.\n3. Click "Check all" button to check '
                               'whether all the connections of all the websites in the website list are good. If '
                               'there are any errors, they will be recorded in the error log and in the file '
                               '"Log.txt".\n4. Check the checkbox to automatically check the status of all websites '
                               'in the website list every time interval.\n5. Click "Add" button to add a new website to the '
                               'website list. It should be non-empty and different from existing websites.\n6. Click '
                               '"Check" button to check the status of the website inputted in the textbox.\n7. Click '
                               'an element in the website list to put it in the textbox.\n8. Double click an element '
                               'in the website list to edit its url.\n9. Click "Delete" button to delete the '
                               'selected website in the website list.\n10. Click "Copy" button to copy the error log '
                               'to the clipboard.\n11. Click "Clear" button to clear the error log. Be aware that it '
                               'will not delete anything in the file "Log.txt".\n12. You may change the parameters in Settings.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    md = MainCode()
    md.show()
    sys.exit(app.exec_())
