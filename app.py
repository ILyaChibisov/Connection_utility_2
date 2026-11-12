import sys
import pandas as pd
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon, QColor, QBrush
from PyQt5.QtWidgets import *

import connection as cn
import out_table as ot
from ui_app import Ui_MainWindow

STANDARD_COLUMNS = [
    'connection_type', 'chunk_name', 'position', 'length', 'io',
    'offset', 'reg_num', 'method', 'is_virtual', 'is_commpressed'
]

ip_list = ['192.168.4.16', '192.168.4.26', '192.168.4.61', '192.168.4.116', '192.168.4.137']


class SimpleTableWidget(QTableWidget):
    def __init__(self, data, parent=None, chunk_data=None, allow_add_rows=True):
        super().__init__(parent)
        self.chunk_data = chunk_data
        self.allow_add_rows = allow_add_rows
        self.deleted_rows = set()

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(45)

        self.setShowGrid(True)

        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #dcdcdc;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #e0e0e0;
                color: #000000;
            }
            QHeaderView::section {
                padding: 4px;
            }
        """)

        self.setData(data)

        # Настраиваем заголовки
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)  # Позволяем менять размер

        # Колонка "Действия" - фиксированная
        header.setSectionResizeMode(self.columnCount() - 1, QHeaderView.Fixed)
        self.setColumnWidth(self.columnCount() - 1, 110)

        # Первичный расчет ширины
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        """Умное распределение ширины при изменении размера окна"""
        super().resizeEvent(event)

        # 1. Сначала сжимаем все колонки по минимуму (по тексту)
        self.resizeColumnsToContents()

        # 2. Считаем, сколько места осталось
        total_width = sum(self.columnWidth(i) for i in range(self.columnCount()))
        available_width = self.viewport().width()

        # 3. Если места больше, чем нужно, распределяем его между connection_type и chunk_name
        if available_width > total_width:
            extra_space = available_width - total_width
            half_extra = extra_space // 2

            chunk_idx = -1
            for i in range(self.columnCount()):
                if self.horizontalHeaderItem(i).text() == 'chunk_name':
                    chunk_idx = i
                    break

            # Добавляем по половине свободного места к connection_type (индекс 0) и chunk_name
            self.setColumnWidth(0, self.columnWidth(0) + half_extra)
            if chunk_idx != -1:
                self.setColumnWidth(chunk_idx, self.columnWidth(chunk_idx) + half_extra)

    def create_delete_button(self, row_idx):
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setAlignment(Qt.AlignCenter)

        btn = QPushButton("Удалить")
        btn.setFixedSize(90, 28)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffcccc; color: #990000; border-radius: 4px; border: 1px solid #ff9999; font-weight: bold; padding: 0px; 
            }
            QPushButton:hover { background-color: #ff9999; }
        """)
        btn.clicked.connect(lambda checked, r=row_idx: self.delete_row(r))
        layout.addWidget(btn)
        return container

    def create_centered_checkbox(self, value):
        """Создает чекбокс, выровненный по центру ячейки"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        checkbox = QCheckBox()
        if str(value).lower() in ['true', '1', 'yes', 't']:
            checkbox.setChecked(True)

        layout.addWidget(checkbox)
        return container

    def setData(self, data):
        headers = data.columns.values.tolist()
        headers_with_actions = headers + ['Действия']
        self.setColumnCount(len(headers_with_actions))
        self.setHorizontalHeaderLabels(headers_with_actions)
        self.setRowCount(len(data))

        for i, row in data.iterrows():
            for j, value in enumerate(row):
                header_name = headers[j]

                if header_name in ['is_virtual', 'is_commpressed']:
                    self.setCellWidget(i, j, self.create_centered_checkbox(value))

                elif header_name == 'chunk_name':
                    combo = QComboBox()
                    combo.setEditable(True)
                    combo.setInsertPolicy(QComboBox.NoInsert)
                    # Убираем жесткий minimumWidth, чтобы он мог сжиматься

                    if self.chunk_data is not None and len(self.chunk_data) > 0:
                        for _, chunk_row in self.chunk_data.iterrows():
                            name = chunk_row.get('chunk_name', chunk_row.get('chunk', ''))
                            pos = chunk_row.get('position', '')
                            length = chunk_row.get('length', '')
                            io = chunk_row.get('io', '')
                            combo.addItem(f"{name} (pos:{pos}, len:{length}, io:{io})")
                            combo.setItemData(combo.count() - 1, chunk_row.to_dict(), Qt.UserRole)

                    current_val_str = str(value).strip()
                    if current_val_str:
                        found_idx = -1
                        for idx in range(combo.count()):
                            item_text = combo.itemText(idx).split(" (")[0].strip()
                            if item_text == current_val_str:
                                found_idx = idx
                                break
                        if found_idx >= 0:
                            combo.setCurrentIndex(found_idx)
                        else:
                            combo.addItem(current_val_str)
                            combo.setCurrentIndex(combo.count() - 1)

                    completer = combo.completer()
                    if completer:
                        completer.setCompletionMode(QCompleter.PopupCompletion)
                        completer.setFilterMode(Qt.MatchStartsWith)

                    combo.currentIndexChanged.connect(
                        lambda index, row_idx=i, cb=combo: self.on_chunk_changed(row_idx, index, cb)
                    )
                    self.setCellWidget(i, j, combo)
                else:
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.setItem(i, j, item)

            self.setCellWidget(i, len(headers), self.create_delete_button(i))

    def delete_row(self, row_idx):
        self.deleted_rows.add(row_idx)
        self.removeRow(row_idx)
        for row in range(self.rowCount()):
            self.setCellWidget(row, self.columnCount() - 1, self.create_delete_button(row))

    def on_chunk_changed(self, row_idx, index, combo_widget):
        if index < 0: return
        chunk_row_data = combo_widget.itemData(index, Qt.UserRole)
        if not chunk_row_data: return

        pos_item = self.item(row_idx, self.get_column_index('position'))
        len_item = self.item(row_idx, self.get_column_index('length'))
        io_item = self.item(row_idx, self.get_column_index('io'))

        if pos_item: pos_item.setText(str(chunk_row_data.get('position', '')))
        if len_item: len_item.setText(str(chunk_row_data.get('length', '')))
        if io_item: io_item.setText(str(chunk_row_data.get('io', '')))

    def get_column_index(self, column_name):
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]
        try:
            return headers.index(column_name)
        except ValueError:
            return -1

    def add_empty_row(self):
        row_index = self.rowCount()
        self.insertRow(row_index)
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]

        for col, header in enumerate(headers):
            if header in ['is_virtual', 'is_commpressed']:
                self.setCellWidget(row_index, col, self.create_centered_checkbox("false"))
            elif header == 'chunk_name':
                combo = QComboBox()
                combo.setEditable(True)
                combo.setInsertPolicy(QComboBox.NoInsert)

                if self.chunk_data is not None and len(self.chunk_data) > 0:
                    for _, chunk_row in self.chunk_data.iterrows():
                        name = chunk_row.get('chunk_name', chunk_row.get('chunk', ''))
                        pos = chunk_row.get('position', '')
                        length = chunk_row.get('length', '')
                        io = chunk_row.get('io', '')
                        combo.addItem(f"{name} (pos:{pos}, len:{length}, io:{io})")
                        combo.setItemData(combo.count() - 1, chunk_row.to_dict(), Qt.UserRole)

                completer = combo.completer()
                if completer:
                    completer.setCompletionMode(QCompleter.PopupCompletion)
                    completer.setFilterMode(Qt.MatchStartsWith)

                combo.currentIndexChanged.connect(
                    lambda index, row_idx=row_index, cb=combo: self.on_chunk_changed(row_idx, index, cb)
                )
                self.setCellWidget(row_index, col, combo)
            else:
                item = QTableWidgetItem("")
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.setItem(row_index, col, item)

        self.setCellWidget(row_index, len(headers), self.create_delete_button(row_index))

    def getData(self):
        data_list = []
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]

        for row in range(self.rowCount()):
            if row in self.deleted_rows: continue
            row_data = {}
            is_empty = True

            for col, header in enumerate(headers):
                if header in ['is_virtual', 'is_commpressed']:
                    cb_widget = self.cellWidget(row, col)
                    if cb_widget:
                        val = cb_widget.layout().itemAt(0).widget().isChecked()
                        row_data[header] = val
                        if val: is_empty = False
                    else:
                        row_data[header] = False
                elif header == 'chunk_name':
                    combo = self.cellWidget(row, col)
                    if combo:
                        val = combo.currentText().split(" (")[0].strip()
                        row_data[header] = val
                        if val: is_empty = False
                    else:
                        row_data[header] = ""
                else:
                    item = self.item(row, col)
                    val = item.text() if item else ""
                    row_data[header] = val
                    if val.strip(): is_empty = False

            if not is_empty: data_list.append(row_data)

        return pd.DataFrame(data_list, columns=headers) if data_list else pd.DataFrame(columns=headers)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon('icon.ico'))

        self.apply_styles()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.ico'))
        show_action = QAction("Показать", self)
        quit_action = QAction("Выход", self)
        hide_action = QAction("Свернуть", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.ui.pushButton_4.clicked.connect(self.get_chunk_info)
        self.ui.pushButton_6.clicked.connect(self.get_chunk_connection_info)
        self.ui.pushButton_8.clicked.connect(self.create_new_connection)
        self.ui.pushButton_9.clicked.connect(self.refactor_connection)
        self.ui.pushButton_11.clicked.connect(self.get_chunk_connection_info_by_search)

        self.ui.pushButton_13.clicked.connect(self.save_connection)
        self.ui.pushButton_cancel.clicked.connect(self.cancel_editing)

        for ip in ip_list:
            self.ui.comboBox.addItem(ip)

        self.ui.comboBox.setCurrentText('192.168.4.16')
        self.ui.lineEdit_2.setText('sshu')
        self.ui.lineEdit_3.setText('q1w2e3r4')

        self.editing_table = None
        self.current_connection_type = ""
        self.is_editing_mode = False
        self.chunk_data = None

        self.load_chunk_data()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QGroupBox {
                font-weight: bold; border: 1px solid #c0c0c0;
                border-radius: 6px; margin-top: 10px; background-color: #fafafa;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: #333333; }
            QLineEdit, QComboBox { padding: 6px; border: 1px solid #b0b0b0; border-radius: 4px; background-color: #ffffff; min-height: 20px; color: #000; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #777777; background-color: #fdfdfd; }
            QPushButton { background-color: #5a5a5a; color: white; border: none; border-radius: 4px; padding: 8px 15px; font-weight: bold; min-height: 25px; }
            QPushButton:hover { background-color: #444444; }
            QPushButton:pressed { background-color: #333333; }
            QTableWidget { 
                background-color: #ffffff; 
                border: 1px solid #c0c0c0; 
                border-radius: 4px; 
                gridline-color: #dcdcdc; 
            }
            QHeaderView::section { 
                background-color: #e8e8e8; 
                padding: 4px; 
                border: none; 
                border-bottom: 1px solid #c0c0c0; 
                border-right: 1px solid #dcdcdc; 
                font-weight: bold; 
                color: #333; 
            }
            QTableWidget::item { 
                padding: 2px; 
                color: #000; 
                border-right: 1px solid #dcdcdc; 
                border-bottom: 1px solid #dcdcdc;
            }
        """)

    def reset_interface(self):
        self.clear_layout()
        self.ui.pushButton_13.hide()
        self.ui.pushButton_add_row.hide()
        self.ui.pushButton_cancel.hide()
        self.editing_table = None
        self.current_connection_type = ""
        self.is_editing_mode = False

    def cancel_editing(self):
        reply = QMessageBox.question(self, 'Отмена', 'Вы уверены, что хотите отменить изменения?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.reset_interface()

    def _get_ip(self):
        ip = self.ui.comboBox.currentText().strip()
        if not ip:
            QMessageBox.warning(self, "Ошибка", "Укажите IP-адрес сервера")
            return None
        return ip

    def _standardize_output(self, data):
        if data is None or len(data) == 0: return data
        columns_to_remove = ['connection_type_id', 'chunk_id']
        data = data.drop(columns=[col for col in columns_to_remove if col in data.columns], errors='ignore')
        reverse_mapping = {'connection': 'connection_type', 'chunk': 'chunk_name', 'chunk_offset': 'offset',
                           'is_compressed': 'is_commpressed'}
        data = data.rename(columns=reverse_mapping)

        result = pd.DataFrame()
        for col in STANDARD_COLUMNS:
            result[col] = data[col] if col in data.columns else None
        return result

    def _prepare_data_for_save(self, data):
        order = ['connection_type', 'chunk_name', 'position', 'length', 'io', 'reg_num', 'method', 'offset',
                 'is_virtual', 'is_commpressed']
        mapping = {'connection_type': 'connection', 'chunk_name': 'chunk', 'offset': 'chunk_offset',
                   'is_commpressed': 'is_compressed'}
        return data[order].rename(columns=mapping)

    def load_chunk_data(self):
        try:
            ip = self._get_ip()
            if ip is None: return False
            user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            raw_data = cn.connect_to_bd(None, ip, user, passwd, 1)
            if 'Ошибка' in raw_data.columns: return False

            if 'chunk' in raw_data.columns:
                raw_data = raw_data.rename(columns={'chunk': 'chunk_name'})

            req_cols = ['chunk_name', 'position', 'length', 'io']
            for c in req_cols:
                if c not in raw_data.columns: raw_data[c] = None

            self.chunk_data = raw_data[req_cols]
            return True
        except Exception:
            return False

    def clear_layout(self):
        while self.ui.gridLayout.count():
            child = self.ui.gridLayout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

    def create_new_connection(self):
        if not self.load_chunk_data(): return
        name, ok = QInputDialog.getText(self, "Новая схема", "Введите название схемы:")
        if not ok or not name.strip(): return

        self.current_connection_type = name.strip()
        self.is_editing_mode = False

        empty_data = pd.DataFrame(columns=STANDARD_COLUMNS)
        row_data = [''] * len(empty_data.columns)
        row_data[0] = self.current_connection_type
        empty_data.loc[0] = row_data

        self.clear_layout()

        self.editing_table = SimpleTableWidget(empty_data, chunk_data=self.chunk_data)
        self.ui.gridLayout.addWidget(self.editing_table)

        self.ui.pushButton_add_row.show()
        self.ui.pushButton_13.show()
        self.ui.pushButton_cancel.show()

        try:
            self.ui.pushButton_add_row.clicked.disconnect()
        except:
            pass
        self.ui.pushButton_add_row.clicked.connect(self.editing_table.add_empty_row)

    def refactor_connection(self):
        if not self.load_chunk_data(): return
        name = self.ui.lineEdit_5.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название схемы")
            return

        ip = self._get_ip()
        if not ip: return
        data = cn.connect_to_bd(None, ip, self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text(), 4, name)

        if len(data) == 0 or 'Ошибка' in data.columns:
            QMessageBox.warning(self, "Ошибка", f"Схема '{name}' не найдена")
            return

        std_data = self._standardize_output(data)
        self.clear_layout()

        self.editing_table = SimpleTableWidget(std_data, chunk_data=self.chunk_data)
        self.ui.gridLayout.addWidget(self.editing_table)

        self.ui.pushButton_add_row.show()
        self.ui.pushButton_13.show()
        self.ui.pushButton_cancel.show()

        try:
            self.ui.pushButton_add_row.clicked.disconnect()
        except:
            pass
        self.ui.pushButton_add_row.clicked.connect(self.editing_table.add_empty_row)

        self.current_connection_type = name
        self.is_editing_mode = True

    def save_connection(self):
        if self.editing_table is None:
            QMessageBox.warning(self, "Внимание", "Нет открытой схемы для сохранения.")
            return

        data = self.editing_table.getData()
        if len(data) == 0:
            QMessageBox.warning(self, "Внимание", "Нет данных для сохранения.")
            return

        for i, row in data.iterrows():
            for col in data.columns:
                if pd.isna(row[col]) or str(row[col]).strip() == '':
                    QMessageBox.warning(self, "Ошибка", f"Пустое значение в колонке '{col}', строка {i + 1}")
                    return

        data['connection_type'] = self.current_connection_type
        db_data = self._prepare_data_for_save(data)

        ip = self._get_ip()
        if not ip: return

        result = cn.connect_to_bd(db_data, ip, self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text(), 0)
        if 'Ошибка' in result.columns:
            QMessageBox.critical(self, "Ошибка", result.iloc[0]['Ошибка'])
            return

        self.clear_layout()
        table = ot.out_table(self._standardize_output(result))
        self.ui.gridLayout.addWidget(table)

        self.ui.pushButton_add_row.hide()
        self.ui.pushButton_13.hide()
        self.ui.pushButton_cancel.hide()

        QMessageBox.information(self, "Успех", "Схема успешно сохранена!")
        self.editing_table = None

    def get_chunk_info(self):
        ip = self._get_ip()
        if not ip: return
        data = cn.connect_to_bd(None, ip, self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text(), 1)
        self.clear_layout()
        self.ui.pushButton_add_row.hide()
        self.ui.pushButton_13.hide()
        self.ui.pushButton_cancel.hide()
        self.ui.gridLayout.addWidget(ot.out_table(data))

    def get_chunk_connection_info(self):
        ip = self._get_ip()
        if not ip: return
        data = cn.connect_to_bd(None, ip, self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text(), 2)
        self.clear_layout()
        self.ui.pushButton_add_row.hide()
        self.ui.pushButton_13.hide()
        self.ui.pushButton_cancel.hide()
        self.ui.gridLayout.addWidget(ot.out_table(self._standardize_output(data)))

    def get_chunk_connection_info_by_search(self):
        ip = self._get_ip()
        if not ip: return
        name = self.ui.lineEdit_4.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Введите название схемы для поиска.")
            return

        data = cn.connect_to_bd(None, ip, self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text(), 4, name)
        self.clear_layout()
        self.ui.pushButton_add_row.hide()
        self.ui.pushButton_13.hide()
        self.ui.pushButton_cancel.hide()
        self.ui.gridLayout.addWidget(ot.out_table(self._standardize_output(data)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = app.font()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    window = MainApp()
    window.show()
    sys.exit(app.exec_())