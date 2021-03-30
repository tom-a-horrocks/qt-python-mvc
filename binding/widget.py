from typing import List

from PySide2.QtWidgets import QTableWidget, QTableWidgetItem


class BindableQTableWidget(QTableWidget):
    """
    Table widget that exposes its data for updating, and clears and repopulates the table on data change.
    Intended to be used for simple one-way (VM->Table) binding for small datasets that don't change open.
    """

    def __init__(self, *args, **kwargs):
        super(BindableQTableWidget, self).__init__(*args, **kwargs)

    def get_data(self):
        n_rows = self.rowCount()
        n_cols = self.columnCount()
        return [
            [self.item(i, j).text() for j in range(n_cols)]
            for i in range(n_rows)
        ]

    def set_data(self, data: List[List[str]]):
        self.setRowCount(0)
        self.setRowCount(len(data))
        print(f'Entering into table with shape {(self.rowCount(), self.columnCount())}')
        for i, row in enumerate(data):
            for j, element in enumerate(row):
                self.setItem(i, j, QTableWidgetItem(str(element)))
