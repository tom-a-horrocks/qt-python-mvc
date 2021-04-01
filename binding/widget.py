from typing import List, Union

from PySide2.QtWidgets import QTableWidget, QTableWidgetItem


class BindableQTableWidget(QTableWidget):
    """
    Table widget that exposes its data for updating, and clears and repopulates the table on data change.
    Intended to be used for simple one-way (VM->Table) binding for small datasets that don't change often.
    """

    def __init__(self, *args, **kwargs):
        super(BindableQTableWidget, self).__init__(*args, **kwargs)

    def text_items(self):
        n_rows = self.rowCount()
        n_cols = self.columnCount()
        return [
            [self.item(i, j).text() for j in range(n_cols)]
            for i in range(n_rows)
        ]

    def QT_items(self):
        n_rows = self.rowCount()
        n_cols = self.columnCount()
        return [
            [self.item(i, j) for j in range(n_cols)]
            for i in range(n_rows)
        ]

    def set_data(self, data: Union[List[List[str]], List[List[QTableWidgetItem]]]):
        self.setRowCount(0)
        self.setRowCount(len(data))
        print(f'Entering into table with shape {(self.rowCount(), self.columnCount())}')
        for i, row in enumerate(data):
            for j, element in enumerate(row):
                if type(element) is str:
                    element = QTableWidgetItem(element)
                self.setItem(i, j, element)
