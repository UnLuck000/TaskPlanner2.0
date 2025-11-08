import sqlite3
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QLineEdit, QLabel, QHeaderView, QComboBox, QTabWidget, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCharts import QChart, QChartView, QPieSeries


class SecondWindow(QWidget):
    def __init__(self, db_path='tasks.db', tray=None):
        super().__init__()
        self.db_path = db_path
        self.tray = tray
        self.conn = None
        self.current_status_filter = "Все"
        self.current_priority_filter = "Все"

        self.init_db()
        self.initUI()
        self.load_tasks()
        self.update_stats()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(10000)

    def init_db(self):
        """Инициализация и создание новой БД(Если её нет)"""
        self.conn = sqlite3.connect(self.db_path)
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            task TEXT NOT NULL,
            until TEXT,
            alert TEXT,
            status TEXT,
            priority TEXT
        )""")
        self.conn.commit()

    def initUI(self):
        """Инициализация интерфейса с вкладками"""
        self.setWindowTitle("Все задачи")
        self.resize(1200, 500)

        self.tabs = QTabWidget()
        self.tab_tasks = QWidget()
        self.tab_stats = QWidget()

        self.tabs.addTab(self.tab_tasks, "Задачи")
        self.tabs.addTab(self.tab_stats, "Статистика")

        self.init_tasks()
        self.init_stats()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Мини-дизайн
        self.setStyleSheet("""
        QWidget { background: #170909; font-family: Arial; }
        QLabel { color: white; }
        QLineEdit, QComboBox {
            background: #140303; color: white;
            border: 1px solid #cfd8e3; border-radius: 4px; padding: 4px;
        }
        QPushButton {
            background: #3c0a0a; color: white; border-radius: 6px; padding: 6px 12px;
        }
        QPushButton:hover { background: #601010; }
        """)

    def init_tasks(self):
        """Инициализация и создание таблицы с задачами"""
        layout = QVBoxLayout()

        self.filter_status = QComboBox()
        self.filter_status.addItems(["Все", "Не начата", "В работе", "Выполнена", "Просрочена", "Отменена"])
        self.filter_status.currentTextChanged.connect(self.on_filter_changed)

        self.filter_priority = QComboBox()
        self.filter_priority.addItems(["Все", "Низкий", "Средний", "Высокий"])
        self.filter_priority.currentTextChanged.connect(self.on_filter_changed)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск по заголовку или описанию...")
        self.search_bar.textChanged.connect(self.load_tasks)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Заголовок', 'Задача', 'До', 'Оповещение', 'Статус', 'Приоритет'])
        header = self.table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        button_edit = QPushButton("Редактировать")
        button_delete = QPushButton("Удалить")
        button_refresh = QPushButton("Обновить")
        button_export = QPushButton("Экспорт в CSV")

        button_edit.clicked.connect(self.edit_selected)
        button_delete.clicked.connect(self.delete_selected)
        button_refresh.clicked.connect(self.load_tasks)
        button_export.clicked.connect(self.export_csv)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Статус:"))
        filter_layout.addWidget(self.filter_status)
        filter_layout.addWidget(QLabel("Приоритет:"))
        filter_layout.addWidget(self.filter_priority)
        filter_layout.addWidget(self.search_bar)
        filter_layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(button_edit)
        buttons_layout.addWidget(button_delete)
        buttons_layout.addWidget(button_refresh)
        buttons_layout.addWidget(button_export)

        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(buttons_layout)

        self.tab_tasks.setLayout(layout)

    def init_stats(self):
        """Инициализация и создание круговой диаграммы(статистики)"""
        layout = QVBoxLayout()

        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(True)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(self.chart_view.renderHints())

        layout.addWidget(self.stats_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.chart_view)

        self.tab_stats.setLayout(layout)

    def load_tasks(self):
        """Загрузка задач с фильтрацией и поиском"""
        self.table.setRowCount(0)
        cur = self.conn.cursor()

        query = "SELECT id, title, task, until, alert, status, priority FROM tasks WHERE 1=1"
        params = []
        if self.current_status_filter != "Все":
            query += " AND status=?"
            params.append(self.current_status_filter)
        if self.current_priority_filter != "Все":
            query += " AND priority=?"
            params.append(self.current_priority_filter)
        if self.search_bar.text().strip():
            query += " AND (title LIKE ? OR task LIKE ?)"
            text = f"%{self.search_bar.text().strip()}%"
            params.extend([text, text])

        query += " ORDER BY id"
        cur.execute(query, params)

        for row_data in cur.fetchall():
            _id, title, task, until, alert, status, priority = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            it0 = QTableWidgetItem(title)
            it0.setData(Qt.ItemDataRole.UserRole, _id)
            self.table.setItem(row, 0, it0)
            self.table.setItem(row, 1, QTableWidgetItem(task))
            self.table.setItem(row, 2, QTableWidgetItem(until or ''))
            self.table.setItem(row, 3, QTableWidgetItem(alert or ''))
            self.table.setItem(row, 4, QTableWidgetItem(status or 'В работе'))
            self.table.setItem(row, 5, QTableWidgetItem(priority or 'Средний'))

        self.update_stats()

    def on_filter_changed(self):
        """Инициализация изменения фильтров"""
        self.current_status_filter = self.filter_status.currentText()
        self.current_priority_filter = self.filter_priority.currentText()
        self.load_tasks()

    def add_row(self, title, task, date1, date2, status, priority):
        """Создание новой задачи(ряда в таблице) с записью в БД"""
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO tasks (title, task, until, alert, status, priority)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, task, date1, date2, status, priority)
        )
        self.conn.commit()
        self.load_tasks()

    def check_until_alert_date(self):
        """Проверка на наличие уведомлений, если есть, вывести на экран, а так же проверка на просроченные задания"""
        today = datetime.now().date()
        cur = self.conn.cursor()
        rows = cur.execute("""SELECT id, title, alert, until, status FROM tasks""").fetchall()
        changed = False

        for _id, title, alert, until, status in rows:
            if alert:
                try:
                    alert_date = datetime.strptime(alert, '%Y-%m-%d').date()
                    if alert_date == today and status not in ('Выполнена', 'Отменена'):
                        QMessageBox.information(self, 'Напоминание', f'Сегодня оповещение по задаче:\n\n«{title}»')
                        cur.execute("""UPDATE tasks SET alert=? WHERE id=?""", ('', _id))
                        changed = True
                except ValueError:
                    pass

            if until:
                try:
                    until_date = datetime.strptime(until, '%Y-%m-%d').date()
                    if until_date < today and status != 'Просрочена':
                        cur.execute("""UPDATE tasks SET status=? WHERE id=?""", ('Просрочена', _id))
                        changed = True
                except ValueError:
                    pass

        if changed:
            self.conn.commit()
            self.load_tasks()

    def export_csv(self):
        """Экспорт всех задач в CSV"""
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как...", "tasks.csv", "CSV Files (*.csv)")
        if not path:
            return
        cur = self.conn.cursor()
        rows = cur.execute("SELECT title, task, until, alert, status, priority FROM tasks").fetchall()
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Заголовок", "Задача", "До", "Оповещение", "Статус", "Приоритет"])
            writer.writerows(rows)
        QMessageBox.information(self, "Экспорт завершён", f"Файл сохранён:\n{path}")

    def update_stats(self):
        """Обновление вкладки статистики"""
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM tasks")
        rows = cur.fetchall()

        total = len(rows)
        if total == 0:
            self.stats_label.setText("Нет задач для отображения статистики")
            self.chart_view.setChart(QChart())
            self.progress.setValue(0)
            return

        status_counts = {}
        for (status,) in rows:
            status_counts[status] = status_counts.get(status, 0) + 1

        done = status_counts.get('Выполнена', 0)
        progress_percent = int(done / total * 100)
        self.progress.setValue(progress_percent)
        self.stats_label.setText(f"Всего задач: {total} | Выполнено: {done} ({progress_percent}%)")

        series = QPieSeries()
        for status, count in status_counts.items():
            series.append(status, count)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Распределение задач по статусам")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.chart_view.setChart(chart)

    def is_valid_date(self, s):
        """Проверка даты на валидность"""
        if not s:
            return True
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def edit_selected(self):
        """Инициализация окна для изменения данных в таблице и БД"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу.")
            return
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать задачу")
        le1 = QLineEdit(self.table.item(row, 0).text())
        le2 = QLineEdit(self.table.item(row, 1).text())
        le3 = QLineEdit(self.table.item(row, 2).text())
        le4 = QLineEdit(self.table.item(row, 3).text())
        le5 = QComboBox()
        statuses = ['Не начата', 'В работе', 'Выполнена', 'Просрочена', 'Отменена']
        le5.addItems(statuses)
        le6 = QComboBox()
        priorities = ['Низкий', 'Средний', 'Высокий']
        le6.addItems(priorities)

        try:
            le5.setCurrentIndex(statuses.index(self.table.item(row, 4).text()))
        except ValueError:
            le5.setCurrentIndex(1)
        try:
            le6.setCurrentIndex(priorities.index(self.table.item(row, 5).text()))
        except ValueError:
            le6.setCurrentIndex(1)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Заголовок"))
        layout.addWidget(le1)
        layout.addWidget(QLabel("Задача"))
        layout.addWidget(le2)
        layout.addWidget(QLabel("До"))
        layout.addWidget(le3)
        layout.addWidget(QLabel("Оповещение"))
        layout.addWidget(le4)
        layout.addWidget(QLabel("Статус"))
        layout.addWidget(le5)
        layout.addWidget(QLabel("Приоритет"))
        layout.addWidget(le6)

        buttons = QHBoxLayout()
        save = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")

        def try_save():
            # валидация(проверка данных на точность)
            if not self.is_valid_date(le3.text()) or not self.is_valid_date(le4.text()):
                QMessageBox.warning(dialog, "Ошибка", "Дата должна быть в формате YYYY-MM-DD")
                return
            dialog.accept()

        save.clicked.connect(try_save)
        cancel.clicked.connect(dialog.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        if dialog.exec():
            cur = self.conn.cursor()
            cur.execute("""UPDATE tasks SET title=?, task=?, until=?, alert=?, status=?, priority=? WHERE id=?""",
                        (le1.text(), le2.text(), le3.text(), le4.text(),
                         le5.currentText(), le6.currentText(), item_id))
            self.conn.commit()
            self.load_tasks()

    def delete_selected(self):
        """Удалить выбранную задачу"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу.")
            return
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return
        reply = QMessageBox.question(self, "Удаление", "Удалить задачу?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id=?", (item_id,))
            self.conn.commit()
            self.load_tasks()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

