from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1100, 800)

        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)

        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # ==========================================
        # 1. ВЕРХНЯЯ ПАНЕЛЬ (Подключение)
        # ==========================================
        self.group_conn = QGroupBox("Подключение к серверу")
        self.conn_layout = QHBoxLayout(self.group_conn)
        self.conn_layout.setSpacing(10)

        self.label_5 = QLabel("IP-адрес:")
        self.comboBox = QComboBox()
        self.comboBox.setEditable(True)
        self.comboBox.setMinimumWidth(150)

        self.label_2 = QLabel("Пользователь:")
        self.lineEdit_2 = QLineEdit()
        self.lineEdit_2.setMinimumWidth(100)

        self.label_3 = QLabel("Пароль:")
        self.lineEdit_3 = QLineEdit()
        self.lineEdit_3.setEchoMode(QLineEdit.Password)
        self.lineEdit_3.setMinimumWidth(100)

        self.conn_layout.addWidget(self.label_5)
        self.conn_layout.addWidget(self.comboBox)
        self.conn_layout.addWidget(self.label_2)
        self.conn_layout.addWidget(self.lineEdit_2)
        self.conn_layout.addWidget(self.label_3)
        self.conn_layout.addWidget(self.lineEdit_3)
        self.conn_layout.addStretch()

        self.main_layout.addWidget(self.group_conn)

        # ==========================================
        # 2. ПАНЕЛЬ ДЕЙСТВИЙ (Кнопки)
        # ==========================================
        self.group_actions = QGroupBox("Действия с базами данных")
        self.actions_layout = QGridLayout(self.group_actions)
        self.actions_layout.setSpacing(10)

        self.pushButton_4 = QPushButton("📄 Таблица контактов")
        self.pushButton_6 = QPushButton("📊 Таблица внесённых схем")
        self.actions_layout.addWidget(self.pushButton_4, 0, 0)
        self.actions_layout.addWidget(self.pushButton_6, 0, 1)

        self.pushButton_11 = QPushButton("🔍 Поиск схемы")
        self.lineEdit_4 = QLineEdit()
        self.lineEdit_4.setPlaceholderText("Введите точное название...")
        self.actions_layout.addWidget(self.pushButton_11, 1, 0)
        self.actions_layout.addWidget(self.lineEdit_4, 1, 1)

        self.pushButton_9 = QPushButton("✏️ Изменить схему")
        self.lineEdit_5 = QLineEdit()
        self.lineEdit_5.setPlaceholderText("Название схемы для изменения...")
        self.actions_layout.addWidget(self.pushButton_9, 2, 0)
        self.actions_layout.addWidget(self.lineEdit_5, 2, 1)

        self.pushButton_8 = QPushButton("➕ Создать схему")
        self.actions_layout.addWidget(self.pushButton_8, 3, 0, 1, 2)

        self.main_layout.addWidget(self.group_actions)

        # ==========================================
        # 3. ПАНЕЛЬ ТАБЛИЦЫ
        # ==========================================
        self.gridLayoutWidget = QWidget()
        self.gridLayout = QVBoxLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addWidget(self.gridLayoutWidget, 1)

        # ==========================================
        # 4. НИЖНЯЯ ПАНЕЛЬ (Только сохранение)
        # ==========================================
        self.save_layout = QHBoxLayout()
        self.save_layout.setSpacing(10)

        self.pushButton_13 = QPushButton("💾 Сохранить изменения")
        self.pushButton_12 = QPushButton("💾 Применить изменения")

        # Добавляем кнопку "Добавить строку" в этот же ряд, но скрываем её по умолчанию
        # Она будет показываться только при создании/редактировании схемы
        self.pushButton_add_row = QPushButton("➕ Добавить строку")
        self.pushButton_add_row.hide()

        self.save_layout.addWidget(self.pushButton_13)
        self.save_layout.addWidget(self.pushButton_12)
        self.save_layout.addWidget(self.pushButton_add_row)
        self.save_layout.addStretch()

        self.main_layout.addLayout(self.save_layout)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle("Connection Utility — Управление схемами")