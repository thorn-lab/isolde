# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'molprobity_widget.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Frame(object):
    def setupUi(self, Frame):
        Frame.setObjectName("Frame")
        Frame.resize(575, 830)
        Frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Frame)
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self._validate_scroll_area = QtWidgets.QScrollArea(Frame)
        self._validate_scroll_area.setWidgetResizable(True)
        self._validate_scroll_area.setObjectName("_validate_scroll_area")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 569, 824))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self._validate_rama_stub_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
        self._validate_rama_stub_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._validate_rama_stub_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._validate_rama_stub_frame.setObjectName("_validate_rama_stub_frame")
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout(self._validate_rama_stub_frame)
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.label_22 = QtWidgets.QLabel(self._validate_rama_stub_frame)
        self.label_22.setObjectName("label_22")
        self.horizontalLayout_21.addWidget(self.label_22)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_21.addItem(spacerItem)
        self._validate_rama_show_button = QtWidgets.QPushButton(self._validate_rama_stub_frame)
        self._validate_rama_show_button.setObjectName("_validate_rama_show_button")
        self.horizontalLayout_21.addWidget(self._validate_rama_show_button)
        self.verticalLayout_12.addWidget(self._validate_rama_stub_frame)
        self._validate_rama_main_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
        self._validate_rama_main_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._validate_rama_main_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._validate_rama_main_frame.setObjectName("_validate_rama_main_frame")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self._validate_rama_main_frame)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.horizontalLayout_23 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_23.setObjectName("horizontalLayout_23")
        self.label_21 = QtWidgets.QLabel(self._validate_rama_main_frame)
        self.label_21.setObjectName("label_21")
        self.horizontalLayout_23.addWidget(self.label_21)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_23.addItem(spacerItem1)
        self._validate_rama_case_combo_box = QtWidgets.QComboBox(self._validate_rama_main_frame)
        self._validate_rama_case_combo_box.setObjectName("_validate_rama_case_combo_box")
        self._validate_rama_case_combo_box.addItem("")
        self._validate_rama_case_combo_box.addItem("")
        self._validate_rama_case_combo_box.addItem("")
        self._validate_rama_case_combo_box.addItem("")
        self._validate_rama_case_combo_box.addItem("")
        self._validate_rama_case_combo_box.addItem("")
        self.horizontalLayout_23.addWidget(self._validate_rama_case_combo_box)
        self._validate_rama_hide_button = QtWidgets.QPushButton(self._validate_rama_main_frame)
        self._validate_rama_hide_button.setObjectName("_validate_rama_hide_button")
        self.horizontalLayout_23.addWidget(self._validate_rama_hide_button)
        self.verticalLayout_13.addLayout(self.horizontalLayout_23)
        self.horizontalLayout_24 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")
        self._validate_rama_plot_container = QtWidgets.QWidget(self._validate_rama_main_frame)
        self._validate_rama_plot_container.setMinimumSize(QtCore.QSize(350, 350))
        self._validate_rama_plot_container.setObjectName("_validate_rama_plot_container")
        self._validate_rama_plot_layout = QtWidgets.QVBoxLayout(self._validate_rama_plot_container)
        self._validate_rama_plot_layout.setContentsMargins(0, 0, 0, 0)
        self._validate_rama_plot_layout.setObjectName("_validate_rama_plot_layout")
        self.horizontalLayout_24.addWidget(self._validate_rama_plot_container)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_24.addItem(spacerItem2)
        self.verticalLayout_13.addLayout(self.horizontalLayout_24)
        self.horizontalLayout_22 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self._validate_rama_sel_combo_box = QtWidgets.QComboBox(self._validate_rama_main_frame)
        self._validate_rama_sel_combo_box.setObjectName("_validate_rama_sel_combo_box")
        self._validate_rama_sel_combo_box.addItem("")
        self._validate_rama_sel_combo_box.addItem("")
        self.horizontalLayout_22.addWidget(self._validate_rama_sel_combo_box)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_22.addItem(spacerItem3)
        self._validate_rama_go_button = QtWidgets.QPushButton(self._validate_rama_main_frame)
        self._validate_rama_go_button.setObjectName("_validate_rama_go_button")
        self.horizontalLayout_22.addWidget(self._validate_rama_go_button)
        self.verticalLayout_13.addLayout(self.horizontalLayout_22)
        self.verticalLayout_12.addWidget(self._validate_rama_main_frame)
        self._validate_omega_stub_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
        self._validate_omega_stub_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._validate_omega_stub_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._validate_omega_stub_frame.setObjectName("_validate_omega_stub_frame")
        self.horizontalLayout_25 = QtWidgets.QHBoxLayout(self._validate_omega_stub_frame)
        self.horizontalLayout_25.setObjectName("horizontalLayout_25")
        self.label_26 = QtWidgets.QLabel(self._validate_omega_stub_frame)
        self.label_26.setObjectName("label_26")
        self.horizontalLayout_25.addWidget(self.label_26)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_25.addItem(spacerItem4)
        self._validate_omega_show_button = QtWidgets.QPushButton(self._validate_omega_stub_frame)
        self._validate_omega_show_button.setObjectName("_validate_omega_show_button")
        self.horizontalLayout_25.addWidget(self._validate_omega_show_button)
        self.verticalLayout_12.addWidget(self._validate_omega_stub_frame)
        self._validate_omega_main_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents_2)
        self._validate_omega_main_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._validate_omega_main_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._validate_omega_main_frame.setObjectName("_validate_omega_main_frame")
        self.verticalLayout_16 = QtWidgets.QVBoxLayout(self._validate_omega_main_frame)
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.label_27 = QtWidgets.QLabel(self._validate_omega_main_frame)
        self.label_27.setObjectName("label_27")
        self.horizontalLayout_27.addWidget(self.label_27)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_27.addItem(spacerItem5)
        self._validate_omega_hide_button = QtWidgets.QPushButton(self._validate_omega_main_frame)
        self._validate_omega_hide_button.setObjectName("_validate_omega_hide_button")
        self.horizontalLayout_27.addWidget(self._validate_omega_hide_button)
        self.verticalLayout_16.addLayout(self.horizontalLayout_27)
        self.gridLayout_7 = QtWidgets.QGridLayout()
        self.gridLayout_7.setObjectName("gridLayout_7")
        self._validate_omega_cis_list = QtWidgets.QListWidget(self._validate_omega_main_frame)
        self._validate_omega_cis_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._validate_omega_cis_list.setObjectName("_validate_omega_cis_list")
        self.gridLayout_7.addWidget(self._validate_omega_cis_list, 1, 0, 1, 1)
        self.label_29 = QtWidgets.QLabel(self._validate_omega_main_frame)
        self.label_29.setObjectName("label_29")
        self.gridLayout_7.addWidget(self.label_29, 0, 0, 1, 1)
        self.label_30 = QtWidgets.QLabel(self._validate_omega_main_frame)
        self.label_30.setObjectName("label_30")
        self.gridLayout_7.addWidget(self.label_30, 0, 1, 1, 1)
        self._validate_omega_twisted_list = QtWidgets.QListWidget(self._validate_omega_main_frame)
        self._validate_omega_twisted_list.setObjectName("_validate_omega_twisted_list")
        self.gridLayout_7.addWidget(self._validate_omega_twisted_list, 1, 1, 1, 1)
        self.verticalLayout_16.addLayout(self.gridLayout_7)
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_28.addItem(spacerItem6)
        self._validate_omega_update_button = QtWidgets.QPushButton(self._validate_omega_main_frame)
        self._validate_omega_update_button.setObjectName("_validate_omega_update_button")
        self.horizontalLayout_28.addWidget(self._validate_omega_update_button)
        self.verticalLayout_16.addLayout(self.horizontalLayout_28)
        self.verticalLayout_12.addWidget(self._validate_omega_main_frame)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_12.addItem(spacerItem7)
        self._validate_scroll_area.setWidget(self.scrollAreaWidgetContents_2)
        self.verticalLayout_2.addWidget(self._validate_scroll_area)

        self.retranslateUi(Frame)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def retranslateUi(self, Frame):
        _translate = QtCore.QCoreApplication.translate
        Frame.setWindowTitle(_translate("Frame", "Frame"))
        self.label_22.setText(_translate("Frame", "Ramachandran Plot"))
        self._validate_rama_show_button.setText(_translate("Frame", "Show"))
        self.label_21.setText(_translate("Frame", "Ramachandran Plot"))
        self._validate_rama_case_combo_box.setItemText(0, _translate("Frame", "General"))
        self._validate_rama_case_combo_box.setItemText(1, _translate("Frame", "Glycine"))
        self._validate_rama_case_combo_box.setItemText(2, _translate("Frame", "Isoleucine/Valine"))
        self._validate_rama_case_combo_box.setItemText(3, _translate("Frame", "Preceding Proline"))
        self._validate_rama_case_combo_box.setItemText(4, _translate("Frame", "Trans Proline"))
        self._validate_rama_case_combo_box.setItemText(5, _translate("Frame", "Cis Proline"))
        self._validate_rama_hide_button.setText(_translate("Frame", "Hide"))
        self._validate_rama_sel_combo_box.setItemText(0, _translate("Frame", "Selected only"))
        self._validate_rama_sel_combo_box.setItemText(1, _translate("Frame", "All"))
        self._validate_rama_go_button.setText(_translate("Frame", "Make it so"))
        self.label_26.setText(_translate("Frame", "Peptide bond geometry"))
        self._validate_omega_show_button.setText(_translate("Frame", "Show"))
        self.label_27.setText(_translate("Frame", "Peptide biond geometry"))
        self._validate_omega_hide_button.setText(_translate("Frame", "Hide"))
        self.label_29.setText(_translate("Frame", "Cis"))
        self.label_30.setText(_translate("Frame", "Twisted"))
        self._validate_omega_update_button.setText(_translate("Frame", "Update list"))

