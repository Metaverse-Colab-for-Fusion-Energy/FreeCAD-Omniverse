# -*- coding: utf-8 -*-
# FreeCAD commands script for the FreeCAD to Omniverse connector workbench
# This script is based on the FreeCAD workbench tutorial in https://github.com/felipe-m/tutorial_freecad_wb (c) Felipe Machado 2017
# The current script was developed by Raska Soemantoro github.com/raska-s 2023
#***************************************************************************
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

from PySide2 import QtCore, QtGui, QtWidgets
import FreeCAD
import FreeCADGui
import Part
import os
import Mesh
import subprocess
import shutil
import Import
import re
import time
import ast
import asyncio
import datetime
import threading
from utils import *
from file_utils import *
__dir__ = os.path.dirname(__file__)

def GetCurrentSelection():
    # helper func to get user's freecad selection
    selection = FreeCADGui.Selection.getSelection()
    if str(selection) =='[<App::Origin object>]':
        print('[ERROR] Origin object selected. Select a valid mesh, part, or body object to push to Nucleus.')
        return None
    if len(selection) == 1:
        selected_object = selection[0]
        print("Selected object:", selected_object.Name)
        return selected_object
    else:
        print("[ERROR] No object selected or multiple objects selected! Select a single object from the Model tree to push to Nucleus.")
        return None


def FindUSDandSTPFiles(usdlink):
    """
    Finds USD and STEP files associated with a project on Nucleus.

    Args:
        usdlink (str): The Nucleus URL of the project.

    Returns:
        tuple: (stdout_lines, stderr_output)
    """
    print('Finding asset files in the project folder ...')

    # Assemble paths and command
    script_dir = GetFetcherScriptsDirectory().replace(" ", "` ")
    batch_file = GetBatchFileName()
    batch_path = os.path.join(script_dir, batch_file)
    local_dir = GetLocalDirectoryName()

    cmd = f'{batch_path} --local_directory {local_dir} --nucleus_url {usdlink} --find_stp_and_usd_files'
    print(cmd)

    # Run the command
    process = subprocess.Popen(
        ['powershell', cmd],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    stdout_lines = stdout.decode('utf-8').split('\r\n')
    stderr_output = stderr.decode('utf-8')

    # Output results
    for line in stdout_lines:
        print('[OmniClient]', line)
    print('ERRORS:', stderr_output)

    return stdout_lines, stderr_output

def DownloadUSDFromNucleus(usdlink):
    """
    Deprecated function. USDs are now not downloaded from Nucleus. Attempts to pull a USD file from Nucleus and insert the resulting STL if permitted.
    
    Args:
        usdlink (str): The Nucleus URL to download from.

    Returns:
        tuple: (stdout_output, stderr_output)
    """
    permission = GetCurrentUSDPermissions()
    print(f'File permission: {permission}')

    if permission == 'NO_ACCESS':
        print(f'[ERROR] NO_PERMISSION: Cannot access USD file: {usdlink}')
        print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
        print('Try logging in under a different username: log out through the nucleus. SIGNOUT BUTTON IS WIP')
        return 'FAIL', 'NO_PERMISSION'

    if permission is None:
        print(f'[ERROR] PERMISSION_NOT_FOUND: Cannot access USD file: {usdlink}')
        print('[ERROR] You have not entered a valid USD link.')
        return 'FAIL', 'PERMISSION_NOT_FOUND'

    if permission != 'OK_ACCESS':
        return 'FAIL', 'UNKNOWN_PERMISSION_STATUS'

    # Permission OK — proceed with download
    doc = FreeCAD.ActiveDocument  # Required to allow Mesh.insert
    script_dir = GetFetcherScriptsDirectory().replace(" ", "` ")
    batch_file = GetBatchFileName()
    batch_path = os.path.join(script_dir, batch_file)

    local_dir = GetLocalDirectoryName()
    token = str(RandomTokenGenerator())
    stl_filename = f'{token}download.stl'
    stl_path = os.path.join(local_dir, stl_filename)

    print(f'Unique version identifier: {token}')
    
    cmd = (
        f'{batch_path} --nucleus_url {usdlink} '
        f'--local_directory {local_dir.replace(" ", "` ")} '
        f'--pull --token {token}'
    )
    print(f'[CMD] {cmd}')

    process = subprocess.Popen(
        ['powershell', cmd],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    stdout_decoded = stdout.decode('utf-8')
    stderr_decoded = stderr.decode('utf-8')

    if os.path.exists(stl_path):
        Mesh.insert(stl_path)
    else:
        print('[ERROR] DLOAD_FAIL: USD download failed!')

    return stdout_decoded, stderr_decoded




def CreateNewAssemblyOnNucleus(projectURL, assembly_name='assembly',
                                assembly_items_usd_links=None, assembly_items_stp_links=None, token=None):
    """
    Creates a new assembly in a Nucleus project and returns its USD link if successful.
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    cmd = (
        f'{batch_path} --nucleus_url {projectURL} --create_new_assembly '
        f'--assembly_name {assembly_name}'
    )

    if assembly_items_usd_links and assembly_items_stp_links:
        cmd += f' --asset_usd_links {" ".join(assembly_items_usd_links)}'
        cmd += f' --asset_stp_links {" ".join(assembly_items_stp_links)}'

    if token:
        cmd += f' --token {token}'

    print(f'[CMD] {cmd}')
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout_lines = stdout.decode().split('\n')
    stderr_lines = stderr.decode().split('\n')

    # Find the generated assembly USD link
    assembly_usd_link = next((line.strip() for line in stdout_lines
                              if '.usd' in line and f'{projectURL}/assembly' in line), None)

    return stdout_lines, stderr_lines, assembly_usd_link

def AddCheckpointToNucleusAsset(url, custom_checkpoint, token=None, filetype='usd'):
    """
    Adds a checkpoint comment to a Nucleus asset (USD or non-USD).

    Args:
        url (str): Nucleus file URL.
        custom_checkpoint (str): Checkpoint label.
        token (str, optional): Upload token.
        filetype (str): 'usd' (default) or 'non_usd'.
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    checkpoint = f'"{custom_checkpoint}"'
    flag = '--add_checkpoint_to_usd' if filetype == 'usd' else '--add_checkpoint_to_non_usd'

    cmd = f'{batch_path} --nucleus_url {url} {flag} --custom_checkpoint {checkpoint}'
    if token:
        cmd += f' --token {token}'

    print(f'[CMD] {cmd}')
    subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()


def FindExistingAssembliesOnNucleus(projectURL):
    """
    Searches for existing assembly USD files in a given Nucleus project.
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    cmd = f'{batch_path} --nucleus_url {projectURL} --find_existing_assemblies'
    print(f'[CMD] {cmd}')

    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout_lines = stdout.decode().split('\n')
    stderr_lines = stderr.decode().split('\n')

    links = [line.strip() for line in stdout_lines if '/assembly' in line and '.usd' in line]
    return stdout_lines, stderr_lines, links or None


def GetPrimReferenceXForms(assemblyURL, token=None):
    """
    Fetches reference, transform, rotation, and scale data of prims in a Nucleus assembly.

    Returns:
        tuple: (stdout_lines, stderr_lines, list of reference dictionaries or None)
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    cmd = f'{batch_path} --nucleus_url {assemblyURL} --get_prim_reference_xforms'
    if token:
        cmd += f' --token {token}'
    print(f'[CMD] {cmd}')

    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout_lines = stdout.decode().split('\n')
    stderr_lines = stderr.decode().split('\n')

    prim_data = []
    for line in stdout_lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) == 4 and parts[0]:
            step_path = parts[0].replace('.usda', '.stp').replace('.usd', '.stp')
            prim_data.append({
                "ref-path": parts[0],
                "step-path": step_path,
                "transform": ast.literal_eval(parts[1]),
                "rot-xyz": ast.literal_eval(parts[2]),
                "scale": ast.literal_eval(parts[3])
            })

    return stdout_lines, stderr_lines, prim_data or None




def _DownloadCmdWrapper(stplink, usdlink, token, custom_checkpoint=None):
    """
    Downloads a STEP file from Nucleus and attaches metadata to the imported object. Used by assembly mode only.
    """
    if not stplink:
        return None

    GetAuthCheck(stplink, filetype='stp')
    print(f'Pulling from {stplink}')
    ok, obj, output, error, fc_err = DownloadSTPFromNucleus(stplink, token=token, custom_checkpoint=custom_checkpoint)
    print('\n'.join(f'OmniClient: {line}' for line in output.split('\r\n')))
    print('ERRORS', error)
    label = GetComponentNameFromStplink(stplink)
    properties = {
        "Label": label,
        "Nucleus_link_stp": stplink,
        "Nucleus_link_usd": usdlink,
        "Nucleus_version_id": token,
        "Last_Nucleus_sync_time": time.strftime(" %d %b  %Y %H:%M:%S", time.localtime())
    }

    for key, val in properties.items():
        obj = attachNewStringProperty(obj, property_name=key, property_value=val)

    return obj

class _DownloadCmd:
    """Command to download geometry from Nucleus."""

    def Activated(self):
        token = str(RandomTokenGenerator())
        usdlink = GetCurrentUSDLink()
        stplink = GetCurrentSTPLinkNoPrint()

        if not stplink:
            print('No STPLINK')
            return None
        print(f'Pulling from {stplink}')
        ok, obj, output, error, fc_err = DownloadSTPFromNucleus(stplink, token=token)

        if ok:
            print('\n'.join(f'OmniClient: {line}' for line in output.split('\r\n')))
            print('ERRORS', error)
            label = GetComponentNameFromStplink(stplink)
            props = {
                "Label": label,
                "Nucleus_link_stp": stplink,
                "Nucleus_link_usd": usdlink,
                "Nucleus_version_id": token,
                "Last_Nucleus_sync_time": time.strftime(" %d %b  %Y %H:%M:%S", time.localtime())
            }
            for key, val in props.items():
                obj = attachNewStringProperty(obj, property_name=key, property_value=val)
        else:
            QtWidgets.QMessageBox.critical(
                None,
                'Omniverse Connector for FreeCAD',
                fc_err
            )

    def GetResources(self):
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_pull.svg',
            'MenuText': QtCore.QT_TRANSLATE_NOOP('OVconnect_pull_from_nucleus', 'Pull from Nucleus'),
            'ToolTip': QtCore.QT_TRANSLATE_NOOP('OVconnect_pull_from_nucleus', 'Pulls geometry from Omniverse Nucleus')
        }

    def IsActive(self):
        def is_valid(url_func, perm_func):
            return perm_func() == 'OK_ACCESS' and url_func() is not None

        return (
            FreeCAD.ActiveDocument is not None and
            is_valid(GetCurrentSTPLinkNoPrint, GetCurrentSTPPermissions) and
            is_valid(GetCurrentUSDLinkNoPrint, GetCurrentUSDPermissions)
        )

