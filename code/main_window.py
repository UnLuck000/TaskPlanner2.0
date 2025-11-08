import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QSystemTrayIcon, QMenu, QMessageBox, QComboBox
)
from PyQt6.QtGui import QIcon, QAction
from second_window import SecondWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.w = None
        self.db_path = os.path.join(os.path.dirname(__file__), 'tasks.db')
        self.tray_icon = None
        self.initUI()
        self.init_tray()

        self.w = SecondWindow(db_path=self.db_path)
        self.w.hide()

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Планировщик задач")
        self.resize(800, 260)

        gb = QGroupBox()
        gb_layout = QFormLayout()

        self.title = QLineEdit()
        self.title.setPlaceholderText("Краткий заголовок, например: Купить продукты")
        self.task = QLineEdit()
        self.task.setPlaceholderText("Описание задачи")
        self.until = QLineEdit()
        self.until.setPlaceholderText("Дата дедлайна (например: 2025-11-10)")
        self.alert = QLineEdit()
        self.alert.setPlaceholderText("Дата и время оповещения (например: 2025-11-09)")

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Низкий", "Средний", "Высокий"])

        self.status = 'В работе'

        gb_layout.addRow(QLabel("Заголовок"), self.title)
        gb_layout.addRow(QLabel("Задача"), self.task)
        gb_layout.addRow(QLabel("Дата дедлайна"), self.until)
        gb_layout.addRow(QLabel("Оповещение (дата)"), self.alert)
        gb_layout.addRow(QLabel("Приоритет"), self.priority_combo)
        gb.setLayout(gb_layout)

        button_add = QPushButton("Добавить")
        button_all = QPushButton("Все задачи")
        self.button_stop = QPushButton("Stop")

        button_add.clicked.connect(self.on_add)
        button_all.clicked.connect(self.show_new_window)
        self.button_stop.clicked.connect(self.full_exit)

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(button_add)
        layout_buttons.addWidget(button_all)
        layout_buttons.addStretch()
        layout_buttons.addWidget(self.button_stop)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(gb)
        main_layout.addLayout(layout_buttons)
        self.setLayout(main_layout)

        # Мини-дизайн
        self.setStyleSheet("""
        QWidget { background: #170909; 
                  font-family: Arial; }
        QLabel { color: white; }
        QGroupBox { font-weight: bold; 
                    color: white; }
        QLineEdit, QComboBox {
            background: #140303; color: white;
            padding: 6px; border: 1px solid #cfd8e3; border-radius: 4px;
            }
        QPushButton {
            background: #3c0a0a; color: white; border-radius: 6px; padding: 6px 12px;
            }
        QPushButton:hover { background: #601010; }
        """)

    def init_tray(self):
        """Инициализация системного трея"""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Планировщик задач")

        tray_menu = QMenu()
        show_action = QAction("Открыть", self)
        stop_action = QAction("Закрыть", self)
        show_action.triggered.connect(self.show_window_from_tray)
        stop_action.triggered.connect(self.full_exit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(stop_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """Открытие программы через системный трей дабл кликом"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_from_tray()

    def show_window_from_tray(self):
        """Открытие программы через системный трей"""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def show_new_window(self):
        """Открытие second_window"""
        if not self.w:
            self.w = SecondWindow(db_path=self.db_path, tray=self.tray_icon)
        self.w.show()
        self.w.raise_()
        self.w.activateWindow()

    def is_valid_date(self, date_str):
        """Проверка на валидность даты"""
        if not date_str:
            return True
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def on_add(self):
        """Добавление новой задачи"""
        title = self.title.text().strip()
        task = self.task.text().strip()
        until = self.until.text().strip()
        alert = self.alert.text().strip()
        priority = self.priority_combo.currentText()

        if not self.is_valid_date(until) or not self.is_valid_date(alert):
            QMessageBox.warning(self, "Ошибка формата даты", "Формат даты должен быть: YYYY-MM-DD")
            return

        if not title or not task:
            QMessageBox.warning(self, "Пустые поля", "Введите заголовок и описание задачи.")
            return

        if not self.w:
            self.w = SecondWindow(db_path=self.db_path, tray=self.tray_icon)

        self.w.add_row(title, task, until, alert, self.status, priority)

        self.title.clear()
        self.task.clear()
        self.until.clear()
        self.alert.clear()
        self.priority_combo.setCurrentIndex(1)

    def closeEvent(self, event):
        """Скрытие приложения при нажатии на крестик"""
        event.ignore()
        self.hide()
        self.w.hide()

    def full_exit(self):
        """Полный выход из приложения при нажатии на кнопку Stop"""
        if self.w:
            self.w.close()
        self.tray_icon.hide()
        QApplication.quit()

# Для создания .exe файла
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

db_path = os.path.join(BASE_DIR, 'tasks.db')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())