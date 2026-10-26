from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from main import *
import sys
import connection as cn
import out_table as ot
import pandas as pd

path, data, data_1, data_2 = ('',) * 4

# ЕДИНЫЙ ПОРЯДОК КОЛОНОК ДЛЯ ВСЕХ ТАБЛИЦ
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
        self.deleted_rows = set()  # Храним индексы удаленных строк
        self.setData(data)

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
                    checkbox = QCheckBox()
                    if str(value).lower() in ['true', '1', 'yes', 't']:
                        checkbox.setChecked(True)
                    else:
                        checkbox.setChecked(False)

                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setAlignment(Qt.AlignCenter)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    self.setCellWidget(i, j, checkbox_widget)

                elif header_name == 'chunk_name':
                    combo = QComboBox()

                    if self.chunk_data is not None and len(self.chunk_data) > 0:
                        if 'chunk_name' in self.chunk_data.columns:
                            chunk_names = self.chunk_data['chunk_name'].unique().tolist()
                        else:
                            chunk_names = self.chunk_data['chunk'].unique().tolist()
                        combo.addItems(chunk_names)

                    current_index = combo.findText(str(value))
                    if current_index >= 0:
                        combo.setCurrentIndex(current_index)
                    else:
                        combo.addItem(str(value))
                        combo.setCurrentIndex(combo.count() - 1)

                    combo.currentTextChanged.connect(
                        lambda text, row_idx=i: self.on_chunk_changed(row_idx, text)
                    )

                    self.setCellWidget(i, j, combo)

                else:
                    item = QTableWidgetItem(str(value))
                    self.setItem(i, j, item)

            delete_button = QPushButton("Удалить")
            delete_button.clicked.connect(lambda checked, row_idx=i: self.delete_row(row_idx))
            self.setCellWidget(i, len(headers), delete_button)

        self.resizeColumnsToContents()

    def delete_row(self, row_idx):
        """Удаляет строку из таблицы и добавляет в список удаленных"""
        # Запоминаем, что эта строка удалена
        self.deleted_rows.add(row_idx)
        self.removeRow(row_idx)

        # Обновляем индексы для оставшихся кнопок удаления
        for row in range(self.rowCount()):
            delete_button = self.cellWidget(row, self.columnCount() - 1)
            if delete_button:
                try:
                    delete_button.clicked.disconnect()
                except:
                    pass
                delete_button.clicked.connect(lambda checked, r=row: self.delete_row(r))

    def on_chunk_changed(self, row_idx, chunk_name):
        """Обработчик изменения выбранного чанка"""
        if self.chunk_data is None or chunk_name == "":
            return

        if 'chunk_name' in self.chunk_data.columns:
            chunk_info = self.chunk_data[self.chunk_data['chunk_name'] == chunk_name]
        else:
            chunk_info = self.chunk_data[self.chunk_data['chunk'] == chunk_name]

        if len(chunk_info) > 0:
            chunk_row = chunk_info.iloc[0]

            position_item = self.item(row_idx, self.get_column_index('position'))
            length_item = self.item(row_idx, self.get_column_index('length'))
            io_item = self.item(row_idx, self.get_column_index('io'))

            if position_item is not None:
                position_item.setText(str(chunk_row.get('position', '')))
            if length_item is not None:
                length_item.setText(str(chunk_row.get('length', '')))
            if io_item is not None:
                io_item.setText(str(chunk_row.get('io', '')))

    def get_column_index(self, column_name):
        """Возвращает индекс колонки по имени"""
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]
        try:
            return headers.index(column_name)
        except ValueError:
            return -1

    def add_empty_row(self):
        """Добавляет пустую строку только по нажатию кнопки"""
        row_index = self.rowCount()
        self.insertRow(row_index)

        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]

        for col, header in enumerate(headers):
            if header in ['is_virtual', 'is_commpressed']:
                checkbox = QCheckBox()

                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.setCellWidget(row_index, col, checkbox_widget)

            elif header == 'chunk_name':
                combo = QComboBox()

                if self.chunk_data is not None and len(self.chunk_data) > 0:
                    if 'chunk_name' in self.chunk_data.columns:
                        chunk_names = self.chunk_data['chunk_name'].unique().tolist()
                    else:
                        chunk_names = self.chunk_data['chunk'].unique().tolist()
                    combo.addItems(chunk_names)

                combo.currentTextChanged.connect(
                    lambda text, row_idx=row_index: self.on_chunk_changed(row_idx, text)
                )

                self.setCellWidget(row_index, col, combo)

            else:
                item = QTableWidgetItem("")
                self.setItem(row_index, col, item)

        delete_button = QPushButton("Удалить")
        delete_button.clicked.connect(lambda checked, row_idx=row_index: self.delete_row(row_idx))
        self.setCellWidget(row_index, len(headers), delete_button)

    def getData(self):
        """Получает данные из таблицы, ИСКЛЮЧАЯ удаленные строки"""
        data_list = []
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount() - 1)]

        for row in range(self.rowCount()):
            # Пропускаем удаленные строки
            if row in self.deleted_rows:
                continue

            row_data = {}
            is_empty_row = True

            for col, header in enumerate(headers):
                if header in ['is_virtual', 'is_commpressed']:
                    checkbox_widget = self.cellWidget(row, col)
                    if checkbox_widget:
                        checkbox = checkbox_widget.layout().itemAt(0).widget()
                        row_data[header] = checkbox.isChecked()
                        if checkbox.isChecked():
                            is_empty_row = False
                    else:
                        row_data[header] = False

                elif header == 'chunk_name':
                    combo_widget = self.cellWidget(row, col)
                    if combo_widget:
                        value = combo_widget.currentText()
                        row_data[header] = value
                        if value.strip():
                            is_empty_row = False
                    else:
                        row_data[header] = ""

                else:
                    item = self.item(row, col)
                    value = item.text() if item else ""
                    row_data[header] = value
                    if value.strip():
                        is_empty_row = False

            # Добавляем только непустые строки, которые не были удалены
            if not is_empty_row:
                data_list.append(row_data)

        result_df = pd.DataFrame(data_list, columns=headers) if data_list else pd.DataFrame(columns=headers)
        return result_df

    def has_valid_data(self):
        """Проверяет, есть ли в таблице хотя бы одна заполненная строка"""
        data = self.getData()
        return len(data) > 0