class _ClearJunkCmd:
    """
    Deprecated class, cleanup of temp data is now done automatically.
    Command to clear session data
    """
    def Activated(self):
        # what is done when the command is clicked
        current_project_link = GetCurrentProjectLinkNoPrint()
        last_project_link = GetLastProjectLinkNoPrint()
        ClearLocalDirectory()
        FreeCAD.assembly_usd_link=None

        if current_project_link != None:
            SaveLastProjectLinkAsTextFile(current_project_link)
        elif last_project_link!=None:
            SaveLastProjectLinkAsTextFile(last_project_link)
    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_clear_junk_files',
            'Clear current session')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_clear_junk_files',
            'Clear current session')
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_clearjunk.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        # The command will be active only if there is an active document
        return not FreeCAD.ActiveDocument is None

class _UploadCmd:
    """Button to upload a selected component to Nucleus."""
    def Activated(self):
        selection = GetCurrentSelection()
        if not selection:
            return

        usd_local, stp_local = GetCurrentUSDLinkNoPrint(), GetCurrentSTPLinkNoPrint()
        token = str(RandomTokenGenerator())

        # Resolve potential link conflicts
        def resolve_link_conflict(label, local, stored):
            if local == stored:
                return local
            options = [stored, local]
            choice, ok = QtWidgets.QInputDialog.getItem(None, "Omniverse Connector for FreeCAD",
                                                    f'Found conflict in Nucleus {label} links. Select one to push to:',
                                                    options, 0, False)
            return choice if ok else None

        if 'Nucleus_link_usd' in selection.PropertiesList and 'Nucleus_link_stp' in selection.PropertiesList:
            usd_fc, stp_fc = selection.Nucleus_link_usd, selection.Nucleus_link_stp
            usdlink = resolve_link_conflict("USD", usd_local, usd_fc)
            stplink = resolve_link_conflict("STP", stp_local, stp_fc)
            if not usdlink or not stplink:
                QtWidgets.QMessageBox.critical(None, "Omniverse Connector for FreeCAD", "Failed to push to Nucleus!")
                return
        else:
            usdlink, stplink = usd_local, stp_local

        # Upload USD
        if usdlink:
            print(f'Pushing {selection.Name} to {usdlink}')
            output, error = UploadUSDToNucleus(usdlink, selection, token=token)
            print('\n'.join(f'OmniClient {line}' for line in output.split('\r\n')))
            print('ERRORS', error)
            selection = attachNewStringProperty(selection, "Nucleus_link_usd", usdlink)

        # Upload STP
        if stplink:
            print(f'Pushing {selection.Name} to {stplink}')
            output, error = UploadSTPToNucleus(stplink, selection, token=token)
            print('\n'.join(f'OmniClient {line}' for line in output.split('\r\n')))
            print('ERRORS', error)
            props = {
                "Label": GetComponentNameFromStplink(stplink),
                "Nucleus_link_stp": stplink,
                "Nucleus_version_id": token,
                "Last_Nucleus_sync_time": time.strftime(" %d %b %Y %H:%M:%S", time.localtime())
            }
            for k, v in props.items():
                selection = attachNewStringProperty(selection, k, v)

        # Upload to secondary USD if enabled
        if getattr(FreeCAD, 'is_enabled_secondary_usdlink', False):
            secondary_usd = GetCurrentUSDLinkNoPrint(secondary=True)
            output, error = UploadUSDToNucleus(secondary_usd, selection, token=token, overwrite_history=True, secondary=True)
            print('\n'.join(f'OmniClient {line}' for line in output.split('\r\n')))
            print('ERRORS', error)

    def GetResources(self):
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_push.svg',
            'MenuText': QtCore.QT_TRANSLATE_NOOP('OVconnect_push_to_nucleus', 'Push to Nucleus'),
            'ToolTip': QtCore.QT_TRANSLATE_NOOP('OVconnect_push_to_nucleus', 'Pushes selected geometry to Omniverse Nucleus')
        }

    def IsActive(self):
        def is_valid(url_func, perm_func):
            return perm_func() == 'OK_ACCESS' and url_func() is not None

        return (
            FreeCAD.ActiveDocument is not None and
            is_valid(GetCurrentSTPLinkNoPrint, GetCurrentSTPPermissions) and
            is_valid(GetCurrentUSDLinkNoPrint, GetCurrentUSDPermissions)
        )


