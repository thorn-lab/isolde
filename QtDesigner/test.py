# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'IsoldeWidget.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_isolde_widget(object):
    def setupUi(self, isolde_widget):
        isolde_widget.setObjectName("isolde_widget")
        isolde_widget.resize(419, 768)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(isolde_widget.sizePolicy().hasHeightForWidth())
        isolde_widget.setSizePolicy(sizePolicy)
        self._isolde_widget_contents = QtWidgets.QWidget()
        self._isolde_widget_contents.setObjectName("_isolde_widget_contents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self._isolde_widget_contents)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.toolBox = QtWidgets.QToolBox(self._isolde_widget_contents)
        self.toolBox.setObjectName("toolBox")
        self.page_7 = QtWidgets.QWidget()
        self.page_7.setGeometry(QtCore.QRect(0, 0, 401, 543))
        self.page_7.setObjectName("page_7")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.page_7)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tabWidget_2 = QtWidgets.QTabWidget(self.page_7)
        self.tabWidget_2.setObjectName("tabWidget_2")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget_2.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget_2.addTab(self.tab_2, "")
        self.verticalLayout_4.addWidget(self.tabWidget_2)
        self.toolBox.addItem(self.page_7, "")
        self._simulate_page = QtWidgets.QWidget()
        self._simulate_page.setGeometry(QtCore.QRect(0, 0, 401, 543))
        self._simulate_page.setObjectName("_simulate_page")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self._simulate_page)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self._simulate_page)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.basicTab = QtWidgets.QWidget()
        self.basicTab.setObjectName("basicTab")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.basicTab)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.scrollArea = QtWidgets.QScrollArea(self.basicTab)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents_4 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_4.setGeometry(QtCore.QRect(0, 0, 357, 371))
        self.scrollAreaWidgetContents_4.setObjectName("scrollAreaWidgetContents_4")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_4)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self._beginner_Mobile_Selection_Frame = QtWidgets.QFrame(self.scrollAreaWidgetContents_4)
        self._beginner_Mobile_Selection_Frame.setMinimumSize(QtCore.QSize(0, 100))
        self._beginner_Mobile_Selection_Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._beginner_Mobile_Selection_Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._beginner_Mobile_Selection_Frame.setObjectName("_beginner_Mobile_Selection_Frame")
        self.label_2 = QtWidgets.QLabel(self._beginner_Mobile_Selection_Frame)
        self.label_2.setGeometry(QtCore.QRect(10, 10, 221, 21))
        self.label_2.setObjectName("label_2")
        self.layoutWidget = QtWidgets.QWidget(self._beginner_Mobile_Selection_Frame)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 30, 260, 33))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_3 = QtWidgets.QLabel(self.layoutWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_4.addWidget(self.label_3)
        self.spinBox = QtWidgets.QSpinBox(self.layoutWidget)
        self.spinBox.setProperty("value", 5)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout_4.addWidget(self.spinBox)
        self.label_4 = QtWidgets.QLabel(self.layoutWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.layoutWidget1 = QtWidgets.QWidget(self._beginner_Mobile_Selection_Frame)
        self.layoutWidget1.setGeometry(QtCore.QRect(10, 60, 317, 33))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.spinBox_2 = QtWidgets.QSpinBox(self.layoutWidget1)
        self.spinBox_2.setProperty("value", 5)
        self.spinBox_2.setObjectName("spinBox_2")
        self.horizontalLayout_5.addWidget(self.spinBox_2)
        self.label_6 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_5.addWidget(self.label_6)
        self.verticalLayout_8.addWidget(self._beginner_Mobile_Selection_Frame)
        self.frame_4 = QtWidgets.QFrame(self.scrollAreaWidgetContents_4)
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.frame_4)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.simModeChooser = QtWidgets.QComboBox(self.frame_4)
        self.simModeChooser.setObjectName("simModeChooser")
        self.simModeChooser.addItem("")
        self.simModeChooser.addItem("")
        self.simModeChooser.addItem("")
        self.horizontalLayout_8.addWidget(self.simModeChooser)
        self.verticalLayout_8.addWidget(self.frame_4)
        self.crystalMapFrame = QtWidgets.QFrame(self.scrollAreaWidgetContents_4)
        self.crystalMapFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.crystalMapFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.crystalMapFrame.setObjectName("crystalMapFrame")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.crystalMapFrame)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.xtalChooseReflections = QtWidgets.QPushButton(self.crystalMapFrame)
        self.xtalChooseReflections.setObjectName("xtalChooseReflections")
        self.horizontalLayout_9.addWidget(self.xtalChooseReflections)
        self.xtalMapSpecs = QtWidgets.QPushButton(self.crystalMapFrame)
        self.xtalMapSpecs.setObjectName("xtalMapSpecs")
        self.horizontalLayout_9.addWidget(self.xtalMapSpecs)
        self.verticalLayout_8.addWidget(self.crystalMapFrame)
        self.EMMapFrame = QtWidgets.QFrame(self.scrollAreaWidgetContents_4)
        self.EMMapFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.EMMapFrame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.EMMapFrame.setObjectName("EMMapFrame")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.EMMapFrame)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.emChooseMaps = QtWidgets.QPushButton(self.EMMapFrame)
        self.emChooseMaps.setObjectName("emChooseMaps")
        self.horizontalLayout_10.addWidget(self.emChooseMaps)
        self.crystalMapFrame.raise_()
        self.crystalMapFrame.raise_()
        self.crystalMapFrame.raise_()
        self.emChooseMaps.raise_()
        self.verticalLayout_8.addWidget(self.EMMapFrame)
        self.verticalLayout_8.setStretch(2, 1)
        self.verticalLayout_8.setStretch(3, 1)
        self._beginner_Mobile_Selection_Frame.raise_()
        self.frame_4.raise_()
        self.EMMapFrame.raise_()
        self.crystalMapFrame.raise_()
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_4)
        self.verticalLayout_5.addWidget(self.scrollArea)
        self.tabWidget.addTab(self.basicTab, "")
        self.remodelTab = QtWidgets.QWidget()
        self.remodelTab.setObjectName("remodelTab")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.remodelTab)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.scrollArea_2 = QtWidgets.QScrollArea(self.remodelTab)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_5 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_5.setGeometry(QtCore.QRect(0, 0, 349, 382))
        self.scrollAreaWidgetContents_5.setObjectName("scrollAreaWidgetContents_5")
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_5)
        self.verticalLayout_6.addWidget(self.scrollArea_2)
        self.tabWidget.addTab(self.remodelTab, "")
        self.restrainTab = QtWidgets.QWidget()
        self.restrainTab.setObjectName("restrainTab")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.restrainTab)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.scrollArea_3 = QtWidgets.QScrollArea(self.restrainTab)
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollArea_3.setObjectName("scrollArea_3")
        self.scrollAreaWidgetContents_6 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_6.setGeometry(QtCore.QRect(0, 0, 67, 16))
        self.scrollAreaWidgetContents_6.setObjectName("scrollAreaWidgetContents_6")
        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_6)
        self.verticalLayout_7.addWidget(self.scrollArea_3)
        self.tabWidget.addTab(self.restrainTab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.goButton = QtWidgets.QToolButton(self._simulate_page)
        self.goButton.setObjectName("goButton")
        self.horizontalLayout.addWidget(self.goButton)
        self.pauseButton = QtWidgets.QToolButton(self._simulate_page)
        self.pauseButton.setObjectName("pauseButton")
        self.horizontalLayout.addWidget(self.pauseButton)
        self.commitButton = QtWidgets.QToolButton(self._simulate_page)
        self.commitButton.setObjectName("commitButton")
        self.horizontalLayout.addWidget(self.commitButton)
        self.discardButton = QtWidgets.QToolButton(self._simulate_page)
        self.discardButton.setObjectName("discardButton")
        self.horizontalLayout.addWidget(self.discardButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.minButton = QtWidgets.QPushButton(self._simulate_page)
        self.minButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.minButton.setObjectName("minButton")
        self.horizontalLayout_7.addWidget(self.minButton)
        self.equilButton = QtWidgets.QPushButton(self._simulate_page)
        self.equilButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.equilButton.setObjectName("equilButton")
        self.horizontalLayout_7.addWidget(self.equilButton)
        self.label_7 = QtWidgets.QLabel(self._simulate_page)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_7.addWidget(self.label_7)
        self.simTemp = QtWidgets.QLineEdit(self._simulate_page)
        self.simTemp.setObjectName("simTemp")
        self.horizontalLayout_7.addWidget(self.simTemp)
        self.tempDial = QtWidgets.QDial(self._simulate_page)
        self.tempDial.setMaximumSize(QtCore.QSize(50, 50))
        self.tempDial.setObjectName("tempDial")
        self.horizontalLayout_7.addWidget(self.tempDial)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.toolBox.addItem(self._simulate_page, "")
        self.verticalLayout_3.addWidget(self.toolBox)
        self.frame_2 = QtWidgets.QFrame(self._isolde_widget_contents)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.undoButton = QtWidgets.QPushButton(self.frame_2)
        self.undoButton.setObjectName("undoButton")
        self.horizontalLayout_2.addWidget(self.undoButton)
        self.redoButton = QtWidgets.QPushButton(self.frame_2)
        self.redoButton.setObjectName("redoButton")
        self.horizontalLayout_2.addWidget(self.redoButton)
        self.verticalLayout_3.addWidget(self.frame_2)
        self._experience_level_frame = QtWidgets.QFrame(self._isolde_widget_contents)
        self._experience_level_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._experience_level_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._experience_level_frame.setObjectName("_experience_level_frame")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self._experience_level_frame)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label = QtWidgets.QLabel(self._experience_level_frame)
        self.label.setObjectName("label")
        self.horizontalLayout_3.addWidget(self.label)
        self.comboBox = QtWidgets.QComboBox(self._experience_level_frame)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.horizontalLayout_3.addWidget(self.comboBox)
        self.verticalLayout_3.addWidget(self._experience_level_frame)
        isolde_widget.setWidget(self._isolde_widget_contents)

        self.retranslateUi(isolde_widget)
        self.toolBox.setCurrentIndex(1)
        self.tabWidget_2.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(isolde_widget)

    def retranslateUi(self, isolde_widget):
        _translate = QtCore.QCoreApplication.translate
        isolde_widget.setWindowTitle(_translate("isolde_widget", "ISOLDE (Interactive Modelling)"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab), _translate("isolde_widget", "Tab 1"))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), _translate("isolde_widget", "Tab 2"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_7), _translate("isolde_widget", "Build"))
        self.label_2.setText(_translate("isolde_widget", "Mobilise selected residue(s) "))
        self.label_3.setText(_translate("isolde_widget", "plus"))
        self.label_4.setText(_translate("isolde_widget", "residues before and after"))
        self.label_5.setText(_translate("isolde_widget", "plus residues coming within"))
        self.label_6.setText(_translate("isolde_widget", "Angstroms"))
        self.simModeChooser.setItemText(0, _translate("isolde_widget", "Crystallography mode"))
        self.simModeChooser.setItemText(1, _translate("isolde_widget", "EM mode"))
        self.simModeChooser.setItemText(2, _translate("isolde_widget", "Free mode (no maps)"))
        self.xtalChooseReflections.setText(_translate("isolde_widget", "Choose reflection data"))
        self.xtalMapSpecs.setText(_translate("isolde_widget", "Map specifications"))
        self.emChooseMaps.setText(_translate("isolde_widget", "Choose map(s)"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.basicTab), _translate("isolde_widget", "Setup"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.remodelTab), _translate("isolde_widget", "Remodel"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.restrainTab), _translate("isolde_widget", "Restrain"))
        self.goButton.setText(_translate("isolde_widget", "Go"))
        self.pauseButton.setText(_translate("isolde_widget", "Pause"))
        self.commitButton.setText(_translate("isolde_widget", "Save changes"))
        self.discardButton.setText(_translate("isolde_widget", "Discard changes"))
        self.minButton.setText(_translate("isolde_widget", "Min"))
        self.equilButton.setText(_translate("isolde_widget", "Equil"))
        self.label_7.setText(_translate("isolde_widget", "Temperature"))
        self.simTemp.setText(_translate("isolde_widget", "100"))
        self.toolBox.setItemText(self.toolBox.indexOf(self._simulate_page), _translate("isolde_widget", "Simulate"))
        self.undoButton.setText(_translate("isolde_widget", "Undo"))
        self.redoButton.setText(_translate("isolde_widget", "Redo"))
        self.label.setText(_translate("isolde_widget", "Experience level"))
        self.comboBox.setItemText(0, _translate("isolde_widget", "Beginner"))
        self.comboBox.setItemText(1, _translate("isolde_widget", "Intermediate"))
        self.comboBox.setItemText(2, _translate("isolde_widget", "Developer"))

