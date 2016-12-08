'''
Created on 6 mai 2015

@author:  Cyril Jacquet
'''
from gui import plugins as gui_plugins
from PyQt5.Qt import pyqtSlot


class WritePropertiesDockPlugin(gui_plugins.GuiWriteSubWindowDockPlugin):

    '''
    PropertiesDockPlugin
    '''
    is_builtin_plugin = True
    ignore = True

    def __init__(self):
        '''
        Constructor
        '''

        super(WritePropertiesDockPlugin, self).__init__()

    def gui_class(self):
        return GuiPropertyDock


# class CorePropertyDock():
#
#     '''
#     CorePropertyDock
#     '''
#
#     dock_name = "properties-dock"
#
#     def __init__(self):
#         '''
#         Constructor
#         '''
#
#         super(CorePropertyDock, self).__init__()
#         self._property_table_model = None
#         self._sheet_id = None
#         self.tree_sheet = None
#
#     @property
#     def sheet_id(self):
#         return self._sheet_id
#
#     @sheet_id.setter
#     def sheet_id(self, sheet_id):
#         if self._sheet_id == sheet_id:
#             pass
#         self._sheet_id = sheet_id
#         if self.sheet_id is not None:
#             self.tree_sheet = core_cfg.core.tree_sheet_manager.get_tree_sheet_from_sheet_id(
#                 self.sheet_id)
#             _ = self.property_table_model
#
#     @property
#     def property_table_model(self):
#         if self._property_table_model is None:
#             self._property_table_model = PropertyTableModel(self)
#             if self._sheet_id is not None:
#                 self._property_table_model.set_sheet_id(self._sheet_id)
#                 self._property_table_model.tree_sheet \
#                     = core_cfg.core.tree_sheet_manager.get_tree_sheet_from_sheet_id(self.sheet_id)
#
#         return self._property_table_model
#
#     @pyqtSlot()
#     def add_property_row(self, index):
#         core_cfg.data.database.sheet_tree.set_property(self.sheet_id, "", "")
#         #self._property_table_model.insertRow(1, index)
#
#     @pyqtSlot()
#     def remove_property_row(self, index):
#         node = self.property_table_model.node_from_index(index)
#         core_cfg.data.database.sheet_tree.remove_property(self.sheet_id, node.key)
#         #self._property_table_model.removeRow(
#         #    index.row(), self._property_table_model.root_model_index())

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QSortFilterProxyModel, QSettings
from gui import cfg as gui_cfg
from gui.property import SheetProperty
from gui.models.property_model import PropertyModel, AddPropertyCommand, RemovePropertyCommand

from plugins.writepropertiesdock import properties_dock_ui


