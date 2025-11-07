import sqlite3
import os
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QLineEdit, QLabel, \
    QHeaderView, QComboBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer


class SecondWindow(QWidget):
    def __init__(self, db_path='tasks.db', tray=None):
        super().__init__()
        self.db_path = db_path
        self.tray = tray  # получаем ссылку на иконку трея для уведомлений
        self.conn = None
        self.init_db()
        self.initUI()
        self.load_tasks()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(10000)

    def init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            task TEXT NOT NULL,
            until TEXT,
            alert TEXT,
            status TEXT
        )""")
        self.conn.commit()

    def initUI(self):
        self.setWindowTitle("Все задачи")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Заголовок', 'Задача', 'До', 'Оповещение', 'Статус'])
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        btn_edit = QPushButton("Редактировать")
        btn_delete = QPushButton("Удалить")
        btn_refresh = QPushButton("Обновить")

        btn_edit.clicked.connect(self.edit_selected)
        btn_delete.clicked.connect(self.delete_selected)
        btn_refresh.clicked.connect(self.load_tasks)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
        QWidget { background: #170909; font-family: Arial; }
        QLabel { color: white; }
        QGroupBox { color: white; }
        QLineEdit {
            background: #140303; color: white;
            padding: 6px; border: 1px solid #cfd8e3; border-radius: 4px;
        }
        QPushButton {
            background: #3c0a0a; color: white; border-radius: 6px; padding: 6px 12px;
        }
        QPushButton:hover { background: #601010; }
        """)

        self.setMinimumSize(700, 420)

    def load_tasks(self):
        self.table.setRowCount(0)
        cur = self.conn.cursor()
        cur.execute("""SELECT id, title, task, until, alert, status FROM tasks ORDER BY id""")
        for row_data in cur.fetchall():
            _id, title, task, until, alert, status = row_data
            row = self.table.rowCount()
            self.table.insertRow(row)
            it0 = QTableWidgetItem(title)
            it0.setData(Qt.ItemDataRole.UserRole, _id)
            self.table.setItem(row, 0, it0)
            self.table.setItem(row, 1, QTableWidgetItem(task))
            self.table.setItem(row, 2, QTableWidgetItem(until or ''))
            self.table.setItem(row, 3, QTableWidgetItem(alert or ''))
            self.table.setItem(row, 4, QTableWidgetItem(status or 'В работе'))

    def add_row(self, title, task, date1, date2, status):
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO tasks (title, task, until, alert, status) VALUES (?, ?, ?, ?, ?)""",
            (title, task, date1, date2, status)
        )
        self.conn.commit()
        self.load_tasks()

    def check_notifications(self):
        today = datetime.now().date()
        cur = self.conn.cursor()
        rows = cur.execute("""SELECT id, title, alert, until, status FROM tasks""").fetchall()
        changed = False

        for _id, title, alert, until, status in rows:
            if alert:
                try:
                    alert_date = datetime.strptime(alert, '%Y-%m-%d').date()
                    if alert_date == today and status not in ('Выполнена', 'Отменена'):
                        QMessageBox.information(
                            self,
                            'Напоминание',
                            f'Сегодня оповещение по задаче:\n\n«{title}»'
                        )
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

    def edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу.")
            return
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Редактировать задачу")
        le1 = QLineEdit(self.table.item(row, 0).text())
        le2 = QLineEdit(self.table.item(row, 1).text())
        le3 = QLineEdit(self.table.item(row, 2).text())
        le4 = QLineEdit(self.table.item(row, 3).text())
        le5 = QComboBox()
        statuses = ['Не начата', 'В работе', 'Выполнена', 'Отменена']
        le5.addItems(statuses)
        try:
            le5.setCurrentIndex(statuses.index(self.table.item(row, 4).text()))
        except ValueError:
            le5.setCurrentIndex(1)

        layout = QVBoxLayout(dlg)
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
        buttons = QHBoxLayout()
        save = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        save.clicked.connect(dlg.accept)
        cancel.clicked.connect(dlg.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

        if dlg.exec():
            new_title = le1.text().strip()
            new_task = le2.text().strip()
            new_until = le3.text().strip()
            new_alert = le4.text().strip()
            new_status = le5.currentText()

            cur = self.conn.cursor()
            cur.execute("""UPDATE tasks SET title=?, task=?, until=?, alert=?, status=? WHERE id=?""",
                        (new_title, new_task, new_until, new_alert, new_status, item_id))
            self.conn.commit()
            self.load_tasks()

    def delete_selected(self):
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
            cur.execute("""DELETE FROM tasks WHERE id=?""", (item_id,))
            self.conn.commit()
            self.load_tasks()

    def closeEvent(self, event):
        event.ignore()
        self.hide()