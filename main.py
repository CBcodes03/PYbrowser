from PyQt5.QtCore import *
import re
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import datetime
from urllib.parse import urlparse
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon
import os
import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

SEARCH_ENGINE=None
def extract_domain_label(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain
dark_theme = """
    QMainWindow {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    QTabWidget::pane {
        border: 1px solid #444444;
    }
    QTabBar::tab {
        background-color: #3E3E3E;
        color: #FFFFFF;
        padding: 5px;
    }
    QTabBar::tab:selected {
        background-color: #555555;
    }
    QLineEdit {
        background-color: #555555;
        color: white;
        border: 1px solid #444444;
    }
    QToolBar {
        background-color: #3E3E3E;
    }
    QPushButton {
        background-color: #444444;
        color: white;
        border-radius: 5px;
        padding: 5px;
    }
"""

light_theme = """
    QMainWindow {
        background-color: #F0F0F0;
        color: #000000;
    }
    QTabWidget::pane {
        border: 1px solid #CCCCCC;
    }
    QTabBar::tab {
        background-color: #E0E0E0;
        color: #000000;
        padding: 5px;
    }
    QTabBar::tab:selected {
        background-color: #CCCCCC;
    }
    QLineEdit {
        background-color: #FFFFFF;
        color: black;
        border: 1px solid #CCCCCC;
    }
    QToolBar {
        background-color: #F0F0F0;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: black;
        border-radius: 5px;
        padding: 5px;
    }
"""
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        ad_blocklist = [
            "doubleclick.net",
            "ads.google.com",
            "advertising.com",
            "adservice.google.com",
            "pagead2.googlesyndication.com",
            "ad.yieldmo.com",
            "adroll.com",
            "ads.mopub.com",
            "analytics.twitter.com",
            "ads.t.co",
            "googlesyndication.com"
        ]
        for pattern in ad_blocklist:
            if pattern in info.requestUrl().toString():
                info.block(True)
                print(f"Blocked: {info.requestUrl()}")
                return

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.ad_block_interceptor = AdBlockInterceptor()
        QWebEngineProfile.defaultProfile().setRequestInterceptor(self.ad_block_interceptor)
        self.setWindowTitle("PYbrowser")
        self.setWindowIcon(QIcon('images/icon.png'))
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        self.add_new_tab()

        self.setCentralWidget(self.tabs)

        # Creating a status bar object
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Creating QToolBar for navigation
        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)

        # Adding actions to the tool bar
        back_btn = QAction("Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.setIcon(QIcon("images/arrow.png"))
        back_btn.triggered.connect(self.back)
        navtb.addAction(back_btn)

        next_btn = QAction("Forward", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.setIcon(QIcon("images/right-arrow.png"))
        next_btn.triggered.connect(self.forward)
        navtb.addAction(next_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.setIcon(QIcon("images/refresh.png"))
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(self.reload)
        navtb.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.setIcon(QIcon("images/home.png"))
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        stop_btn = QAction("Stop", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.setIcon(QIcon("images/close.png"))
        stop_btn.triggered.connect(self.stop)
        navtb.addAction(stop_btn)

        download_btn = QAction("Download Page", self)
        download_btn.setStatusTip("Download the current page")
        download_btn.triggered.connect(self.download_page)
        

        bookmark_btn = QAction("Bookmark", self)
        bookmark_btn.setStatusTip("Bookmark the current page")
        bookmark_btn.setIcon(QIcon("images/star.png"))
        bookmark_btn.triggered.connect(self.add_bookmark)
        navtb.addAction(bookmark_btn)

        # Add new tab action
        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.setStatusTip("Open a new tab")
        new_tab_btn.setIcon(QIcon("images/tab.png"))
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        navtb.addAction(new_tab_btn)

        # Theme Toggle Button
        self.is_dark_mode = True
        theme_btn = QAction("Toggle Theme", self)
        theme_btn.setIcon(QIcon("images/themes.png"))
        theme_btn.triggered.connect(self.toggle_theme)
        navtb.addAction(theme_btn)
        self.setStyleSheet("background-color: #2c3e50;")
        self.apply_dark_theme()

        # Create a Settings Dropdown
        settings_menu = QMenu("Settings", self)
        navtb.addAction(settings_menu.menuAction())
        settings_menu.addAction("Show Bookmarks", self.show_bookmarks)
        settings_menu.setIcon(QIcon("images/settings.png"))
        settings_menu.addAction("History", self.show_history)
        settings_menu.addAction(download_btn)

        self.show()

    def add_new_tab(self, url=None, label=""):
        # Create a new QWebEngineView
        new_tab = QWebEngineView()

        if isinstance(url, str) and url:
            label = extract_domain_label(url)
            new_tab.setUrl(QUrl(url))
        else:
            label = "home"
            new_tab.setUrl(QUrl("file:///home/chirag/Desktop/PYbrowser/index.html"))

        # Connect the urlChanged signal to update the URL bar and title
        new_tab.urlChanged.connect(lambda q: self.update_urlbar(q, new_tab))
        new_tab.urlChanged.connect(self.add_to_history)
        new_tab.urlChanged.connect(self.handle_url_change)

        # Create a new tab in the tab widget
        index = self.tabs.addTab(new_tab, label)
        self.tabs.setCurrentIndex(index)  # Switch to the new tab

        # Set the initial tab's title
        self.tabs.setTabText(index, label)

    def update_urlbar(self, q, tab):
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)
        self.update_tab_title(q)

    def update_tab_title(self, q):
        current_index = self.tabs.currentIndex()
        if current_index != -1:  # Ensure there's a valid index
            new_label = extract_domain_label(q.toString())  # Get the domain label
            # Update the tab's title
            self.tabs.setTabText(current_index, new_label)

    def handle_url_change(self, qurl):
        current_tab = self.tabs.currentWidget()  # Get the current tab
        current_index = self.tabs.currentIndex()  # Get the current tab's index

        # Check if the URL is the default one (home page)
        if qurl.toString() == "file:///home/chirag/Desktop/PYbrowser/index.html":
            label = "home"
        else:
            url_string = qurl.toString()
            label = re.search(r'[^/]+$', url_string)
            print(label)
        self.tabs.setTabText(current_index, str(label.group()))


    def close_current_tab(self, index):
        if self.tabs.count() > 1:       
            self.tabs.removeTab(index)

    def back(self):
        current_tab = self.tabs.currentWidget()
        current_tab.back()

    def forward(self):
        current_tab = self.tabs.currentWidget()
        current_tab.forward()

    def reload(self):
        current_tab = self.tabs.currentWidget()
        current_tab.reload()


    def navigate_home(self):
        current_tab = self.tabs.currentWidget()
        current_index = self.tabs.currentIndex()
        current_tab.setUrl(QUrl("file:///home/chirag/Desktop/PYbrowser/index.html"))
        self.tabs.setTabText(current_index, "home")
        


    def stop(self):
        current_tab = self.tabs.currentWidget()  # Get the current active tab (QWebEngineView)
        current_tab.stop()  # Stop loading the current page

    def navigate_to_url(self,link=None):
        if link != None:
            current_tab = self.tabs.currentWidget()
            current_index = self.tabs.currentIndex()
            label=extract_domain_label(link)
            current_tab.setUrl(QUrl(link))
            self.tabs.setTabText(current_index, label)
        else:
            input_text = self.urlbar.text().strip()
            current_tab = self.tabs.currentWidget()
            current_index = self.tabs.currentIndex()
            if input_text:
                if input_text.startswith("http://") or input_text.startswith("https://"):
                    q = QUrl(input_text)
                    label=f"{input_text}"
                else:
                    search_url = f"https://www.google.com/search?q={input_text}"
                    q = QUrl(search_url)
                    label=f"{input_text}"
                current_tab.setUrl(q)
                self.tabs.setTabText(current_index, label)

    def update_urlbar(self, q):
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def download_page(self):
        current_tab = self.tabs.currentWidget()
        current_url = current_tab.url().toString()
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "HTML Files (*.html);;All Files (*)", options=options)

        if file_name:
            current_tab.page().toHtml(lambda html: self.save_html(file_name, html))

    def save_html(self, file_name, html):
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(html)

    def add_bookmark(self):
        current_url = self.tabs.currentWidget().url().toString()
        title = self.tabs.currentWidget().page().title()

        # Append the new bookmark to the bookmarks.txt file
        bookmark_file = "bookmarks.txt"
        with open(bookmark_file, 'a') as f:
            f.write(f"{title} \n {current_url}")  # Write the title and URL separated by '|'
        
        QMessageBox.information(self, "Bookmark Added", f"'{title}' has been bookmarked.")

    def load_bookmarks(self):
        # Load bookmarks from the bookmarks.txt file
        bookmark_file = "bookmarks.txt"
        self.bookmarks = []

        if os.path.exists(bookmark_file):
            with open(bookmark_file, 'r') as f:
                for line in f:
                    if line.strip():  # Ignore empty lines
                        title, url = line.strip().split('\n')
                        self.bookmarks.append((title, url))

    def show_bookmarks(self):
        self.load_bookmarks()  # Load bookmarks from file before displaying

        if not self.bookmarks:
            QMessageBox.information(self, "Bookmarks", "No bookmarks added yet.")
            return

        # Create a QDialog to display the bookmarks
        self.bookmark_dialog = QDialog(self)
        self.bookmark_dialog.setWindowTitle("Bookmarks")
        self.bookmark_dialog.setMinimumSize(400, 300)

        # Vertical layout to hold all bookmarks
        layout = QVBoxLayout()

        # Scroll area to make the bookmarks list scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # Add each bookmark as a clickable QLabel with a delete button
        for title, url in self.bookmarks:
            bookmark_layout = QHBoxLayout()  # Horizontal layout to hold the bookmark and delete button

            # Bookmark label with link
            bookmark_label = QLabel(f"<a href='{url}'>{title}</a>")
            bookmark_label.setOpenExternalLinks(False)  # We handle opening the link
            bookmark_label.linkActivated.connect(lambda link=url: self.navigate_to_url(link))

            # Delete button for each bookmark
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, u=url: self.delete_bookmark(u))  # Connect button to delete_bookmark

            bookmark_layout.addWidget(bookmark_label)
            bookmark_layout.addWidget(delete_btn)
            scroll_layout.addLayout(bookmark_layout)

        # Set up scroll area with bookmarks
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the dialog's layout
        layout.addWidget(scroll_area)
        self.bookmark_dialog.setLayout(layout)

        self.bookmark_dialog.exec_()

    def delete_bookmark(self, url):
        # Close the current bookmark dialog before updating the list
        if hasattr(self, 'bookmark_dialog') and self.bookmark_dialog.isVisible():
            self.bookmark_dialog.close()

        # Load current bookmarks
        self.load_bookmarks()

        # Remove the bookmark that matches the URL
        self.bookmarks = [bookmark for bookmark in self.bookmarks if bookmark[1] != url]

        # Rewrite the bookmarks.txt file without the deleted bookmark
        bookmark_file = "bookmarks.txt"
        with open(bookmark_file, 'w') as f:
            for title, bookmark_url in self.bookmarks:
                f.write(f"{title}|{bookmark_url}\n")

        # Show updated bookmarks
        self.show_bookmarks()


    def show_history(self):
        # Close any existing history dialog if it's open
        if hasattr(self, 'history_dialog') and self.history_dialog.isVisible():
            self.history_dialog.close()
            del self.history_dialog  # Ensure it's removed completely

        # Create the dialog before doing anything else
        self.history_dialog = QDialog(self)
        self.history_dialog.setWindowTitle("History")
        self.history_dialog.setMinimumSize(400, 300)

        # Load history from the file
        history_file = "history.txt"
        self.history = []
        
        # Check if history file exists, if not, create it
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                for line in f:
                    if line.strip():  # Avoid empty lines
                        timestamp, title, url = line.strip().split(' | ')
                        self.history.append((timestamp, title, url))
        else:
            open(history_file, 'w').close()  # Create the file if it doesn't exist

        layout = QVBoxLayout()

        # "Clear All" button to clear the entire history
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)

        # Scroll area for history list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        history_container = QWidget()
        history_layout = QVBoxLayout()

        if not self.history:
            QMessageBox.information(self, "History", "No history available.")
        else:
            for timestamp, title, url in self.history:
                history_item_layout = QHBoxLayout()

                # Display title and URL with clickable link
                history_item = QLabel(f"<a href='{url}'>{title}</a> ({timestamp})")
                history_item.setOpenExternalLinks(True)
                history_item_layout.addWidget(history_item)

                # Add "Delete" button for each history entry
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda _, u=url: self.delete_history_item(u))
                history_item_layout.addWidget(delete_btn)

                # Add the item to the history layout
                history_layout.addLayout(history_item_layout)

        history_container.setLayout(history_layout)
        scroll_area.setWidget(history_container)

        layout.addWidget(scroll_area)
        self.history_dialog.setLayout(layout)

        # Show the updated history dialog
        self.history_dialog.show()

        

    def add_to_history(self, q):
        url = q.toString()
        title = self.tabs.currentWidget().page().title()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_file = "history.txt"
        if not self.history or self.history[-1][2] != url:
            self.history.append((timestamp, title, url))
            with open(history_file, 'a') as f:
                f.write(f"{timestamp} | {title} | {url}\n")

    def delete_history_item(self, url_to_delete):
        history_file = "history.txt"
        self.history = [entry for entry in self.history if entry[2] != url_to_delete]
        with open(history_file, 'w') as f:
            for timestamp, title, url in self.history:
                f.write(f"{timestamp} | {title} | {url}\n")
        QMessageBox.information(self, "History Deleted", f"History for URL '{url_to_delete}' has been deleted.")
        self.show_history()

    def clear_history(self):
        history_file = "history.txt"
        open(history_file, 'w').close()
        self.show_history()

    def toggle_theme(self):
        if self.is_dark_mode:
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet(dark_theme)
        self.is_dark_mode = True

    def apply_light_theme(self):
        self.setStyleSheet(light_theme)
        self.is_dark_mode = False
app = QApplication(sys.argv)
app.setApplicationName("PYbrowser")

window = MainWindow()

app.exec()