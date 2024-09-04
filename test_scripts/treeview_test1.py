import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget, QHeaderView, QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Create the QTreeView
        tree_view = QTreeView()

        # Set the model for the QTreeView
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Column 1', 'Column 2','col3'])
        tree_view.setModel(model)

        # Add a few items to the model
        for i in range(5):
            item1 = QStandardItem(f"Item {i+1}")
            item2 = QStandardItem(f"Col2")
            item3 = QStandardItem(f"Col3")
            model.appendRow([item1, item2,item3])

        # Set the header to allow the user to resize columns
        header = tree_view.header()
        #header.setSectionResizeMode(QHeaderView.Interactive)  # Allow user to resize all columns interactively

        # Optional: Set specific columns to different resize modes
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Auto resize the first column to its contents
        #header.setSectionResizeMode(1, QHeaderView.Fixed)  # Auto resize the first column to its contents
        #header.setSectionResizeMode(2, QHeaderView.Fixed)  # Allow the second column to be resizable
        header.setStretchLastSection(False)
        #header.setSectionResizeMode(2, QHeaderView.Fixed)  # Stretch the third column to fill remaining space

        # Optional: Set minimum and maximum widths for a column
        #header.setMinimumSectionSize(50)  # Set minimum width for all columns
        #tree_view.setColumnWidth(0, 500)  # Set initial width of the first column
        tree_view.setColumnWidth(1, 50)  # Set initial width of the second column
        tree_view.setColumnWidth(2, 50)  # Set initial width of the third column

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(tree_view)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