class _CheckConnectionCmd:
    """DEPRECATED CLASS!
    placeholder command to test user authentication - this is now automated"""
    def Activated(self):
        # what is done when the command is clicked
        usdlink = GetCurrentUSDLink()
        if usdlink is not None:
            GetAuthCheck(usdlink)
    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_user_auth',
            'Validate Nucleus Connection')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_user_auth',
            'Validate Nucleus Connection')
        return {
            'Pixmap': __dir__ + '/icons/ovConnect_conn_sync.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        # The command will be active if there is an active document
        return not FreeCAD.ActiveDocument is None

class AssemblyChecklistDialog(QtWidgets.QDialog):
    """Checklist Dialog for creating new assembly - user can select assembly components and set assembly name"""
    def __init__(
        self,
        name,
        stringlist=None,
        checked=False,
        icon=None,
        parent=None,
        ):
        super(AssemblyChecklistDialog, self).__init__(parent)
        self.name = name
        self.icon = icon
        self.model = QtGui.QStandardItemModel()
        self.listView = QtWidgets.QListView()
        for string in stringlist:
            item = QtGui.QStandardItem(string)
            item.setCheckable(True)
            check = \
                (QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
            item.setCheckState(check)
            self.model.appendRow(item)

        self.listView.setModel(self.model)

        self.okButton = QtWidgets.QPushButton('Create new assembly')
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.selectButton = QtWidgets.QPushButton('Select All')
        self.unselectButton = QtWidgets.QPushButton('Unselect All')

        self.assembly_name_text = QtWidgets.QLabel('New assembly name:')
        self.assembly_name_input = QtWidgets.QLineEdit()
        self.assembly_items_text = QtWidgets.QLabel('Select assembly items:')

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)
        hbox.addWidget(self.selectButton)
        hbox.addWidget(self.unselectButton)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.assembly_name_text)
        vbox.addWidget(self.assembly_name_input)
        vbox.addWidget(self.assembly_items_text)
        vbox.addWidget(self.listView)
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setWindowTitle(self.name)
        if self.icon:
            self.setWindowIcon(self.icon)

        self.okButton.clicked.connect(self.onAccepted)
        self.cancelButton.clicked.connect(self.reject)
        self.selectButton.clicked.connect(self.select)
        self.unselectButton.clicked.connect(self.unselect)

    def onAccepted(self):
        self.choices = [self.model.item(i).text() for i in
                        range(self.model.rowCount())
                        if self.model.item(i).checkState()
                        == QtCore.Qt.Checked]
        self.assembly_name = self.assembly_name_input.text()
        self.accept()

    def select(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def unselect(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

def GetAvailableLiveSessions(usdlink):
    """
    Returns available live sessions for a given USD file on Nucleus.
    """
    doc = FreeCAD.ActiveDocument
    FreeCAD.setActiveDocument(doc.Name)
    error_code = None
    success=None
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName(live=True)
    batchfilepath = os.path.join(batchfilepath, batchfilename)

    cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --find_sessions'
    print(cmd)
    # print(cmd) # FOR DEBUG
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    stdout = stdout.split('\r\n')
    list_of_sessions = []
    for line in stdout:
        if 'NO_SESSION_FOUND' in line:
            success = False
            error_code = line
        elif 'SESSION_ID' in line:
            list_of_sessions.append(line.split(' ')[1])

    if list_of_sessions != []:
        success=True
    else:
        success=False
        list_of_sessions = None
    return success, list_of_sessions, error_code

class OmniverseAssemblyPanel:
    """
    Assembly Panel mega-class. This class handles moving of assembly, handling of live assembly, pushing/pulling, etc.
    """
    def __init__(self, widget):
        self.form = widget
        self.layout = QtWidgets.QVBoxLayout(widget)
        self.currentProjectURL = GetCurrentProjectLinkNoPrint()
        self.assemblyUSDLink = getattr(FreeCAD, 'assembly_usd_link', None)
        self.proc = None
        self.valid_freecad_objects = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj, 'Nucleus_link_usd')]
        self._build_ui()

    def _build_ui(self):
        self.status_label = QtWidgets.QLabel(' Status: \u2705 Ready' if self.assemblyUSDLink else ' Status: \u274c')
        current_assembly = self.assemblyUSDLink.split('/')[-1] if self.assemblyUSDLink else 'No assembly selected'
        self.assy_label = QtWidgets.QLabel(f' \u2705 Current assembly: {current_assembly}' if self.assemblyUSDLink else f' \u274c {current_assembly}')
        project_label = QtWidgets.QLabel(f' \u2705 Current project: {self.currentProjectURL}')
        buttons = [
            ("Make assembly from workspace objects", self.flow_create_new_assembly),
            ("Import existing assembly into workspace", self.flow_open_existing_assembly),
            ("Upload assembly changes", self.flow_upload_assembly_changes),
            ("Fetch new assembly changes", self.flow_download_assembly_changes),
        ]
        for text, func in buttons:
            btn = QtWidgets.QPushButton(text); btn.clicked.connect(func); self.layout.addWidget(btn)
        self.live_mode_button = QtWidgets.QPushButton("(EXPERIMENTAL) Live assembly mode")
        self.live_mode_button.setCheckable(True)
        self.live_mode_button.clicked.connect(self.flow_start_live_assy_mode)
        for w in [QtWidgets.QLabel("Assembly Panel"), self.status_label, project_label, self.assy_label, self.live_mode_button]:
            self.layout.addWidget(w)

    def _warn(self, msg):
        print('[WARN]', msg)
        box = QtWidgets.QMessageBox(); box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setText(msg); box.exec_()

    def flow_create_new_assembly(self):
        objs, labels = GetListOfAssemblyObjects(self.currentProjectURL)
        if not objs: return self._warn("No pushed components found!")
        form = AssemblyChecklistDialog("Create new assembly", labels, checked=True)
        if not form.exec_(): return
        name = form.assembly_name
        if not name or not text_follows_rules(name): return self._warn("Invalid assembly name")
        selected = GetSelectedAssemblyObjects(objs, labels, form.choices)
        usd_links = [o.Nucleus_link_usd for o in selected]
        stp_links = [o.Nucleus_link_stp for o in selected]
        token = str(RandomTokenGenerator())
        out, err, link = CreateNewAssemblyOnNucleus(self.currentProjectURL, name, usd_links, stp_links, token)
        print('\n'.join(out + err))
        for usd in usd_links:
            AddCheckpointToNucleusAsset(usd, f"Add asset to assembly in {link.split('/')[-1]}", token)
        FreeCAD.assembly_usd_link = link
        self.assy_label.setText(f' \u2705 Current assembly: {link.split("/")[-1]}')
        self.status_label.setText(' Status: \u2705 Ready')

    def flow_open_existing_assembly(self):
        out, err, links = FindExistingAssembliesOnNucleus(self.currentProjectURL)
        if not links: return self._warn("No existing assemblies found.")
        names = [l.split('/')[-1] for l in links]
        name, ok = QtWidgets.QInputDialog.getItem(self.form, "Select assembly", "Import:", names, 0, False)
        if not ok: return
        link = next(l for l in links if name in l)
        FreeCAD.assembly_usd_link = link
        token = str(RandomTokenGenerator())
        _, _, data = GetPrimReferenceXForms(link, token)
        for d in data:
            print(d['step-path'])
        for d in data:
            obj = _DownloadCmdWrapper(d['step-path'], d['ref-path'], token, f"Imported as {name}")
            obj.Placement.Base = FreeCAD.Vector(d['transform'])
            obj.Placement.Rotation = FreeCAD.Rotation(*d['rot-xyz'][::-1])
        AddCheckpointToNucleusAsset(link, "Imported assembly into FreeCAD", token)
        self.assy_label.setText(f' \u2705 Current assembly: {link.split("/")[-1]}')
        self.status_label.setText(' Status: \u2705 Ready')

    def flow_upload_assembly_changes(self):
        link = getattr(FreeCAD, 'assembly_usd_link', None)
        if not link: return self._warn("No assembly link found.")
        usd_links, pos = get_assembly_component_placement('base')
        _, rot = get_assembly_component_placement('rotation')
        MoveAssemblyXformPositions(link, usd_links, pos, rot, token=str(RandomTokenGenerator()))

    def flow_download_assembly_changes(self):
        link = getattr(FreeCAD, 'assembly_usd_link', None)
        if not link: return self._warn("No assembly link specified.")
        token = str(RandomTokenGenerator())
        _, _, data = GetPrimReferenceXForms(link, token)
        valid_objs = [o for o in FreeCAD.ActiveDocument.Objects if hasattr(o, 'Nucleus_link_usd')]
        for d in data:
            obj = next(o for o in valid_objs if o.Nucleus_link_usd == d['ref-path'])
            obj.Placement.Base = FreeCAD.Vector(d['transform'])
            obj.Placement.Rotation = FreeCAD.Rotation(*d['rot-xyz'][::-1])

    def flow_start_live_assy_mode(self):
        if not self.live_mode_button.isChecked():
            self.live_mode_button.setText("(EXPERIMENTAL) Live assembly mode")
            return self.kill_live_process()
        link = getattr(FreeCAD, 'assembly_usd_link', None)
        if not link: return self._warn("No assembly link specified.")
        success, sessions, _ = GetAvailableLiveSessions(link)
        if not success: return self._warn("No live sessions found.")
        session, ok = QtWidgets.QInputDialog.getItem(self.form, "Select session", "Available:", sessions, 0, False)
        if not ok: return
        self.live_mode_button.setText("(EXPERIMENTAL) Live assembly mode ACTIVE")
        self.proc = QtCore.QProcess()
        self.proc.readyReadStandardOutput.connect(self.move_components_on_stdout)
        self.proc.readyReadStandardError.connect(lambda: print(str(self.proc.readAllStandardError())))
        self.proc.stateChanged.connect(lambda s: print(f"State: {['Not running','Starting','Running'][s]}"))
        self.proc.finished.connect(lambda: setattr(self, 'proc', None))
        self.proc.start("powershell", [make_live_start_command(link, session)])

    def move_components_on_stdout(self):
        lines = str(self.proc.readAllStandardOutput())
        if self.currentProjectURL not in lines: return
        entries = [e.strip() for e in lines.split('|') if e]
        for i in range(0, len(entries), 3):
            usd, t, r = entries[i:i+3]
            obj = next(o for o in self.valid_freecad_objects if o.Nucleus_link_usd == usd)
            obj.Placement.Base = FreeCAD.Vector(ast.literal_eval(t))
            obj.Placement.Rotation = FreeCAD.Rotation(*ast.literal_eval(r)[::-1])

    def kill_live_process(self):
        if self.proc:
            self.proc.write(bytes("q\n", 'utf-8'))
            self.proc.waitForReadyRead()
            self.proc.closeWriteChannel()
            self.proc.waitForFinished()
            print("Live session terminated.")

