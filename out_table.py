from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

def out_table(data):
    headers = data.columns.values.tolist()
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)

    for i, row in data.iterrows():
        table.setRowCount(table.rowCount() + 1)
        for j in range(table.columnCount()):
            table.setItem(i, j, QTableWidgetItem(str(row[j])))

    table.resizeColumnsToContents()
    table.updateGeometry()
    table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    return table