class MyWin(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

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

        # Подключаем кнопки
        self.ui.pushButton_4.clicked.connect(self.get_chunk_info)
        self.ui.pushButton_6.clicked.connect(self.get_chunk_connection_info)
        self.ui.pushButton_8.clicked.connect(self.create_new_connection)
        self.ui.pushButton_9.clicked.connect(self.refactor_connection)
        self.ui.pushButton_11.clicked.connect(self.get_chunk_connection_info_by_search)
        self.ui.pushButton_12.clicked.connect(self.save_connection)
        self.ui.pushButton_13.clicked.connect(self.save_connection)

        # Кнопки "Принять изменения" всегда видны
        self.ui.pushButton_12.setVisible(True)
        self.ui.pushButton_13.setVisible(True)

        for ip in ip_list:
            self.ui.comboBox.addItem("%s" % ip)

        # Разрешаем ручной ввод IP-адреса
        self.ui.comboBox.setEditable(True)
        self.ui.comboBox.setInsertPolicy(QComboBox.NoInsert)

        self.editing_table = None
        self.current_connection_type = ""
        self.is_editing_mode = False
        self.chunk_data = None

        # Загружаем данные о чанках при инициализации
        self.load_chunk_data()

    def _get_ip(self):
        """Возвращает IP из comboBox (выбранный или введённый вручную) с валидацией."""
        ip = self.ui.comboBox.currentText().strip()
        if not ip:
            QMessageBox.warning(self, "Ошибка", "Укажите IP-адрес сервера")
            return None
        parts = ip.split('.')
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            QMessageBox.warning(self, "Ошибка", f"Некорректный IP-адрес: {ip}")
            return None
        return ip

    def _standardize_output(self, data):
        """Приводит вывод к стандартному формату"""
        if data is None or len(data) == 0:
            return data

        # Убираем служебные колонки
        columns_to_remove = ['connection_type_id', 'chunk_id']
        data = data.drop(columns=[col for col in columns_to_remove if col in data.columns], errors='ignore')

        # Обратное преобразование названий колонок из БД в наш стандарт
        reverse_column_mapping = {}

        if 'connection' in data.columns:
            reverse_column_mapping['connection'] = 'connection_type'
        if 'chunk' in data.columns:
            reverse_column_mapping['chunk'] = 'chunk_name'
        if 'chunk_offset' in data.columns:
            reverse_column_mapping['chunk_offset'] = 'offset'
        elif 'offset' in data.columns:
            pass
        if 'is_compressed' in data.columns:
            reverse_column_mapping['is_compressed'] = 'is_commpressed'

        data = data.rename(columns=reverse_column_mapping)

        # Создаем новый DataFrame с правильным порядком
        result_data = pd.DataFrame()

        for col in STANDARD_COLUMNS:
            if col in data.columns:
                result_data[col] = data[col]
            else:
                result_data[col] = None

        return result_data

    def _prepare_data_for_save(self, data):
        """Подготавливает данные для сохранения в БД"""
        database_column_order = [
            'connection_type', 'chunk_name', 'position', 'length', 'io',
            'reg_num', 'method', 'offset', 'is_virtual', 'is_commpressed'
        ]

        column_mapping = {
            'connection_type': 'connection',
            'chunk_name': 'chunk',
            'offset': 'chunk_offset',
            'is_commpressed': 'is_compressed'
        }

        data = data[database_column_order].rename(columns=column_mapping)
        return data

    def load_chunk_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            ip = self._get_ip()
            if ip is None:
                return False
            user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            raw_chunk_data = cn.connect_to_bd(None, ip, user, passwd, 1)
            self.chunk_data = self._standardize_chunk_data(raw_chunk_data)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные для выпадающих списков: {str(e)}")
            return False

    def _standardize_chunk_data(self, chunk_data):
        """Стандартизирует данные о чанках для использования в комбобоксах"""
        if chunk_data is None or len(chunk_data) == 0:
            return chunk_data

        chunk_mapping = {}
        if 'chunk' in chunk_data.columns:
            chunk_mapping['chunk'] = 'chunk_name'

        if chunk_mapping:
            chunk_data = chunk_data.rename(columns=chunk_mapping)

        required_columns = ['chunk_name', 'position', 'length', 'io']
        for col in required_columns:
            if col not in chunk_data.columns:
                chunk_data[col] = None

        chunk_data = chunk_data[required_columns]
        return chunk_data

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def create_new_connection(self):
        """Создание новой схемы подключения"""
        try:
            if not self.load_chunk_data():
                return

            connection_name, ok = QInputDialog.getText(self, "Новая схема подключения",
                                                       "Введите название схемы подключения:")

            if not ok or not connection_name.strip():
                return

            self.current_connection_type = connection_name.strip()
            self.is_editing_mode = False

            # Создаем пустой DataFrame с одной пустой строкой
            empty_data = pd.DataFrame(columns=STANDARD_COLUMNS)
            empty_data.loc[0] = [''] * len(empty_data.columns)

            self.clear_layout(self.ui.gridLayout)
            container = QWidget()
            layout = QVBoxLayout(container)

            # Создаем таблицу без автоматических пустых строк
            self.editing_table = SimpleTableWidget(empty_data, chunk_data=self.chunk_data, allow_add_rows=False)
            layout.addWidget(self.editing_table)

            # Добавляем кнопку для добавления новых строк
            add_row_button = QPushButton("Добавить строку")
            add_row_button.clicked.connect(self.editing_table.add_empty_row)
            layout.addWidget(add_row_button)

            self.ui.gridLayout.addWidget(container, 0, 0)

            QMessageBox.information(self, "Успех",
                                    f"Создана новая схема '{self.current_connection_type}'. Заполните данные и нажмите 'Принять изменения' для сохранения.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании новой схемы: {str(e)}")

    def refactor_connection(self):
        """Загрузка существующей схемы для редактирования"""
        try:
            if not self.load_chunk_data():
                return

            connection_name = self.ui.lineEdit_5.text().strip()

            if not connection_name:
                QMessageBox.warning(self, "Ошибка", "Введите название схемы подключения")
                return

            ip = self._get_ip()
            if ip is None:
                return
            user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()

            # Используем точное соответствие для поиска
            data_2 = cn.connect_to_bd(None, ip, user, passwd, 4, connection_name)

            if len(data_2) == 0:
                QMessageBox.warning(self, "Ошибка", f"Схема подключения '{connection_name}' не найдена")
                return

            # Стандартизируем данные перед отображением
            data_2_standard = self._standardize_output(data_2)

            self.clear_layout(self.ui.gridLayout)

            container = QWidget()
            layout = QVBoxLayout(container)

            # Создаем таблицу без автоматических пустых строк
            self.editing_table = SimpleTableWidget(data_2_standard, chunk_data=self.chunk_data, allow_add_rows=False)
            layout.addWidget(self.editing_table)

            # Добавляем кнопку для добавления новых строк
            add_row_button = QPushButton("Добавить строку")
            add_row_button.clicked.connect(self.editing_table.add_empty_row)
            layout.addWidget(add_row_button)

            self.ui.gridLayout.addWidget(container, 0, 0)

            self.current_connection_type = connection_name
            self.is_editing_mode = True

            QMessageBox.information(self, "Успех",
                                    f"Схема '{connection_name}' загружена для редактирования. "
                                    f"Вы можете добавлять новые строки с помощью кнопки 'Добавить строку'.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке схемы: {str(e)}")

    def save_connection(self):
        """Сохранение схемы подключения в БД (универсальный метод)"""
        try:
            if self.editing_table is None:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения. Сначала создайте или загрузите схему.")
                return

            data_to_save = self.editing_table.getData()

            if len(data_to_save) == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения. Заполните хотя бы одну строку.")
                return

            # Проверяем, что все поля заполнены
            for i, row in data_to_save.iterrows():
                for column in data_to_save.columns:
                    value = row[column]
                    if pd.isna(value) or str(value).strip() == '':
                        QMessageBox.warning(self, "Ошибка",
                                            f"Все поля должны быть заполнены. Пустое значение в колонке '{column}', строка: {i + 1}")
                        return

            # Убеждаемся, что все строки имеют правильное название схемы
            data_to_save['connection_type'] = self.current_connection_type

            # Подготавливаем данные для БД
            db_data = self._prepare_data_for_save(data_to_save)

            # Загружаем в БД напрямую
            ip = self._get_ip()
            if ip is None:
                return
            user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            result = cn.connect_to_bd(db_data, ip, user, passwd, 0)

            if 'Ошибка' in result.columns:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении в БД: {result.iloc[0]['Ошибка']}")
                return

            # Показываем результат
            self.clear_layout(self.ui.gridLayout)
            result_standard = self._standardize_output(result)
            table = ot.out_table(result_standard)
            self.ui.gridLayout.addWidget(table, 0, 0)

            success_message = "Схема подключения успешно сохранена в БД" if self.is_editing_mode else "Новая схема подключения успешно добавлена в БД"
            QMessageBox.information(self, "Успех", success_message)

            # ОЧИЩАЕМ СОСТОЯНИЕ ПОСЛЕ УСПЕШНОГО СОХРАНЕНИЯ
            self.current_connection_type = ""
            self.editing_table = None
            self.is_editing_mode = False

            # Очищаем поле ввода для следующей операции
            self.ui.lineEdit_5.clear()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def get_chunk_info(self):
        global data_1
        ip = self._get_ip()
        if ip is None:
            return
        user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        data_1 = cn.connect_to_bd(None, ip, user, passwd, 1)
        table = ot.out_table(data_1)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)

    def get_chunk_connection_info(self):
        global data_2
        ip = self._get_ip()
        if ip is None:
            return
        user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        data_2 = cn.connect_to_bd(None, ip, user, passwd, 2)
        data_2_standard = self._standardize_output(data_2)
        table = ot.out_table(data_2_standard)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)

    def get_chunk_connection_info_by_search(self):
        """Поиск схемы подключения по точному соответствию"""
        global data_2
        ip = self._get_ip()
        if ip is None:
            return
        user, passwd = self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        type_con = self.ui.lineEdit_4.text().strip()

        if not type_con:
            QMessageBox.warning(self, "Ошибка", "Введите название схемы для поиска")
            return

        # Используем точное соответствие для поиска
        data_2 = cn.connect_to_bd(None, ip, user, passwd, 4, type_con)

        if len(data_2) == 0:
            QMessageBox.information(self, "Результат поиска", f"Схема подключения '{type_con}' не найдена")
            return

        data_2_standard = self._standardize_output(data_2)
        table = ot.out_table(data_2_standard)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    myapp = MyWin()
    myapp.show()
    sys.exit(app.exec_())