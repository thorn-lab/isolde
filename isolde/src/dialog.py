# @Author: Tristan Croll <tic20>
# @Date:   11-Jun-2019
# @Email:  tic20@cam.ac.uk
# @Last modified by:   tic20
# @Last modified time: 11-Jun-2019
# @License: Free for non-commercial use (see license.pdf)
# @Copyright: 2016-2019 Tristan Croll



'''
Dialog boxes for use by the ISOLDE gui
'''

def generic_warning(message):
    from PyQt5.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()

def choice_warning(message):
    '''
    Pop up a warning dialog box with the given message, and return True
    if the user wants to go ahead.
    '''
    from PyQt5.QtWidgets import QMessageBox
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
    reply = msg.exec_()
    if reply == QMessageBox.Ok:
        return True
    return False

def failed_template_warning(residue):
    '''
    Warning dialog handling the case where a template is not recognised by
    OpenMM when attempting to start a simulation.
    '''
    from PyQt5.QtWidgets import QMessageBox, QPushButton
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msgtext = 'Residue {} {} of chain {} (shown) does not match any template'\
        + ' in the molecular dynamics database. It may be missing atoms (have'\
        + ' you added hydrogens?) or be an unusual residue that has not been'\
        + ' parameterised. Choose what you wish to do with it from the options'\
        + ' below.'
    msg.setText(msgtext.format(residue.name, residue.number, residue.chain_id))

    addh = QPushButton('Add hydrogens and retry')
    msg.addButton(addh, QMessageBox.AcceptRole)
    exclude = QPushButton('Exclude residue from simulations and retry')
    msg.addButton(exclude, QMessageBox.RejectRole)
    abort = QPushButton('Abort')
    msg.addButton(abort, QMessageBox.NoRole)
    msg.exec_()
    btn = msg.clickedButton()
    # print("Button: {}".format(btn))
    if btn == addh:
        return "addh"
    if btn == exclude:
        return "exclude"
    return "abort"
