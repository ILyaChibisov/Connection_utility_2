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

ip_list = ['192.168.4.16', '192.168.4.26', '192.168.4.61']


class SimpleTableWidget(QTableWidget):
    def __init__(self, data, parent=None, chunk_data=None):
        super().__init__(parent)
        self.chunk_data = chunk_data  # Данные о чанках для комбобоксов
        self.setData(data)

    def setData(self, data):
        headers = data.columns.values.tolist()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setRowCount(len(data))

        for i, row in data.iterrows():
            for j, value in enumerate(row):
                header_name = headers[j]

                if header_name in ['is_virtual', 'is_commpressed']:
                    # Создаем чекбоксы для булевых полей
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
                    # Создаем комбобокс для выбора чанка
                    combo = QComboBox()

                    # Добавляем доступные чанки
                    if self.chunk_data is not None and len(self.chunk_data) > 0:
                        # Используем правильное имя колонки из chunk_data
                        if 'chunk_name' in self.chunk_data.columns:
                            chunk_names = self.chunk_data['chunk_name'].unique().tolist()
                        else:
                            chunk_names = self.chunk_data['chunk'].unique().tolist()
                        combo.addItems(chunk_names)

                    # Устанавливаем текущее значение
                    current_index = combo.findText(str(value))
                    if current_index >= 0:
                        combo.setCurrentIndex(current_index)
                    else:
                        combo.addItem(str(value))
                        combo.setCurrentIndex(combo.count() - 1)

                    # Подключаем сигнал изменения
                    combo.currentTextChanged.connect(
                        lambda text, row_idx=i: self.on_chunk_changed(row_idx, text)
                    )

                    self.setCellWidget(i, j, combo)

                else:
                    item = QTableWidgetItem(str(value))
                    self.setItem(i, j, item)

        self.resizeColumnsToContents()

    def on_chunk_changed(self, row_idx, chunk_name):
        """Обработчик изменения выбранного чанка"""
        if self.chunk_data is None or chunk_name == "":
            return

        # Находим информацию о выбранном чанке
        if 'chunk_name' in self.chunk_data.columns:
            chunk_info = self.chunk_data[self.chunk_data['chunk_name'] == chunk_name]
        else:
            chunk_info = self.chunk_data[self.chunk_data['chunk'] == chunk_name]

        if len(chunk_info) > 0:
            # Берем первую запись (должна быть уникальной)
            chunk_row = chunk_info.iloc[0]

            # Обновляем поля position, length, io
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
        for i in range(self.columnCount()):
            if self.horizontalHeaderItem(i).text() == column_name:
                return i
        return -1

    def add_empty_row(self):
        current_row_count = self.rowCount()
        self.insertRow(current_row_count)

        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount())]
        for col, header in enumerate(headers):
            if header in ['is_virtual', 'is_commpressed']:
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.setCellWidget(current_row_count, col, checkbox_widget)

            elif header == 'chunk_name':
                # Создаем комбобокс для новой строки
                combo = QComboBox()

                # Добавляем доступные чанки
                if self.chunk_data is not None and len(self.chunk_data) > 0:
                    if 'chunk_name' in self.chunk_data.columns:
                        chunk_names = self.chunk_data['chunk_name'].unique().tolist()
                    else:
                        chunk_names = self.chunk_data['chunk'].unique().tolist()
                    combo.addItems(chunk_names)

                # Подключаем сигнал изменения
                combo.currentTextChanged.connect(
                    lambda text, row_idx=current_row_count: self.on_chunk_changed(row_idx, text)
                )

                self.setCellWidget(current_row_count, col, combo)

            else:
                item = QTableWidgetItem("")
                self.setItem(current_row_count, col, item)

    def getData(self):
        data_list = []
        headers = [self.horizontalHeaderItem(i).text() for i in range(self.columnCount())]

        print(f"DEBUG: Table headers in UI: {headers}")

        for row in range(self.rowCount()):
            row_data = {}
            for col, header in enumerate(headers):
                if header in ['is_virtual', 'is_commpressed']:
                    checkbox_widget = self.cellWidget(row, col)
                    if checkbox_widget:
                        checkbox = checkbox_widget.layout().itemAt(0).widget()
                        row_data[header] = checkbox.isChecked()
                    else:
                        row_data[header] = False

                elif header == 'chunk_name':
                    combo_widget = self.cellWidget(row, col)
                    if combo_widget:
                        row_data[header] = combo_widget.currentText()
                    else:
                        row_data[header] = ""

                else:
                    item = self.item(row, col)
                    row_data[header] = item.text() if item else ""

            # Выводим значения для отладки
            if row == 0:  # только для первой строки
                print(
                    f"DEBUG: User input - reg_num: {row_data.get('reg_num', 'N/A')}, method: {row_data.get('method', 'N/A')}, offset: {row_data.get('offset', 'N/A')}")

            data_list.append(row_data)

        result_df = pd.DataFrame(data_list, columns=headers)
        return result_df


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
        # self.ui.pushButton_2.clicked.connect(self.update_connections) #
        # self.ui.pushButton_3.clicked.connect(self.data_update_connections)
        self.ui.pushButton_4.clicked.connect(self.get_chunk_info)
        # self.ui.pushButton_5.clicked.connect(self.csv_chunk_info)
        self.ui.pushButton_6.clicked.connect(self.get_chunk_connection_info)
        # self.ui.pushButton_7.clicked.connect(self.csv_chunk_connection_info)
        self.ui.pushButton_8.clicked.connect(self.create_new_connection)
        self.ui.pushButton_9.clicked.connect(self.refactor_connection)
        # self.ui.pushButton_10.clicked.connect(self.get_all_connections)
        self.ui.pushButton_11.clicked.connect(self.get_chunk_connection_info_by_search)
        self.ui.pushButton_12.clicked.connect(self.save_new_connection)
        self.ui.pushButton_13.clicked.connect(self.save_edited_connection)

        for ip in ip_list:
            self.ui.comboBox.addItem("%s" % ip)

        self.editing_table = None
        self.current_connection_type = ""
        self.is_editing_mode = False
        self.chunk_data = None

        # Загружаем данные о чанках при инициализации
        self.load_chunk_data()

    def _standardize_output(self, data):
        """Приводит вывод к стандартному формату"""
        if data is None or len(data) == 0:
            return data

        print(f"DEBUG: Input data columns: {data.columns.tolist()}")

        # Убираем служебные колонки
        columns_to_remove = ['connection_type_id', 'chunk_id']
        data = data.drop(columns=[col for col in columns_to_remove if col in data.columns], errors='ignore')

        # Обратное преобразование названий колонок из БД в наш стандарт
        reverse_column_mapping = {}

        # Проверяем какие колонки есть в данных и создаем mapping
        if 'connection' in data.columns:
            reverse_column_mapping['connection'] = 'connection_type'
        if 'chunk' in data.columns:
            reverse_column_mapping['chunk'] = 'chunk_name'  # Исправлено: chunk -> chunk_name
        if 'chunk_offset' in data.columns:
            reverse_column_mapping['chunk_offset'] = 'offset'
        elif 'offset' in data.columns:
            # Если уже есть offset, оставляем как есть
            pass
        if 'is_compressed' in data.columns:
            reverse_column_mapping['is_compressed'] = 'is_commpressed'

        data = data.rename(columns=reverse_column_mapping)

        # ВАЖНО: Исправляем порядок колонок согласно STANDARD_COLUMNS
        # Создаем новый DataFrame с правильным порядком
        result_data = pd.DataFrame()

        for col in STANDARD_COLUMNS:
            if col in data.columns:
                result_data[col] = data[col]
            else:
                # Если колонка отсутствует, создаем ее с NaN значениями
                result_data[col] = None

        print(f"DEBUG: Output data columns: {result_data.columns.tolist()}")
        if len(result_data) > 0:
            sample_row = result_data.iloc[0]
            print(
                f"DEBUG: Sample values - reg_num: {sample_row.get('reg_num', 'N/A')}, method: {sample_row.get('method', 'N/A')}, offset: {sample_row.get('offset', 'N/A')}")

        return result_data

    def _prepare_data_for_save(self, data):
        """Подготавливает данные для сохранения в БД (универсальный метод)"""
        # ПРАВИЛЬНЫЙ ПОРЯДОК КОЛОНОК ДЛЯ БАЗЫ ДАННЫХ
        database_column_order = [
            'connection_type', 'chunk_name', 'position', 'length', 'io',
            'reg_num', 'method', 'offset', 'is_virtual', 'is_commpressed'
        ]

        # Переименовываем колонки согласно структуре таблицы в БД
        column_mapping = {
            'connection_type': 'connection',
            'chunk_name': 'chunk',  # Исправлено: chunk_name -> chunk
            'offset': 'chunk_offset',
            'is_commpressed': 'is_compressed'
        }

        # Переупорядочиваем и переименовываем колонки
        data = data[database_column_order].rename(columns=column_mapping)

        return data

    def load_chunk_data(self):
        """Загрузка данных для выпадающих списков"""
        try:
            print("DEBUG: Loading chunk data...")
            ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            raw_chunk_data = cn.connect_to_bd('', ip, user, passwd, 1)

            # Стандартизируем данные о чанках
            self.chunk_data = self._standardize_chunk_data(raw_chunk_data)

            print(f"DEBUG: Chunk data columns: {self.chunk_data.columns.tolist()}")
            if len(self.chunk_data) > 0:
                print(f"DEBUG: Sample chunk data: {self.chunk_data.iloc[0].to_dict()}")
            return True
        except Exception as e:
            print(f"DEBUG: Error loading chunk data: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные для выпадающих списков: {str(e)}")
            return False

    def _standardize_chunk_data(self, chunk_data):
        """Стандартизирует данные о чанках для использования в комбобоксах"""
        if chunk_data is None or len(chunk_data) == 0:
            return chunk_data

        print(f"DEBUG: Raw chunk data columns: {chunk_data.columns.tolist()}")

        # Переименовываем колонки для единообразия
        chunk_mapping = {}
        if 'chunk' in chunk_data.columns:
            chunk_mapping['chunk'] = 'chunk_name'
        if 'chunk_name' in chunk_data.columns:
            # Уже правильное имя, оставляем как есть
            pass

        if chunk_mapping:
            chunk_data = chunk_data.rename(columns=chunk_mapping)

        # Оставляем только нужные колонки
        required_columns = ['chunk_name', 'position', 'length', 'io']
        for col in required_columns:
            if col not in chunk_data.columns:
                chunk_data[col] = None

        chunk_data = chunk_data[required_columns]
        print(f"DEBUG: Standardized chunk data columns: {chunk_data.columns.tolist()}")

        return chunk_data

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def create_new_connection(self):
        """Создание новой схемы подключения"""
        try:
            # Загружаем актуальные данные о чанках
            if not self.load_chunk_data():
                return

            connection_name, ok = QInputDialog.getText(self, "Новая схема подключения",
                                                       "Введите название схемы подключения:")

            if not ok or not connection_name.strip():
                return

            self.current_connection_type = connection_name.strip()
            self.is_editing_mode = False

            # Создаем пустой DataFrame со стандартными колонками
            empty_data = pd.DataFrame(columns=STANDARD_COLUMNS)
            empty_data.loc[0] = [''] * len(empty_data.columns)

            # Создаем редактируемую таблицу с передачей данных о чанках
            self.clear_layout(self.ui.gridLayout)
            container = QWidget()
            layout = QVBoxLayout(container)

            self.editing_table = SimpleTableWidget(empty_data, chunk_data=self.chunk_data)
            layout.addWidget(self.editing_table)

            add_row_button = QPushButton("Добавить строку")
            add_row_button.clicked.connect(self.editing_table.add_empty_row)
            layout.addWidget(add_row_button)

            self.ui.gridLayout.addWidget(container, 0, 0)

            QMessageBox.information(self, "Успех",
                                    f"Создана новая схема '{self.current_connection_type}'. Заполните данные и нажмите 'Внести в БД'")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании новой схемы: {str(e)}")

    def save_new_connection(self):
        """Сохранение новой схемы подключения в БД"""
        try:
            if self.editing_table is None or not self.current_connection_type:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
                return

            new_data = self.editing_table.getData()

            if len(new_data) == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
                return

            # Проверяем, что все поля заполнены
            for column in new_data.columns:
                empty_cells = new_data[column].isnull() | (new_data[column].astype(str) == '')
                if empty_cells.any():
                    empty_rows = empty_cells[empty_cells].index.tolist()
                    QMessageBox.warning(self, "Ошибка",
                                        f"Все поля должны быть заполнены. Пустые значения в колонке '{column}', строки: {[r + 1 for r in empty_rows]}")
                    return

            # Проверяем единое название схемы
            connection_names = new_data['connection_type'].unique()
            if len(connection_names) > 1:
                QMessageBox.warning(self, "Ошибка",
                                    f"Все строки должны иметь одинаковое название схемы подключения. Найдены: {', '.join(connection_names)}")
                return

            new_data['connection_type'] = self.current_connection_type

            # Подготавливаем данные для БД
            db_data = self._prepare_data_for_save(new_data)

            # Сохраняем в CSV
            temp_file = 'temp_new_connection.csv'
            db_data.to_csv(temp_file, sep=',', index=False, encoding='utf-8')
            print(f"DEBUG: Saving to CSV with columns: {db_data.columns.tolist()}")
            if len(db_data) > 0:
                print(f"DEBUG: First row values: {db_data.iloc[0].tolist()}")

            # Загружаем в БД
            ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            result = cn.connect_to_bd(temp_file, ip, user, passwd, 0)

            # Удаляем временный файл
            import os
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # Показываем результат (стандартизированный)
            self.clear_layout(self.ui.gridLayout)
            result_standard = self._standardize_output(result)
            table = ot.out_table(result_standard)
            self.ui.gridLayout.addWidget(table, 0, 0)

            QMessageBox.information(self, "Успех", "Новая схема подключения успешно добавлена в БД")

            self.current_connection_type = ""
            self.editing_table = None

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def refactor_connection(self):
        """Загрузка существующей схемы для редактирования"""
        try:
            # Загружаем актуальные данные о чанках
            if not self.load_chunk_data():
                return

            connection_name = self.ui.lineEdit_5.text().strip()

            if not connection_name:
                QMessageBox.warning(self, "Ошибка", "Введите название схемы подключения")
                return

            ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()

            data_2 = cn.connect_to_bd(path, ip, user, passwd, [connection_name])

            if len(data_2) == 0:
                QMessageBox.warning(self, "Ошибка", f"Схема подключения '{connection_name}' не найдена")
                return

            print(f"DEBUG: Raw data from DB columns: {data_2.columns.tolist()}")
            if len(data_2) > 0:
                print(
                    f"DEBUG: Raw data values - reg_num: {data_2.iloc[0]['reg_num']}, method: {data_2.iloc[0]['method']}, chunk_offset: {data_2.iloc[0].get('chunk_offset', 'N/A')}")

            # Стандартизируем данные перед отображением
            data_2_standard = self._standardize_output(data_2)

            print(f"DEBUG: After standardization columns: {data_2_standard.columns.tolist()}")
            if len(data_2_standard) > 0:
                print(
                    f"DEBUG: Standardized values - reg_num: {data_2_standard.iloc[0]['reg_num']}, method: {data_2_standard.iloc[0]['method']}, offset: {data_2_standard.iloc[0]['offset']}")

            self.clear_layout(self.ui.gridLayout)
            self.editing_table = SimpleTableWidget(data_2_standard, chunk_data=self.chunk_data)
            self.ui.gridLayout.addWidget(self.editing_table, 0, 0)

            # ВЫВЕДЕМ ЗАГОЛОВКИ ТАБЛИЦЫ ДЛЯ ПРОВЕРКИ
            headers = [self.editing_table.horizontalHeaderItem(i).text() for i in
                       range(self.editing_table.columnCount())]
            print(f"DEBUG: Table headers in UI: {headers}")

            self.current_connection_type = connection_name
            self.is_editing_mode = True

            QMessageBox.information(self, "Успех", f"Схема '{connection_name}' загружена для редактирования")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке схемы: {str(e)}")

    def save_edited_connection(self):
        """Сохранение отредактированной схемы"""
        try:
            if self.editing_table is None:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
                return

            edited_data = self.editing_table.getData()

            if len(edited_data) == 0:
                QMessageBox.warning(self, "Ошибка", "Нет данных для сохранения")
                return

            print(
                f"DEBUG: Edited data from table: {edited_data.iloc[0].to_dict() if len(edited_data) > 0 else 'Empty'}")

            # Проверяем, что все поля заполнены
            for column in edited_data.columns:
                empty_cells = edited_data[column].isnull() | (edited_data[column].astype(str) == '')
                if empty_cells.any():
                    empty_rows = empty_cells[empty_cells].index.tolist()
                    QMessageBox.warning(self, "Ошибка",
                                        f"Все поля должны быть заполнены. Пустые значения в колонке '{column}', строки: {[r + 1 for r in empty_rows]}")
                    return

            # Подготавливаем данные для БД
            db_data = self._prepare_data_for_save(edited_data)

            # Сохраняем в CSV
            temp_file = 'temp_edited_connection.csv'
            db_data.to_csv(temp_file, sep=',', index=False, encoding='utf-8')
            print(f"DEBUG: Saving edited to CSV with columns: {db_data.columns.tolist()}")
            if len(db_data) > 0:
                print(f"DEBUG: First row values: {db_data.iloc[0].tolist()}")

            # Загружаем в БД
            ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
            result = cn.connect_to_bd(temp_file, ip, user, passwd, 0)

            # Удаляем временный файл
            import os
            if os.path.exists(temp_file):
                os.remove(temp_file)

            # Показываем результат (стандартизированный)
            self.clear_layout(self.ui.gridLayout)
            result_standard = self._standardize_output(result)
            table = ot.out_table(result_standard)
            self.ui.gridLayout.addWidget(table, 0, 0)

            QMessageBox.information(self, "Успех", "Схема подключения успешно обновлена")

            self.current_connection_type = ""
            self.editing_table = None
            self.is_editing_mode = False

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    # Остальные методы остаются без изменений...
    # def update_connections(self):
    #     global data
    #     ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
    #     data = cn.connect_to_bd(path, ip, user, passwd, 3)
    #     data_standard = self._standardize_output(data)
    #     table = ot.out_table(data_standard)
    #     self.clear_layout(self.ui.gridLayout)
    #     self.ui.gridLayout.addWidget(table, 0, 0)

    # def data_update_connections(self):
    #     global data
    #     if len(data) > 1 and self.ui.pushButton_3.text() != 'Выполнено':
    #         data_standard = self._standardize_output(data)
    #         data_standard.to_csv('connection_info.csv', sep=',', index=False, encoding='utf-8')
    #         self.ui.pushButton_3.setText('Выполнено')

    def get_chunk_info(self):
        global data_1
        ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        data_1 = cn.connect_to_bd(path, ip, user, passwd, 1)
        # data_1_standard = self._standardize_output(data_1)
        table = ot.out_table(data_1)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)

    # def csv_chunk_info(self):
    #     global data_1
    #     if self.ui.pushButton_5.text() != 'Выполнено':
    #         data_1_standard = self._standardize_output(data_1)
    #         data_1_standard.to_csv('chunk_info.csv', sep=',', index=False, encoding='utf-8')
    #         self.ui.pushButton_5.setText('Выполнено')

    def get_chunk_connection_info(self):
        global data_2
        ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        data_2 = cn.connect_to_bd(path, ip, user, passwd, 2)
        data_2_standard = self._standardize_output(data_2)
        table = ot.out_table(data_2_standard)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)

    # def get_all_connections(self):
    #     global data_2
    #     ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
    #     data_2 = cn.connect_to_bd(path, ip, user, passwd, 2)
    #     data_2_standard = self._standardize_output(data_2)
    #     table = ot.out_table(data_2_standard)
    #     self.clear_layout(self.ui.gridLayout)
    #     self.ui.gridLayout.addWidget(table, 0, 0)

    def get_chunk_connection_info_by_search(self):
        global data_2
        ip, user, passwd = self.ui.comboBox.currentText(), self.ui.lineEdit_2.text(), self.ui.lineEdit_3.text()
        type_con = self.ui.lineEdit_4.text()
        data_2 = cn.connect_to_bd(path, ip, user, passwd, [type_con])
        data_2_standard = self._standardize_output(data_2)
        table = ot.out_table(data_2_standard)
        self.clear_layout(self.ui.gridLayout)
        self.ui.gridLayout.addWidget(table, 0, 0)

    # def csv_chunk_connection_info(self):
    #     global data_2
    #     type_con = self.ui.lineEdit_4.text()
    #     if self.ui.pushButton_7.text() != 'Выполнено':
    #         data_2_standard = self._standardize_output(data_2)
    #         data_2_standard.to_csv('chunk_connection_info(' + type_con + ').csv', sep=',', index=False,
    #                                encoding='utf-8')
    #         self.ui.pushButton_7.setText('Выполнено')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon.ico'))
    myapp = MyWin()
    myapp.show()
    sys.exit(app.exec_())