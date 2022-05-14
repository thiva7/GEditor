from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class Table(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        rowsLabel = QLabel("Rows:", self)
        self.rows = QSpinBox(self)
        colsLabel = QLabel("Columns:", self)
        self.cols = QSpinBox(self)
        spaceLabel = QLabel("Margin Thickness:", self)
        self.space = QSpinBox(self)
        padLabel = QLabel("Cell size:", self)
        self.pad = QSpinBox(self)
        self.pad.setValue(10)
        insertButton = QPushButton("Add", self)
        insertButton.clicked.connect(self.insert)

        layout = QGridLayout()
        layout.addWidget(rowsLabel, 0, 0)
        layout.addWidget(self.rows, 0, 1)
        layout.addWidget(colsLabel, 1, 0)
        layout.addWidget(self.cols, 1, 1)
        layout.addWidget(padLabel, 2, 0)
        layout.addWidget(self.pad, 2, 1)
        layout.addWidget(spaceLabel, 3, 0)
        layout.addWidget(self.space, 3, 1)
        layout.addWidget(insertButton, 4, 0, 1, 2)

        self.setWindowTitle("Καταχωρηση Πινακα")
        self.setGeometry(300, 300, 200, 100)
        self.setLayout(layout)

    def insert(self):
        cursor = self.parent.editor.textCursor()
        rows = self.rows.value()
        cols = self.cols.value()
        if not rows or not cols:
            popup = QMessageBox(QMessageBox.Warning,
                                "Error",
                                "The number of rows or columns can not be zero!",
                                QMessageBox.Ok, self)
            popup.show()
        else:
            padding = self.pad.value()
            space = self.space.value()
            fmt = QTextTableFormat()
            fmt.setCellPadding(padding)
            fmt.setCellSpacing(space)
            cursor.insertTable(rows, cols, fmt)
            self.close()