def MoveAssemblyXformPositions(assembly_url, usd_links, translations, rotations, token=None):
    """
    Function to send a message to Nucleus to move objects in an assembly. Only used for batch assembly workflow.
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    cmd = f'{batch_path} --nucleus_url {assembly_url} --move_assembly ' \
          f'--set_rot_xyz {parse_list_into_set_srt_command_arg(rotations)} ' \
          f'--set_transform {parse_list_into_set_srt_command_arg(translations)} ' \
          f'--asset_usd_links {" ".join(usd_links)}'

    if token:
        cmd += f' --token {token}'

    print(cmd)
    process = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode().splitlines(), stderr.decode().splitlines()

class OmniConnectionSettingsPanel:
    # Omniverse connection settings panel
    def __init__(self, widget):
        self.form = widget
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Omniverse Connection Settings"))

        self.currentProjectURL_text = QtWidgets.QLabel(" ❌ No project Nucleus URL specified ")
        self.selected_asset_text = QtWidgets.QLabel(" ❌ No STP asset selected.")
        self.selected_asset_usd_text = QtWidgets.QLabel(' ❌ No corresponding USD asset selected.')

        stp, usd, proj = GetCurrentSTPLinkNoPrint(), GetCurrentUSDLinkNoPrint(), GetCurrentProjectLinkNoPrint()
        if stp: self.selected_asset_text.setText(" ✅ Current STP asset: "+stp.split('/')[-1])
        if usd: self.selected_asset_usd_text.setText(' ✅ Corresponding USD: '+ usd.split('/')[-1])
        if proj: self.currentProjectURL_text.setText(" ✅ Current project URL: "+proj)

        buttons = [
            ("Open existing project", self.inputProjectURL),
            ("Create new project", self.createNewProject),
            ("Create new asset in project", self.dialogBoxCreateNewAsset),
            ("Browse project assets", self.getListItem),
            ("Disconnect from project", self.disconnect_from_project),
            ("About", self.show_about_page)
        ]

        for label, func in buttons:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(func)
            layout.addWidget(btn)

        layout.addWidget(self.currentProjectURL_text)
        layout.addWidget(self.selected_asset_text)
        layout.addWidget(self.selected_asset_usd_text)
        self.form.setLayout(layout)

    def show_about_page(self):
        dialog = QtWidgets.QInputDialog(self.form)
        version_info = QtWidgets.QLabel("FreeCAD Omniverse Connector\nVersion 3.0.3 \n© 2024 The University of Manchester")
        dialog.show()
        dialog.findChild(QtWidgets.QLineEdit).hide()
        dialog.layout().itemAt(0).widget().hide()
        dialog.layout().insertWidget(1, version_info)
        button_box = dialog.findChild(QtWidgets.QDialogButtonBox)
        button_box.clear()
        adv_btn = QtWidgets.QPushButton("Advanced")
        adv_btn.clicked.connect(self.show_advanced_page)
        button_box.addButton(adv_btn, QtWidgets.QDialogButtonBox.ActionRole)
        dialog.exec_()

    def show_advanced_page(self):
        # Create a dialog for Advanced options
        advanced_dialog = QtWidgets.QDialog()
        advanced_dialog.setWindowTitle("Advanced Options")
        main_layout = QtWidgets.QVBoxLayout(advanced_dialog)

        # Main label
        advanced_label = QtWidgets.QLabel("Advanced Options")
        main_layout.addWidget(advanced_label)

        grid_layout = QtGui.QGridLayout()

        usd_toggle = QtWidgets.QCheckBox("Enable direct USD push")
        usd_link_label = QtWidgets.QLabel("Nucleus USD link:")
        usd_link = QtWidgets.QLineEdit()
        usd_warning_label = QtWidgets.QLabel("")
        usd_warning_label.setStyleSheet("color: red;")  
        usd_warning_label.hide()

        grid_layout.addWidget(usd_toggle, 0, 0, 1, 1)
        grid_layout.addWidget(usd_link_label, 1, 1, 1, 1)
        grid_layout.addWidget(usd_link, 1, 2, 1, -1)
        grid_layout.addWidget(usd_warning_label, 2, 1, 1, -1)

        if 'is_enabled_secondary_usdlink' not in dir(FreeCAD):
            FreeCAD.is_enabled_secondary_usdlink = False

        if FreeCAD.is_enabled_secondary_usdlink:
            usd_toggle.setChecked(True)
            FreeCAD.secondary_usdlink = GetCurrentUSDLinkNoPrint(secondary=True)
            usd_link.setText(FreeCAD.secondary_usdlink)
            usd_link.setEnabled(True)
        else:
            usd_toggle.setChecked(False)
            usd_link.setEnabled(False)

        if GetCurrentUSDPermissions(secondary=True) != 'OK_ACCESS':
            usd_warning_label.setText("Invalid access permissions to the USD link.")
            usd_warning_label.show()

        # Ensure the text field remains populated if the link exists
        if hasattr(FreeCAD, 'secondary_usdlink') and FreeCAD.secondary_usdlink:
            usd_link.setText(FreeCAD.secondary_usdlink)

        usd_toggle.toggled.connect(lambda checked: usd_link.setEnabled(checked))
        step_toggle = QtWidgets.QCheckBox("Enable direct STEP push")
        step_link_label = QtWidgets.QLabel("Nucleus STEP link:")
        step_link = QtWidgets.QLineEdit()
        step_warning_label = QtWidgets.QLabel("")
        step_warning_label.setStyleSheet("color: red;")  # Warning text in red
        step_warning_label.hide()

        if 'is_enabled_secondary_stplink' not in dir(FreeCAD):
            FreeCAD.is_enabled_secondary_stplink = False

        if FreeCAD.is_enabled_secondary_stplink:
            step_toggle.setChecked(True)
            FreeCAD.secondary_stplink = GetCurrentSTPLinkNoPrint(secondary=True)
            step_link.setText(FreeCAD.secondary_stplink)
            step_link.setEnabled(True)
        else:
            step_toggle.setChecked(False)
            step_link.setEnabled(False)

        if hasattr(FreeCAD, 'secondary_stplink') and FreeCAD.secondary_stplink:
            step_link.setText(FreeCAD.secondary_stplink)
        main_layout.addLayout(grid_layout)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(advanced_dialog.accept)
        button_box.rejected.connect(advanced_dialog.reject)
        main_layout.addWidget(button_box)

        if advanced_dialog.exec_() == QtWidgets.QDialog.Accepted:
            if usd_toggle.isChecked():
                secondary_usdlink = usd_link.text()
                _, _, permission = GetAuthCheck(secondary_usdlink, filetype='usd', secondary=True)
                if permission == 'OK_ACCESS':
                    print(f"USD Secondary Link: {secondary_usdlink}")
                    SaveSecondaryUSDLinkAsTextFile(secondary_usdlink)
                    FreeCAD.is_enabled_secondary_usdlink = True
                    FreeCAD.secondary_usdlink = secondary_usdlink
                else:
                    FreeCAD.is_enabled_secondary_usdlink = False
                    FreeCAD.secondary_usdlink = secondary_usdlink
            else:
                FreeCAD.is_enabled_secondary_usdlink = False

            # Handle STEP link
            if step_toggle.isChecked():
                secondary_stplink = step_link.text()
                _, _, permission = GetAuthCheck(secondary_stplink, filetype='stp', secondary=True)
                if permission == 'OK_ACCESS':
                    print(f"STP Secondary Link: {secondary_stplink}")
                    SaveSecondarySTPLinkAsTextFile(secondary_stplink)
                    FreeCAD.is_enabled_secondary_stplink = True
                    FreeCAD.secondary_stplink = secondary_stplink
                else:
                    FreeCAD.is_enabled_secondary_stplink = False
                    FreeCAD.secondary_stplink = secondary_stplink
            else:
                FreeCAD.is_enabled_secondary_stplink = False


    def disconnect_from_project(self):
        if not getattr(FreeCAD, 'is_connected_to_nucleus_project', False):
            self._warn("No Nucleus project currently connected!")
            return

        SaveLastProjectLinkAsTextFile(GetCurrentProjectLinkNoPrint() or GetLastProjectLinkNoPrint())
        last_project_link = GetLastProjectLinkNoPrint()
        current_project_link = GetCurrentProjectLinkNoPrint()
        ClearLocalDirectory()
        if current_project_link != None:
            SaveLastProjectLinkAsTextFile(current_project_link)
        elif last_project_link!=None:
            SaveLastProjectLinkAsTextFile(last_project_link)
        FreeCAD.assembly_usd_link = None
        FreeCAD.is_connected_to_nucleus_project = False
        self.currentProjectURL_text.setText('❌ No project Nucleus URL specified.')
        self.selected_asset_text.setText(' ❌ No STP asset selected.')
        self.selected_asset_usd_text.setText(' ❌ No corresponding USD asset selected.')

    def createNewProject(self):
        dialog = QtWidgets.QInputDialog(self.form)
        dialog.setWindowTitle('Omniverse Connector for FreeCAD')
        dialog.setLabelText('Create new project on Nucleus')
        dialog.show()

        dialog.findChild(QtWidgets.QLineEdit).hide()

        text_format_rules = QtWidgets.QLabel("Project names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")

        hostname_prompt = QtWidgets.QLabel("Nucleus host name:")
        input_hostname = QtWidgets.QLineEdit()
        projectname_prompt = QtWidgets.QLabel("New project name:")
        input_projectname = QtWidgets.QLineEdit()
        make_project_private_bool = QtWidgets.QCheckBox("Make project private")

        dialog.layout().insertWidget(1, hostname_prompt)
        dialog.layout().insertWidget(2, input_hostname)
        dialog.layout().insertWidget(3, projectname_prompt)
        dialog.layout().insertWidget(4, input_projectname)
        dialog.layout().insertWidget(5, text_format_rules)
        dialog.layout().insertWidget(6, make_project_private_bool)

        dialog.exec_()
        hostname_new_project = input_hostname.text()
        name_new_project = input_projectname.text()


        if make_project_private_bool.isChecked() == True:
            public_project=False
        else:
            public_project=True

        if hostname_new_project!='':
            if name_new_project!='':
                if text_follows_rules(name_new_project) ==True:
                    if no_restricted_strings_in_project_link(name_new_project) == True:
                        ok, stdout, stderr = CreateNewProjectOnNucleus(host_name = hostname_new_project, project_name = name_new_project, make_public = public_project)
                        if ok==False:
                            print('[ERROR] Failed to create new project!')
                            error_warning_text = None
                            for line in stdout:
                                if 'ERROR' in line:
                                    error_warning_text = line
                                    print(line)
                                else:
                                    print('OmniClient:'+line)
                            if error_warning_text == None:
                                error_warning_text = 'Failed to create new project!'

                            msgBox = QtWidgets.QMessageBox()
                            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                            msgBox.setText(error_warning_text)
                            msgBox.exec_()
                        elif ok==True:
                            stdout = [line.strip() for line in stdout]
                            projectURL = [line for line in stdout if 'omniverse://'+hostname_new_project in line][0]
                            print('Creating new project at '+ projectURL)
                            check_project_ok = self.checkProjectURL(inputProjectURL=projectURL)
                            if check_project_ok ==True:
                                delete_asset_localdata()
                                self.selected_asset_text.setText(' \u274c No STP asset selected.')
                                self.selected_asset_usd_text.setText(' \u274c No corresponding USD asset selected.')
                    else:
                        msgBox = QtWidgets.QMessageBox()
                        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                        msgBox.setText("Project names cannot contain the text 'asset' or 'assembly'.")
                        msgBox.exec_()
                        self.createNewProject()
                else:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                    msgBox.setText("Project names must start with a letter.\nIt can contain letters, digits, or underscores, and cannot contain spaces.")
                    msgBox.exec_()
                    self.createNewProject()
            else:
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setText("No project name specified!")
                msgBox.exec_()
                self.createNewProject()
        else:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText("No hostname specified!")
            msgBox.exec_()

    def set_project_link(self):
        self.input_box_project_url.setText(self.last_project_link)

    def inputProjectURL(self):
        dialog = QtWidgets.QInputDialog(self.form)
        dialog.setWindowTitle('Omniverse Connector for FreeCAD')
        dialog.setLabelText('Input existing project URL')
        dialog.show()
        dialog.findChild(QtWidgets.QLineEdit).hide()
        
        self.input_box_project_url = QtWidgets.QLineEdit()
        projecturl_prompt_text = QtWidgets.QLabel("Enter a link with format omniverse://HOST_NAME/PROJECT_PATH")

        dialog.layout().insertWidget(1, self.input_box_project_url)
        dialog.layout().insertWidget(2, projecturl_prompt_text)

        self.last_project_link = GetLastProjectLinkNoPrint()


        if self.last_project_link != None:
            last_project_completer = QtWidgets.QCompleter([self.last_project_link])
            self.input_box_project_url.setCompleter(last_project_completer)


        dialog.exec_()
        projectURL = self.input_box_project_url.text()

        if projectURL!='':
            if '.usd' not in projectURL:
                if no_restricted_strings_in_project_link(projectURL) ==True:
                    check_project_ok = self.checkProjectURL(inputProjectURL = clean_omniverse_path(projectURL))
                    if check_project_ok ==True:
                        delete_asset_localdata()
                        self.selected_asset_text.setText(' \u274c No STP asset selected.')
                        self.selected_asset_usd_text.setText(' \u274c No corresponding USD asset selected.')
                else:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                    msgBox.setText("Project links cannot contain the text 'asset' or 'assembly'.\nEnter a link with format omniverse://HOST_NAME/PROJECT_DIRECTORY . ")
                    msgBox.exec_()
                    self.inputProjectURL()       
            else:
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setText("Project links are folder links and must not include .usd in its path.\nEnter a link with format omniverse://HOST_NAME/PROJECT_DIRECTORY . ")
                msgBox.exec_()
                self.inputProjectURL()

    def checkProjectURL(self, inputProjectURL = None):
        currentProjectURL = GetCurrentProjectLinkNoPrint()
        if inputProjectURL !=None:
            SaveProjectLinkAsTextFile(inputProjectURL)
            print('New Omniverse Nucleus project link at: ', inputProjectURL)
            savedURL = GetCurrentProjectLinkNoPrint()
            if savedURL is not None:
                _, _, permission = GetAuthCheck(savedURL, filetype='project')
                print(permission)
                if permission == 'NO_ACCESS':
                    print('[ERROR] Failed to authenticate with Nucleus at '+ savedURL)
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                    msgBox.setText("[ERROR] Failed to authenticate with nucleus at "+savedURL)
                    msgBox.exec_()
                    self.currentProjectURL_text.setText('\u274c No project Nucleus URL specified.')
                    delete_project_link()
                    ok = False
                    FreeCAD.is_connected_to_nucleus_project = False
                else:
                    self.currentProjectURL_text.setText(' \u2705 Project directory: '+savedURL)
                    ok = True
                    FreeCAD.is_connected_to_nucleus_project = True

        elif currentProjectURL is not None and inputProjectURL==None:
            SaveProjectLinkAsTextFile(currentProjectURL)
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText("No USD link specified! \nRevert to initial Nucleus USD link at:\n"+currentProjectURL)
            msgBox.exec_()

            print('[WARN] No project link specified!')
            print('Revert to initial Omniverse Nucleus project link at: ', currentProjectURL)
            savedURL = GetCurrentProjectLinkNoPrint()
            if savedURL is not None:
                _, _, permission = GetAuthCheck(savedURL, filetype='project')
                print(permission)
                if permission == 'NO_ACCESS':
                    print('[ERROR] Failed to authenticate with Nucleus at '+ savedURL)
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                    msgBox.setText("[ERROR] Failed to authenticate with nucleus at "+savedURL)
                    msgBox.exec_()
                    self.currentProjectURL_text.setText(' \u274c No Project Nucleus URL specified.')
                    delete_project_link()
                    ok = False
                    FreeCAD.is_connected_to_nucleus_project = False
                else:
                    self.currentProjectURL_text.setText('\u2705 Project directory: '+savedURL)
                    ok = True
                    FreeCAD.is_connected_to_nucleus_project = True
        else:
            print('[WARN] No project link specified!')
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
            msgBox.setText("No project link specified!")
            msgBox.exec_()
            ok = False

        return ok
    def dialogBoxCreateNewAsset(self):
        currentProjectURL = GetCurrentProjectLinkNoPrint()
        if currentProjectURL:
            dialog = QtWidgets.QInputDialog(self.form)
            dialog.setWindowTitle('Omniverse Connector for FreeCAD')
            dialog.setLabelText('Create new asset on Nucleus')
            
            dialog.show()

            dialog.findChild(QtWidgets.QLineEdit).hide()

            assetname_prompt = QtWidgets.QLabel("New asset name:")
            input_assetname = QtWidgets.QLineEdit()

            text_format_rules = QtWidgets.QLabel("Asset names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")

            dialog.layout().insertWidget(1, assetname_prompt)
            dialog.layout().insertWidget(2, input_assetname)
            dialog.layout().insertWidget(3, text_format_rules)
            current_project_dialogtext = QtWidgets.QLabel(' Current project:'+ currentProjectURL)
            dialog.exec_()
            asset_name = input_assetname.text()
            token = str(RandomTokenGenerator())

            if asset_name!='':
                if text_follows_rules(asset_name)==True:
                    print('Creating new asset '+ asset_name+' on project '+ currentProjectURL)
                    stdout, stderr, stplink, usdlink, error_text = CreateNewAssetOnNucleus(asset_name, use_url = True, projectURL=currentProjectURL, token=token)
                    if error_text == None:
                        self.selected_asset_text.setText(' \u2705 Selected asset: '+stplink.split('/')[-1])
                        self.selected_asset_usd_text.setText(' \u2705 Corresponding USD: '+ usdlink.split('/')[-1])
                        SaveSTPLinkAsTextFile(stplink)
                        SaveUSDLinkAsTextFile(usdlink)

                        GetAuthCheck(stplink,  filetype='stp')
                        GetAuthCheck(usdlink,  filetype='usd')
                    else:
                        msgBox = QtWidgets.QMessageBox()
                        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
                        msgBox.setText(error_text)
                        msgBox.exec_()
                        self.dialogBoxCreateNewAsset()
                else:
                    msgBox = QtWidgets.QMessageBox()
                    msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                    msgBox.setText("Asset names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")
                    msgBox.exec_()
                    self.dialogBoxCreateNewAsset()
            else:
                print('[WARN] No asset name specified!')
                msgBox = QtWidgets.QMessageBox()
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setText("No asset name specified!")
                msgBox.exec_()
        else:
            print('[WARN] No project link specified or found!')
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText("No project link specified or found!")
            msgBox.exec_()


    def getListItem(self):
        currentProjectURL = GetCurrentProjectLinkNoPrint()
        if currentProjectURL is not None:
            FindUSDandSTPFiles(currentProjectURL)
            item_list = GetListOfSTPFiles()
            usd_list = GetListOfUSDFiles()

            if item_list!=None and usd_list!=None:
                usd_list = [link_entry.strip() for link_entry in usd_list]
                item_list = [link_entry.strip() for link_entry in item_list]
                item_list_short = [item.split('/')[-1] for item in item_list]
                
                new_asset_string = 'Create new asset...'
                item_list_short.append(new_asset_string)
                if len(item_list_short)>2:
                    dialog_txt = "Found "+ str(len(item_list_short)-1) +' geometry assets. Select one or create new asset:'
                else:
                    dialog_txt = "Found " +'1 geometry asset. Select it or create new asset:'
                item_short, ok = QtWidgets.QInputDialog.getItem(self.form, "Omniverse Connector for FreeCAD", dialog_txt, item_list_short, 0, False)
                if ok and item_short:
                    if item_short !=new_asset_string:
                        self.selected_asset = item_short
                        print(item_short)
                        print(usd_list)
                        item = get_full_link_from_short(item_short, item_list_short, item_list)
                        print(item)
                        usdlink = find_corresponding_element(item, item_list, usd_list)
                        usdlink_short =usdlink.split('/')[-1]
                        print(usdlink)
                        SaveSTPLinkAsTextFile(item)
                        SaveUSDLinkAsTextFile(usdlink)
                        GetAuthCheck(item,  filetype='stp')
                        GetAuthCheck(usdlink,  filetype='usd')
                        self.selected_asset_text.setText(' \u2705 Selected asset: '+item_short)
                        self.selected_asset_usd_text.setText(' \u2705 Corresponding USD: '+ usdlink_short)
                    elif item_short==new_asset_string:
                        self.dialogBoxCreateNewAsset()
            elif item_list==None and usd_list==None:
                print('No assets found.')
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Question)
                msg.setText('No assets found. Create new?')
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
                ret = msg.exec_()
                if ret==QtWidgets.QMessageBox.Ok:
                    self.dialogBoxCreateNewAsset()
        else:
            print('[WARN] No project link specified!')
            msgBox = QtWidgets.QMessageBox()
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText("No project link specified!")
            msgBox.exec_()            
    def accept(self):
        FreeCADGui.Control.closeDialog() #close the dialog

    def _warn(self, msg):
        box = QtWidgets.QMessageBox()
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setText(msg)
        box.exec_()

class _GetURLPanel:
    """
    Button to open the connection settings panel
    """

    def Activated(self):
        baseWidget = QtWidgets.QWidget()
        panel = OmniConnectionSettingsPanel(baseWidget)
        FreeCADGui.Control.showDialog(panel)

    def GetResources(self):
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'Omniverse project settings',
            'Omniverse project settings')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'Omniverse project settings',
            'Omniverse project settings')
        return {
            'Pixmap': __dir__ + '/icons/ovConnect_connSettings.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        return not FreeCAD.ActiveDocument is None

class _GetAssemblyPanel:
    """
    Button to open the assembly settings panel
    """

    def Activated(self):
        baseWidget = QtWidgets.QWidget()
        panel = OmniverseAssemblyPanel(baseWidget)
        FreeCADGui.Control.showDialog(panel)

    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_assembly_tools',
            'Assembly tools')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_assembly_tools',
            'Launch a new assembly or configure assembly preferences')
        return {
            'Pixmap': __dir__ + '/icons/ovConnect_assembly.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        is_activeDocumentExists = not FreeCAD.ActiveDocument is None
        project_permission = GetCurrentProjectPermissions()
        projectURL = GetCurrentProjectLinkNoPrint()
        is_projectPermissionOK = project_permission == 'OK_ACCESS'
        is_projectURLExists = projectURL!= None
        is_checksValid = is_activeDocumentExists == True and is_projectPermissionOK==True and is_projectURLExists==True

        return is_checksValid

FreeCADGui.addCommand('OVconnect_URLPanel', _GetURLPanel())
FreeCADGui.addCommand('OVconnect_push_to_nucleus', _UploadCmd())
FreeCADGui.addCommand('OVconnect_pull_from_nucleus', _DownloadCmd())
FreeCADGui.addCommand('OVconnect_assembly_tools', _GetAssemblyPanel())
# FreeCADGui.addCommand('OVconnect_clear_junk_files', _ClearJunkCmd())