class GuiPropertyDock():

    '''
    GuiPropertyDock
    '''
    dock_name = "properties-dock"
    dock_displayed_name = _("Properties")

    def __init__(self):
        '''
        Constructor
        '''
        super(GuiPropertyDock, self).__init__()
        self.widget = None
        # self.core_part = None  # CorePropertyDock
        self._sheet_id = None
        self.paperFilterModel = TableFilter()
        self.paperFilterSystemModel = TableFilter()
        self._current_property_id = None
        self._table_model = None
        self._system_table_model = None

    @property
    def table_model(self):
        if self._table_model is None:
            self._table_model = gui_cfg.models["0_sheet_property_model"]

        return self._table_model

    @property
    def system_table_model(self):
        if self._system_table_model is None:
            self._system_table_model = gui_cfg.models["0_sheet_system_property_model"]

        return self._system_table_model


    @property
    def paper_id(self):
        """
        Only used for compatibility with API, return sheet_id
        :return:
        """
        return self.sheet_id

    @paper_id.setter
    def paper_id(self, paper_id):
        """
        Only used for compatibility with API, call sheet_id
        :param id:
        """
        self.sheet_id = paper_id

    @property
    def sheet_id(self):
        return self._sheet_id

    @sheet_id.setter
    def sheet_id(self, sheet_id):
        if self._sheet_id == sheet_id:
            return
        self._sheet_id = sheet_id
        self.paperFilterModel.filterByPaperId(sheet_id)
        self.paperFilterSystemModel.filterByPaperId(sheet_id)


    def get_widget(self):

        if self.widget is None:
            self.widget = QWidget()
            self.ui = properties_dock_ui.Ui_WritePropertiesDock()
            self.ui.setupUi(self.widget)
            gui_cfg.signal_hub.apply_settings_widely_sent.connect(self.apply_settings)
            self.apply_settings()


            self.paperFilterSystemModel.setParent(self.widget)
            self.paperFilterSystemModel.setFilterKeyColumn(-1)
            self.paperFilterSystemModel.setFilterCaseSensitivity(False)
            self.paperFilterSystemModel.setSourceModel(self.system_table_model)


            system_filter = QSortFilterProxyModel(self.widget)
            system_filter.setFilterKeyColumn(0)
            system_filter.setFilterCaseSensitivity(False)
            system_filter.setSourceModel(self.paperFilterSystemModel)

            # system model :
            self.ui.systemTableView.setModel(system_filter)

            # system connect :
            self.ui.filterLineEdit.textChanged.connect(system_filter.setFilterFixedString)


            # filter :
            self.paperFilterModel.setParent(self.widget)
            self.paperFilterModel.setFilterKeyColumn(-1)
            self.paperFilterModel.setFilterCaseSensitivity(False)
            self.paperFilterModel.setSourceModel(self.table_model)

            filter = QSortFilterProxyModel(self.widget)
            filter.setFilterKeyColumn(0)
            filter.setFilterCaseSensitivity(False)
            filter.setSourceModel(self.paperFilterModel)



            # model :
            self.ui.tableView.setModel(filter)

            # connect :
            self.ui.addPropButton.clicked.connect(self.add_property_row)
            self.ui.removePropButton.clicked.connect(self.remove_property_row)
            self.ui.filterLineEdit.textChanged.connect(filter.setFilterFixedString)
            self.ui.tableView.clicked.connect(self.set_current_id)

            self.ui.tableView.selectionModel().currentRowChanged.connect(self.set_current_id)

            self.widget.gui_part = self
        return self.widget



    @pyqtSlot()
    def add_property_row(self):
        command = AddPropertyCommand(self.paper_id, self.table_model)
        self.table_model.undo_stack.push(command)
        new_sheet_id = command.last_new_id
        self.table_model.set_undo_stack_active()

    @pyqtSlot()
    def remove_property_row(self):
        # if SheetProperty(self._current_property_id).remove() == True:
        #     self._current_property_id = None

        command = RemovePropertyCommand(self._current_property_id, self.table_model)
        self._current_property_id = None
        self.table_model.undo_stack.push(command)
        self.table_model.set_undo_stack_active()


    @pyqtSlot('QModelIndex', 'QModelIndex')
    def set_current_id(self, current_index, previous_index):
        self.set_current_id(current_index)

    @pyqtSlot('QModelIndex')
    def set_current_id(self, model_index):
        #self.ui.tableView.setCurrentIndex(model_index)
        self._current_property_id = model_index.data(PropertyModel.IdRole)

    @pyqtSlot()
    def apply_settings(self):
        settings = QSettings()
        self.ui.systemTableView.setVisible(bool(settings.value("settings/misc/dev_mode", False)))

from PyQt5.QtCore import QSortFilterProxyModel, Qt

class TableFilter(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(TableFilter, self).__init__(parent)
        self._current_paper_id = -1

    def filterAcceptsRow(self, row, index):
        code = self.sourceModel().index(row, 0,index).data(PropertyModel.CodeRole)
        if code == self._current_paper_id:
            return True
        else:
            return False


    def filterByPaperId(self, paper_id:int):

        self._current_paper_id = paper_id
        self.invalidateFilter()

