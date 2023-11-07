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

import PySide
from PySide import QtCore, QtGui
import FreeCAD
import FreeCADGui
import Part
import os
import Mesh
import subprocess
import shutil
import random
import string
import ImportGui
import re
import time
import ast
import asyncio
import sys
import datetime
# from quamash import QEventLoop
import threading
# from PyQt5.QtWidgets import QApplication

__dir__ = os.path.dirname(__file__)

### BACKEND FUNCTIONS
# FreeCAD Command made with a Python script
def GetFetcherScriptsDirectory():
    workbench_path = os.path.dirname(os.path.realpath(__file__))
    omni_directory = workbench_path + '/omniConnect'
    return omni_directory

def GetLocalDirectoryName():
    workbench_path = os.path.dirname(os.path.realpath(__file__))
    local_directory = workbench_path+"/junkFiles"
    return local_directory

def GetBatchFileName(live=False):
    if live == False:
        batchfilename = "/run_py_omni_client.bat"
    else:
        batchfilename = '/run_py_live_session.bat'
    return batchfilename

def ClearLocalDirectory():
    folder = GetLocalDirectoryName()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('[ERROR] Failed to delete %s. Reason: %s' % (file_path, e))

def RandomTokenGenerator():
	characters = string.ascii_letters + string.digits  # letters and numbers
	token = ''.join(random.choices(characters, k=5))
	return token

def SaveUSDLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_usd = str(usdlink)
    textfile_name = local_directory+'/usdlink.txt'
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveLastProjectLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_project= str(usdlink)
    textfile_name = local_directory+'/last_projectlink.txt'
    with open(textfile_name, 'w') as f:
        f.write(usdlink)


def SaveProjectLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_project= str(usdlink)
    textfile_name = local_directory+'/projectlink.txt'
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveSTPLinkAsTextFile(stplink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_stp = str(stplink)
    textfile_name = local_directory+'/stplink.txt'
    with open(textfile_name, 'w') as f:
        f.write(stplink)

def SaveUSDPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_usd =permission
    textfile_name = local_directory+'/usd_permission.txt'
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveProjectPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_project =permission
    textfile_name = local_directory+'/project_permission.txt'
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveSTPPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_stp =permission
    textfile_name = local_directory+'/stp_permission.txt'
    with open(textfile_name, 'w') as f:
        f.write(permission)

def delete_project_link():
    local_directory = GetLocalDirectoryName()
    textfile_name = local_directory+'/projectlink.txt'
    try:
        os.remove(textfile_name)
    except FileNotFoundError:
        # print(f"The file '{textfile_name}' does not exist.")
        pass
    except PermissionError:
        # print(f"Permission denied. Unable to delete the file '{textfile_name}'.")
        pass
    except Exception as e:
        print(f"An error occurred while deleting the file '{textfile_name}': {str(e)}")

def delete_asset_localdata():
    local_directory = GetLocalDirectoryName()
    textfile_names = [str(local_directory)+'/usdlink.txt', str(local_directory)+'/usd_permission.txt', str(local_directory)+'/stplink.txt', str(local_directory)+'/stp_permission.txt']
    
    for asset_data in textfile_names:
        try:
            os.remove(asset_data)
        except FileNotFoundError:
            print(f"The file '{asset_data}' does not exist.")
        except PermissionError:
            print(f"Permission denied. Unable to delete the file '{asset_data}'.")
        except Exception as e:
            print(f"An error occurred while deleting the file '{asset_data}': {str(e)}")




def GetCurrentUSDPermissions():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/usd_permission.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            permission = lines[0]
        else:
            permission=None
        return permission
    except IOError:
        return None

def GetCurrentProjectPermissions():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/project_permission.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            permission = lines[0]
        else:
            permission=None
        return permission
    except IOError:
        return None

def GetCurrentSTPPermissions():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/stp_permission.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            permission = lines[0]
        else:
            permission=None
        return permission
    except IOError:
        return None

def GetCurrentUSDLink():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/usdlink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
            print('[ERROR] No USD link specified! Check whether you have inputted your USD link.')
        return usdlink
    except IOError:
        print('[ERROR] USD link not found! Check whether you have inputted your USD link.')


def GetCurrentUSDLinkNoPrint():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/usdlink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
        return usdlink
    except IOError:
    	return None

def GetCurrentProjectLink():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/projectlink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
            print('[ERROR] No USD link specified! Check whether you have inputted your USD link.')
        return usdlink
    except IOError:
        print('[ERROR] USD link not found! Check whether you have inputted your USD link.')


def GetCurrentProjectLinkNoPrint():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/projectlink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
        return usdlink
    except IOError:
        return None

def GetLastProjectLinkNoPrint():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/last_projectlink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
        return usdlink
    except IOError:
        return None

def GetCurrentSTPLinkNoPrint():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/stplink.txt'
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            stplink = lines[0]
        else:
            stplink=None
        return stplink
    except IOError:
        return None


def GetCurrentSelection():
    selection = FreeCADGui.Selection.getSelection()
    # Check the number of selected objects
    if str(selection) =='[<App::Origin object>]':
        print('[ERROR] Origin object selected. Select a valid mesh, part, or body object to push to Nucleus.')
        return None
    if len(selection) == 1:
        # Access the selected object
        selected_object = selection[0]
        print("Selected object:", selected_object.Name)
        return selected_object
    else:
        print("[ERROR] No object selected or multiple objects selected! Select a single object from the Model tree to push to Nucleus.")
        return None

def GetAuthCheck(usdlink, filetype='usd'):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath += batchfilename 
    error_code_no_permissions = 'NO_PERMISSION'
    error_code_link_not_found = 'NOT_FOUND'
    error_code_no_auth = 'NO_AUTH'
    print('Validating connection with '+usdlink)
    
    cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --auth'
    print(cmd)
    # print(cmd) # FOR DEBUG
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    stdout = stdout.split('\r\n')
    no_access = 0
    for line in stdout:
        line = str(line)
        print('[OmniClient]', line)
        if error_code_no_permissions in line:
            no_access +=1
        if error_code_link_not_found in line:
            no_access +=1
        if error_code_no_auth in line:
            no_access +=1   
    if no_access ==0:
        permission='OK_ACCESS'
    else:
        permission = 'NO_ACCESS'
    if filetype=='stp':
        SaveSTPPermissionsAsTextFile(permission)
    elif filetype=='usd':
        SaveUSDPermissionsAsTextFile(permission)
    elif filetype=='project':
        SaveProjectPermissionsAsTextFile(permission)
    print('[ERRORS]', stderr)

    return stdout, stderr, permission

def FindUSDandSTPFiles(usdlink):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath += batchfilename
    local_directory = GetLocalDirectoryName()
    print('Finding asset files on project folder ...')
    cmd = batchfilepath + ' --local_directory ' + local_directory + ' --nucleus_url ' + usdlink +' --find_stp_and_usd_files'
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    stdout = stdout.split('\r\n')
    for line in stdout:
        line = str(line)
        print('[OmniClient] '+line)
    print('ERRORS: '+ stderr)
    return stdout, stderr

def GetListOfSTPFiles():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/stplist.txt'
        stp_url_list = []
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            for entry in lines:
                stp_url_list.append(entry)
        else:
            stp_url_list=None
        FreeCAD.OV_link_list_stp = stp_url_list
        return stp_url_list
    except IOError:
        return None

def GetListOfUSDFiles():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = local_directory+'/usdlist.txt'
        usd_url_list = []
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            for entry in lines:
                usd_url_list.append(entry)
        else:
            usd_url_list=None
        FreeCAD.OV_link_list_usd = usd_url_list
        return usd_url_list
    except IOError:
        return None

#TODO: FIX THIS!

def UploadUSDToNucleus(usdlink, selected_object, token, existing_usd = True):
    #TODO - WIP
    if existing_usd == True:
        # permission = 
        permission = GetCurrentUSDPermissions()
        if permission =='NO_ACCESS':
            print('[ERROR] NO_PERMISSION: Cannot access USD file: '+ usdlink)
            print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
            print('Try logging in under a different username: log out through the nucleus. SIGNOUT BUTTON IS WIP')
            stdout='FAIL'
            stderr='NO_PERMISSION'
        elif permission is None:
            print('[ERROR] PERMISSION_NOT_FOUND: Cannot access USD file: '+ usdlink)
            print('[ERROR] You have not entered a valid USD link.')
            stdout='FAIL'
            stderr='PERMISSION_NOT_FOUND'
        elif permission == 'OK_ACCESS': 
        # Batch file where the OV USD uploader lives
            batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
            batchfilename = GetBatchFileName()
            batchfilepath = batchfilepath+batchfilename
            # local directory where copies are staged
            local_STL_path = GetLocalDirectoryName()
            print('local_STL_path', local_STL_path)
            # A one-time token for fetching to make sure get the right file. This needs to be a random string
            # token = str(RandomTokenGenerator())
            print('Unique version identifier: '+token)
            local_STL_filename = local_STL_path +  '/'+token+'upload.stl'
            Mesh.export([selected_object], local_STL_filename)
            print('local_STL_filename', local_STL_filename)
            # Parsing commands for the batchfile
            cmd = batchfilepath + ' --nucleus_url' +' '+ usdlink + ' --local_directory '+ local_STL_path.replace(" ","` ") +' --push' +" --token "+ token
            print(cmd)
            # Now running command to push to Nucleus
            p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')
            # stdout = str(stdout)
            # stderr = str(stderr)
    return stdout, stderr


def UploadSTPToNucleus(stplink, selected_object, token, existing_stp = True):
    if existing_stp ==True:
        permission = GetCurrentSTPPermissions()
        if permission =='NO_ACCESS':
            print('[ERROR] NO_PERMISSION: Cannot access STP file: '+ stplink)
            print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
            print('Try logging in under a different username: log out through the nucleus.')
            stdout='FAIL'
            stderr='NO_PERMISSION'
        elif permission is None:
            print('[ERROR] PERMISSION_NOT_FOUND: Cannot access STP file: '+ stplink)
            print('[ERROR] You have not entered a valid Nucleus link.')
            stdout='FAIL'
            stderr='PERMISSION_NOT_FOUND'
        elif permission == 'OK_ACCESS': 
        # Batch file where the OV USD uploader lives
            batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
            batchfilename = GetBatchFileName()
            batchfilepath = batchfilepath+batchfilename
            # local directory where copies are staged
            local_directory = GetLocalDirectoryName()
            # A one-time token for fetching to make sure get the right file. This needs to be a random string
            # token = str(RandomTokenGenerator())
            print('Unique version identifier: '+token)
            local_STP_filepath = local_directory +  '/'+token+'upload.stp'
            ImportGui.export([selected_object], local_STP_filepath)
            # selected_object.Label2 = str([stplink, token])
            # Parsing commands for the batchfile
            cmd = batchfilepath + ' --nucleus_url' +' '+ stplink + ' --local_non_usd_filename '+ local_STP_filepath.replace(" ","` ") +' --push_non_usd' +" --token "+ token
            print(cmd)
            # Now running command to push to Nucleus
            p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            stderr = stderr.decode('utf-8')
            # stdout = str(stdout)
            # stderr = str(stderr)
    return stdout, stderr



def DownloadUSDFromNucleus(usdlink):
    permission = GetCurrentUSDPermissions()
    print('File permission: '+permission)
    if permission =='NO_ACCESS':
        print('[ERROR] NO_PERMISSION: Cannot access USD file: '+ usdlink)
        print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
        print('Try logging in under a different username: log out through the nucleus. SIGNOUT BUTTON IS WIP')
        # stdout='FAIL'
        # stderr='NO_PERMISSION'
    elif permission is None:
        print('[ERROR] PERMISSION_NOT_FOUND: Cannot access USD file: '+ usdlink)
        print('[ERROR] You have not entered a valid USD link.')
        # stdout='FAIL'
        # stderr='PERMISSION_NOT_FOUND'
    elif permission == 'OK_ACCESS':        
        doc = FreeCAD.ActiveDocument
        # Batch file where the OV USD fetcher lives
        batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
        batchfilename = GetBatchFileName()
        batchfilepath = batchfilepath+batchfilename
        # local directory where copies are staged
        local_STL_path = GetLocalDirectoryName()
        # A one-time token for fetching to make sure get the right file. This needs to be a random string
        token = str(RandomTokenGenerator())
        print('Unique version identifier: '+token)
        # Parsing commands for the batchfile
        cmd = batchfilepath  + ' --nucleus_url' +' '+ usdlink + ' --local_directory '+ local_STL_path.replace(" ","` ") +' --pull' + " --token "+ token
        print(cmd)
        p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')


        # Now reading what has just been downloaded - token in below
        local_STL_filename = local_STL_path +  '/'+token+'download.stl'
        if os.path.exists(local_STL_filename):
            Mesh.insert(local_STL_filename)
        else:
            print('[ERROR] DLOAD_FAIL: USD download failed!')
            # print('If error persists, clear junk and try again. Note: user needs to reinput URL after clear junk.')
            # stdout = 'FAIL'
            # stderr = 'DLOAD_FAIL'
    return stdout, stderr

def check_file_isempty(file_path):
    #Checks whether a file is empty or not. If 
    expected_content = b'EMPTY_FILE'
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            # print(content)
            return content == expected_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False

def DownloadSTPFromNucleus(stplink, token):
    imported_object = None
    permission = GetCurrentSTPPermissions()
    print('File permission: '+permission)
    if permission =='NO_ACCESS':
        print('[ERROR] NO_PERMISSION: Cannot access STP file: '+ stplink)
        fc_err = '[ERROR] NO_PERMISSION: Cannot access STP file: '+ stplink
        print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
        print('Try logging in under a different username: log out through the nucleus.')
        # stdout='FAIL'
        # stderr='NO_PERMISSION'
    elif permission is None:
        print('[ERROR] PERMISSION_NOT_FOUND: Cannot access STP file: '+ stplink)
        fc_err = '[ERROR] PERMISSION_NOT_FOUND: Cannot access STP file: '+ stplink
        print('[ERROR] You have not entered a valid Nucleus link.')
        # stdout='FAIL'
        # stderr='PERMISSION_NOT_FOUND'
    elif permission == 'OK_ACCESS':        
        doc = FreeCAD.ActiveDocument
        FreeCAD.setActiveDocument(doc.Name)
        current_instances = set(doc.findObjects())
        fc_err = None
        # Batch file where the OV USD fetcher lives
        batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
        batchfilename = GetBatchFileName()
        batchfilepath = batchfilepath+batchfilename
        # local directory where copies are staged
        local_directory_path = GetLocalDirectoryName()
        # A one-time token for fetching to make sure get the right file. This needs to be a random string
        # token = str(RandomTokenGenerator())
        print('Unique version identifier: '+token)

        local_STP_filepath = local_directory_path +'/'+token+'download.stp'

        # Parsing commands for the batchfile
        cmd = batchfilepath  + ' --nucleus_url '+ stplink + ' --pull_non_usd ' + " --local_non_usd_filename "+ local_STP_filepath.replace(" ","` ") + " --token " + token
        print(cmd)
        p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        # Now reading what has just been downloaded - token in below
        
        if os.path.exists(local_STP_filepath):
            if check_file_isempty(local_STP_filepath)==False:
                imported_object = ImportGui.insert(local_STP_filepath, doc.Name, useLinkGroup=True, merge = False)
                ok=True
            else:
                fc_err = '[ERROR] EMPTY_ASSET: Asset is a placeholder item. Push an object to Nucleus to replace the placeholder.'
                print(fc_err)
                ok=False
        else:
            fc_err = '[ERROR] DLOAD_FAIL: STP download failed!'
            print(fc_err)
            ok=False
            # print('If error persists, clear junk and try again. Note: user needs to reinput URL after clear junk.')
            # stdout = 'FAIL'
            # stderr = 'DLOAD_FAIL'
    return ok, imported_object, stdout, stderr, fc_err

def CreateNewProjectOnNucleus(host_name, project_name):
    
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename

    cmd = batchfilepath + ' --create_new_project ' + ' --project_name ' + str(project_name) + ' --host_name ' + str(host_name)
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')


    if "error" in stdout.lower():
        ok = False
    else:
        ok =True
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')        
    return ok, stdout, stderr


def CreateNewAssemblyOnNucleus(projectURL, assembly_name = None, assembly_items_usd_links=None, assembly_items_stp_links=None):
    #todo wip making a wrapper function for create new assembly
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename

    assembly_usd_link = None

    if assembly_name == None:
        assembly_name = 'assembly'

    if assembly_items_usd_links!=None and assembly_items_stp_links!=None:
        str_assembly_items_usd = ' '.join(assembly_items_usd_links)
        str_assembly_items_stp = ' '.join(assembly_items_stp_links)
        cmd = batchfilepath + ' --nucleus_url '+ str(projectURL) + ' --create_new_assembly ' + ' --assembly_name ' + str(assembly_name) +' --asset_usd_links '+ str(str_assembly_items_usd) + ' --asset_stp_links '+ str(str_assembly_items_stp)
    else:
        cmd = batchfilepath + ' --nucleus_url '+ str(projectURL) + ' --create_new_assembly ' + ' --assembly_name ' + str(assembly_name)
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    # print(stdout[-1])
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
    for line in stdout:
        line = line.strip()
        if '.usd' and str(projectURL+'/assembly') in line:
            assembly_usd_link = line

    return stdout, stderr, assembly_usd_link

def FindExistingAssembliesOnNucleus(projectURL):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename

    cmd = batchfilepath + ' --nucleus_url '+ str(projectURL) + ' --find_existing_assemblies '
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    # print(stdout[-1])
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
    existing_assembly_usd_links = []
    for line in stdout:
        line = line.strip()
        if '.usd' and str('/assembly') in line:
            existing_assembly_usd_links.append(line)
    if existing_assembly_usd_links ==[]:
        existing_assembly_usd_links = None
    return stdout, stderr, existing_assembly_usd_links

def GetPrimReferenceXForms(assemblyURL):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename

    cmd = batchfilepath + ' --nucleus_url '+ str(assemblyURL) + ' --get_prim_reference_xforms '
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    # print(stdout[-1])
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
    prim_data =[]
    for line in stdout:
        reference_data = line.split('|')
        reference_data = [data.strip() for data in reference_data]
        if reference_data !=['']:
            if '.usda' in str(reference_data[0]):
                step_path = str(reference_data[0]).replace('.usda', '.stp')
            elif '.usd' in str(reference_data[0]):
                step_path = str(reference_data[0]).replace('.usd', '.stp')
            reference_dict = {
            "ref-path": str(reference_data[0]),
            "step-path": str(step_path),
            "transform": ast.literal_eval(reference_data[1]),
            "rot-xyz": ast.literal_eval(reference_data[2]),
            "scale": ast.literal_eval(reference_data[3])
            }
            prim_data.append(reference_dict)
    if prim_data ==[]:
        primdata = None

    return stdout, stderr, prim_data




def CreateNewAssetOnNucleus(asset_name, use_url = True, projectURL=None, host_name=None, project_name=None, token=None):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename
    if use_url ==False:
        cmd = batchfilepath + ' --create_new_asset ' + ' --project_name ' + str(project_name) + ' --host_name ' + str(host_name) + ' --asset_name ' + str(asset_name)
    elif use_url==True:
        cmd = batchfilepath + ' --create_new_asset ' + ' --nucleus_url ' + str(projectURL) + ' --asset_name ' + str(asset_name)
    if token:
        cmd += ' --token '+ token
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    # print(stdout[-1])
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
    for line in stdout:
        line = line.strip()
        if '.usd' in line:
            usdlink = line
            print(line)
        if '.stp' in line:
            stplink = line
            print(line)
    return stdout, stderr, stplink, usdlink

def GetComponentNameFromStplink(stplink):
    return str(stplink.split('/')[-1]).split('.')[0]

def attachNewStringProperty(selection, property_name, property_value):
    object_property_list = selection.PropertiesList
    if property_name not in object_property_list:
        selection.addProperty('App::PropertyString', property_name)
        exec("selection."+property_name+"='"+str(property_value)+"'")
    else:
        exec("selection."+property_name+"='"+str(property_value)+"'")
    # setting property as read-only!
    exec("selection.setEditorMode('"+str(property_name)+"', 1)")
    return selection

def getStringPropertyValue(selection, property_name):
    object_property_list = selection.PropertiesList
    if property_name in object_property_list:
        # exec('value = selection.'+str(property_name))
        # exec("value = selection."+property_name)
        # exec('value = selection.Nucleus_link_usd')
        return selection, exec('selection.'+str(property_name))
    else:
        return selection, None

def get_assembly_component_placement(type='base'):
    # func to get list of valid (already uploaded to OV) assembly components position and rotation
    doc = FreeCAD.ActiveDocument
    valid_freecad_objects = [obj for obj in doc.Objects if hasattr(obj, 'Nucleus_link_usd')]
    if type =='base':
        placement = [tuple(obj.Placement.Base) for obj in valid_freecad_objects]
    elif type == 'rotation':
        placement = [tuple(obj.Placement.Rotation.getYawPitchRoll())[::-1] for obj in valid_freecad_objects] 
    component_usd_links = [obj.Nucleus_link_usd  for obj in valid_freecad_objects]
    return component_usd_links, placement

def parse_list_into_set_srt_command_arg(input_list):
    input_list_str = str(input_list)
    no_brackets = input_list_str.replace("]", " ").replace("[", " ")
    no_parentheses = no_brackets.replace(")", " ").replace("(", " ")
    return no_parentheses


def strip_suffixes(item):
    return re.sub(r'\.(usd|usda|usdc|usdz|stp|step)$', '', item, flags=re.IGNORECASE)


def find_corresponding_element(selected_item, first_list, second_list):
    for first_item, second_item in zip(first_list, second_list):
        if strip_suffixes(selected_item) == strip_suffixes(second_item):
            return second_item


### FRONTEND FUNCTIONS - MAPPING BUTTONS WIDGETS ETC TO REAL FUNCTIONS


def _DownloadCmdWrapper(stplink, usdlink, token):

    if stplink is not None:
        GetAuthCheck(stplink,  filetype='stp')
        print('Pulling from '+stplink)
        ok, imported_object, output, error, fc_err = DownloadSTPFromNucleus(stplink, token = token)
        output = output.split('\r\n')
        for line in output:
            print('OmniClient:', line)
        print('ERRORS', error)
        component_label = GetComponentNameFromStplink(stplink)

        imported_object = attachNewStringProperty(imported_object, property_name = "Label", property_value = component_label)
        imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_link_stp", property_value = stplink)
        imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_link_usd", property_value = usdlink)
        imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_version_id", property_value = token)
        t = time.localtime()
        current_time = time.strftime(" %d %b  %Y %H:%M:%S", t)
        imported_object = attachNewStringProperty(imported_object, property_name = "Last_Nucleus_sync_time", property_value = current_time)       
        return imported_object
class _DownloadCmd:
    """Command to download from nucleus"""
    def Activated(self):
        # what is done when the command is clicked
        token = str(RandomTokenGenerator())
        # usdlink = getStringPropertyValue(selection, 'Nucleus_link_usd')
        # stplink = getStringPropertyValue(selection, 'Nucleus_link_stp')
        # if usdlink==None or stplink==None:
        usdlink = GetCurrentUSDLink()
        stplink = GetCurrentSTPLinkNoPrint()

        if stplink is not None:
            print('Pulling from '+stplink)
            ok, imported_object, output, error, fc_err = DownloadSTPFromNucleus(stplink, token = token)
            if ok==True:
                output = output.split('\r\n')
                for line in output:
                    print('OmniClient:', line)
                print('ERRORS', error)
                component_label = GetComponentNameFromStplink(stplink)

                imported_object = attachNewStringProperty(imported_object, property_name = "Label", property_value = component_label)
                imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_link_stp", property_value = stplink)
                imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_link_usd", property_value = usdlink)
                imported_object = attachNewStringProperty(imported_object, property_name = "Nucleus_version_id", property_value = token)
                t = time.localtime()
                current_time = time.strftime(" %d %b  %Y %H:%M:%S", t)
                imported_object = attachNewStringProperty(imported_object, property_name = "Last_Nucleus_sync_time", property_value = current_time)       
            if ok==False:
                msgBox = QtGui.QMessageBox()
                msgBox.setIcon(QtGui.QMessageBox.Critical)
                msgBox.setText(fc_err)
                msgBox.setWindowTitle('Omniverse Connector for FreeCAD')
                msgBox.exec_()

               

        #DEPRECATED SINCE MOVE INTERCHANGE FORMAT TO STP
        # usdlink = GetCurrentUSDLink()
        # if usdlink is not None:
        #     print('Pulling from '+usdlink)
        #     output, error = DownloadUSDFromNucleus(usdlink)
        #     output = output.split('\r\n')
        #     for line in output:
        #         print('OmniClient:', line)
        #     print('ERRORS', error)

    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_pull_from_nucleus',
            'Pull from Nucleus')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_pull_from_nucleus',
            'Pulls geometry from Omniverse Nucleus')
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_pull.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        usd_URL= GetCurrentUSDLinkNoPrint() 
        usd_permission= GetCurrentUSDPermissions()

        stp_permission = GetCurrentSTPPermissions()
        stp_URL = GetCurrentSTPLinkNoPrint()

        is_stpPermissionOK = stp_permission == 'OK_ACCESS'
        is_stpURLExists = stp_URL!= None
        is_stpSideValid = is_stpPermissionOK ==True and is_stpURLExists==True

        is_usdPermissionOK = usd_permission == 'OK_ACCESS'
        is_usdURLExists = usd_URL!= None
        is_usdSideValid = is_usdPermissionOK==True and is_usdURLExists==True

        is_activeDocumentExists = not FreeCAD.ActiveDocument is None

        is_checksValid = is_activeDocumentExists == True and is_stpSideValid==True and is_usdSideValid==True
        return is_checksValid

class _ClearJunkCmd:

    
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
            'Clear local junk files')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_clear_junk_files',
            'Clear local junk files')
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_clearjunk.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        # The command will be active if there is an active document
        return not FreeCAD.ActiveDocument is None




# GUI command that links the Python script
class _UploadCmd:
    """Command to upload a selected component to nucleus"""
    #TODO FIX THIS!! Attach permissions to freecad ITEM so we can read from it. must somehow attach permissions from getauthcheck

    
    def Activated(self):
        # what is done when the command is clicked
        selection =GetCurrentSelection()
        #TODO FIX THIS BIT = if usdlink from FreeCAd variable is different to the one from the directory
        if selection != None:
            usdlink_local = GetCurrentUSDLinkNoPrint()
            stplink_local = GetCurrentSTPLinkNoPrint()

            usd_link_is_exist_on_fc = 'Nucleus_link_usd' in selection.PropertiesList
            stp_link_is_exist_on_fc = 'Nucleus_link_stp' in selection.PropertiesList

            if usd_link_is_exist_on_fc==True and stp_link_is_exist_on_fc==True:
                usdlink_fcvar = selection.Nucleus_link_usd
                stplink_fcvar = selection.Nucleus_link_stp

                if usdlink_fcvar !=usdlink_local or stplink_fcvar != stplink_local:
                    
                    stplink_list = [stplink_fcvar, stplink_local]
                    usdlink_list = [usdlink_fcvar, usdlink_local]

                    if stplink_fcvar!=stplink_local:
                        dialog_txt = 'Found conflict in Nucleus STP links. Select the desired STP link to push to:'
                        item, ok = QtGui.QInputDialog.getItem(QtGui.QWidget(), "Omniverse Connector for FreeCAD", dialog_txt, stplink_list, 0, False)
                        if ok and item:
                            stplink = item
                            usdlink = usdlink_list[stplink_list.index(item)]
                        else:
                            msgBox = QtGui.QMessageBox()
                            msgBox.setIcon(QtGui.QMessageBox.Question)
                            msgBox.setText("Failed to push to Nucleus!")
                            msgBox.exec_()

                    elif usdlink_fcvar!=usdlink_local:
                        dialog_txt = 'Found conflict in Nucleus USD links. Select the desired USD link to push to:'
                        item, ok = QtGui.QInputDialog.getItem(QtGui.QWidget(), "Omniverse Connector for FreeCAD", dialog_txt, usdlink_list, 0, False)
                        if ok and item:
                            stplink = item
                            usdlink = stplink_list[usdlink_list.index(item)]
                        else:
                            msgBox = QtGui.QMessageBox()
                            msgBox.setIcon(QtGui.QMessageBox.Question)
                            msgBox.setText("Failed to push to Nucleus!")
                            msgBox.exec_()

                else:
                    usdlink= usdlink_fcvar
                    stplink = stplink_fcvar
            else:
                usdlink = usdlink_local
                stplink = stplink_local

            token = str(RandomTokenGenerator())
            if usdlink is not None:
                if selection is not None:
                    print('Pushing '+str(selection.Name)+' to '+usdlink)
                    output, error = UploadUSDToNucleus(usdlink, selection, token = token)
                    output = output.split('\r\n')
                    for line in output:
                        print('OmniClient', line)
                    print('ERRORS', error)
                    selection = attachNewStringProperty(selection, property_name = "Nucleus_link_usd", property_value = usdlink)
            if stplink is not None:
                if selection is not None:
                    print('Pushing '+str(selection.Name)+' to '+stplink)
                    output, error = UploadSTPToNucleus(stplink, selection, token = token)
                    output = output.split('\r\n')
                    for line in output:
                        print('OmniClient', line)
                    print('ERRORS', error)
                    t = time.localtime()
                    current_time = time.strftime(" %d %b %Y %H:%M:%S", t)
                    component_label = GetComponentNameFromStplink(stplink)

                    selection = attachNewStringProperty(selection, property_name = "Label", property_value = component_label)
                    selection = attachNewStringProperty(selection, property_name = "Last_Nucleus_sync_time", property_value = current_time)
                    selection = attachNewStringProperty(selection, property_name = "Nucleus_link_stp", property_value = stplink)
                    selection = attachNewStringProperty(selection, property_name = "Nucleus_version_id", property_value = token)

    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_push_to_nucleus',
            'Push to Nucleus')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'OVconnect_push_to_nucleus',
            'Pushes selected geometry to Omniverse Nucleus')
        return {
            'Pixmap': __dir__ + '/icons/OVConnect_push.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):

        usd_permission = GetCurrentUSDPermissions()
        usd_URL = GetCurrentUSDLinkNoPrint()

        stp_permission = GetCurrentSTPPermissions()
        stp_URL = GetCurrentSTPLinkNoPrint()

        is_stpPermissionOK = stp_permission == 'OK_ACCESS'
        is_stpURLExists = stp_URL!= None
        is_stpSideValid = is_stpPermissionOK ==True and is_stpURLExists==True

        is_usdPermissionOK = usd_permission == 'OK_ACCESS'
        is_usdURLExists = usd_URL!= None
        is_usdSideValid = is_usdPermissionOK==True and is_usdURLExists==True

        is_activeDocumentExists = not FreeCAD.ActiveDocument is None

        is_checksValid = is_activeDocumentExists == True and is_stpSideValid==True and is_usdSideValid==True


        # The command will be active if the above checks all return True! - measure against invalid upload
        return is_checksValid

class _CheckConnectionCmd:
    """DEPRECATED CLASS!
    placeholder command to test user authetication"""
    
    def Activated(self):
        # what is done when the command is clicked
        usdlink = GetCurrentUSDLink()
        if usdlink is not None:
            GetAuthCheck(usdlink)

            # print('Connection validated.')
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

def GetListOfAssemblyObjects(projectURL):
    doc = FreeCAD.ActiveDocument
    object_list = []
    object_label_list = []
    for obj in doc.Objects:
        if 'Nucleus_link_usd' in dir(obj):
            if projectURL in str(obj.Nucleus_link_usd):
                object_list.append(obj)
                object_label_list.append(obj.Label)
    return object_list, object_label_list



#######
### BACKUP OMNIURLPANEL:
# class SpecifyOmniverseURLPanel:
#     def __init__(self,widget):
#         self.form = widget
#         layout = QtGui.QVBoxLayout()
#         self.URL_TextLabel = QtGui.QLabel("Input project URL:")
#         currentURL = GetCurrentUSDLinkNoPrint()
#         self.currentURL = QtGui.QLabel("No Nucleus URL specified.")
#         if currentURL is not None:
#             self.currentURL = QtGui.QLabel("Current project URL: "+currentURL)
#         # else:
#         #   self.currentURL = QtGui.QLabel("No Nucleus URL specified.")
#         # The layout will be horizontal
#         # Spin Box that takes doubles
#         self.URL_Text = QtGui.QLineEdit()

#         self.browse_button = QtGui.QPushButton("Browse assets")
#         self.browse_button.clicked.connect(self.getListItem)
#         # Default value
#         self.URL_Text.setPlaceholderText('omniverse://hostname/path/to/your/project')
#         self.selected_asset_text = QtGui.QLabel('No asset selected.')
#         # suffix to indicate the units
#         layout.addWidget(self.URL_TextLabel)
#         layout.addWidget(self.URL_Text)
#         layout.addWidget(self.browse_button)
#         layout.addWidget(self.currentURL)
#         layout.addWidget(self.selected_asset_text)

#         self.form.setLayout(layout)

#     def getListItem(self):
#         items = ("haha", "hihi", "hoho")
#         item, ok = QtGui.QInputDialog.getItem(self.form, "select input", "list of hahas", items, 0, False)
#         if ok and item:
#             # self.URL_Text.setText(item)
#             self.selected_asset = item
#             self.selected_asset_text.setText('Selected asset: '+item)



#     # Ok and Cancel buttons are created by default in FreeCAD Task Panels
#     # What is done when we click on the ok button.
#     def accept(self):
#         currentURL = GetCurrentUSDLinkNoPrint()
#         hostPath = self.URL_Text.text()
#         if hostPath !='':
#             SaveUSDLinkAsTextFile(hostPath)
#             print('New Omniverse Nucleus USD link at: ', hostPath)
#             savedURL = GetCurrentUSDLinkNoPrint()
#             if savedURL is not None:
#                 GetAuthCheck(savedURL)

#         elif currentURL is not None and hostPath=='':
#             SaveUSDLinkAsTextFile(currentURL)
#             msgBox = QtGui.QMessageBox()
#             msgBox.setText("No USD link specified! \nRevert to initial Nucleus USD link at:\n"+currentURL)
#             msgBox.exec_()

#             print('[WARN] No USD link specified!')
#             print('Revert to initial Omniverse Nucleus USD link at: ', currentURL)
#             savedURL = GetCurrentUSDLinkNoPrint()
#             if savedURL is not None:
#                 GetAuthCheck(savedURL)
#         else:
#             print('[WARN] No USD link specified!')
#             msgBox = QtGui.QMessageBox()
#             msgBox.setText("No USD link specified!")
#             msgBox.exec_()

#         FreeCADGui.Control.closeDialog() #close the dialog


class ChecklistDialog(QtGui.QDialog):

    def __init__(
        self,
        name,
        stringlist=None,
        checked=False,
        icon=None,
        parent=None,
        ):
        super(ChecklistDialog, self).__init__(parent)

        self.name = name
        self.icon = icon
        self.model = QtGui.QStandardItemModel()
        self.listView = QtGui.QListView()

        for string in stringlist:
            item = QtGui.QStandardItem(string)
            item.setCheckable(True)
            check = \
                (QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
            item.setCheckState(check)
            self.model.appendRow(item)

        self.listView.setModel(self.model)

        self.okButton = QtGui.QPushButton('Create new assembly')
        self.cancelButton = QtGui.QPushButton('Cancel')
        self.selectButton = QtGui.QPushButton('Select All')
        self.unselectButton = QtGui.QPushButton('Unselect All')

        

        self.assembly_name_text = QtGui.QLabel('New assembly name:')
        self.assembly_name_input = QtGui.QLineEdit()
        self.assembly_items_text = QtGui.QLabel('Select assembly items:')

        

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.okButton)
        hbox.addWidget(self.cancelButton)
        hbox.addWidget(self.selectButton)
        hbox.addWidget(self.unselectButton)

        vbox = QtGui.QVBoxLayout(self)
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
        # TODO: error box opens up when assembly name is none
        self.accept()

    def select(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Checked)

    def unselect(self):
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(QtCore.Qt.Unchecked)

def live_get_available_sessions(usdlink):
    doc = FreeCAD.ActiveDocument
    FreeCAD.setActiveDocument(doc.Name)
    # current_instances = set(doc.findObjects())
    error_code = None
    success=None

    # Batch file where the OV USD fetcher lives
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName(live=True)
    batchfilepath = batchfilepath+batchfilename

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






# def start_QProcess(cmd):
#     parent_object = QtCore.QObject()
#     process = QtCore.QProcess(parent_object)
#     process.start(cmd)

#     def read_qprocess_output(process):
#         while True:
#             outputBytes  = process.readAll().data()
#             if outputBytes:
#                 outputUnicode = outputBytes.decode('utf-8')
#                 print('STDOUT: ', outputUnicode)
#             else:
#                 break
#     def read_qprocess_stderr(process):
#         while True:
#             outputBytes  = process.readAll().data()
#             if outputBytes:
#                 outputUnicode = outputBytes.decode('utf-8')
#                 print('STDERR: ', outputUnicode)
#             else:
#                 break
    
#     process.readyReadStandardOutput.connect(read_qprocess_output(process))
#     process.readyReadStandardError.connect(read_qprocess_stderr(process))


# class live_session(usdlink, session_name):
#     def __init__(self):
#         self.usdlink = usdlink
#         self.session_name = session_name
#         self.doc = FreeCAD.ActiveDocument
#         FreeCAD.setActiveDocument(self.doc.Name)

#         batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
#         batchfilename = GetBatchFileName(live=True)
#         self.batchfilepath = batchfilepath+batchfilename
#         self.cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --session_name ' + session_name + ' --start_live '

# def live_start_session(usdlink, session_name):
#     # DONT USE THIS YET!
#     doc = FreeCAD.ActiveDocument
#     FreeCAD.setActiveDocument(doc.Name)
#     currentProjectURL = GetCurrentProjectLinkNoPrint()
#     # current_instances = set(doc.findObjects())
#     error_code = None
#     success=None

#     # Batch file where the OV USD fetcher lives
#     batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
#     batchfilename = GetBatchFileName(live=True)
#     batchfilepath = batchfilepath+batchfilename

#     cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --session_name ' + session_name + ' --start_live '
#     print(cmd)
#     # print(cmd) # FOR DEBUG

#     def on_stdout(line):
#         print("STDOUT:", line.decode('utf-8'))

#     def on_stderr(line):
#         print("STDERR:", line.decode('utf-8'))

#     # return_code = execute(['powershell', cmd], on_stdout, on_stderr)

#     start_QProcess(cmd)

#     return None




    # print(execute(
    #     ["powershell", cmd],
    #     lambda x: print("STDOUT: %s" % x.decode('utf-8')),
    #     lambda x: print("STDERR: %s" % x.decode('utf-8')),
    # ))
    # p = await asyncio.create_subprocess_shell(cmd, stdin = asyncio.subprocess.PIPE, stdout = asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE, bufsize = 0)

    # # counter = 0
    # for line in iter(await p.stdout.readline, b''):
    #     # await read_stdout_asynchronously(line)
    #     # option = ainput()
    #     # option = 'hi'
    #     # TODO: CHANGE ainput to button click 
    #     # if option !=None:
    #         # print('writing '+str(option)+' to stdin')
    #         # comm_option = bytes(str(option)+'\n', 'utf-8')
    #         # p.stdin.write(comm_option)
    #     print(str(datetime.datetime.now())+" | " + line.decode('utf-8'))
    #     # counter+=1
        
    # print('done process')

    



class OmniverseAssemblyPanel:
    def __init__(self,widget):

        self.form = widget
        self.layout = QtGui.QVBoxLayout()
        self.currentProjectURL = GetCurrentProjectLinkNoPrint()
        self.isLive = False
        # self.currentAssemblyURL = GetCurrentProjectAssembly()


        self.panel_name_text = QtGui.QLabel('Assembly Panel')
        self.current_project_name_text = QtGui.QLabel(' \u2705 Current project: '+ str(self.currentProjectURL))

        self.assemblyUSDLink = None

        if not hasattr(FreeCAD, 'assembly_usd_link'):
            FreeCAD.assembly_usd_link = None

        if FreeCAD.assembly_usd_link != None:
            self.status_header_text = QtGui.QLabel(' Status: \u2705 Ready')
            self.current_assembly_URL_text = QtGui.QLabel(' \u2705 Current assembly: '+ str(FreeCAD.assembly_usd_link))
        else:
            self.status_header_text = QtGui.QLabel(' Status: \u274c')
            self.current_assembly_URL_text = QtGui.QLabel(' \u274c No assembly selected.')
        # self.current_assembly_URL_text = 
        
        self.create_new_assembly_button = QtGui.QPushButton("Create new assembly from workspace objects")
        self.create_new_assembly_button.clicked.connect(self.flow_create_new_assembly)

        self.open_existing_assembly_button = QtGui.QPushButton("Import existing assembly into workspace")
        self.open_existing_assembly_button.clicked.connect(self.flow_open_existing_assembly)

        self.live_mode_button = QtGui.QPushButton("(EXPERIMENTAL) Live assembly mode")
        self.live_mode_button.setCheckable(True)
        self.live_mode_button.clicked.connect(self.flow_start_live_assy_mode)

        self.upload_assy_changes_button = QtGui.QPushButton("Upload assembly changes")
        self.upload_assy_changes_button.clicked.connect(self.flow_upload_assembly_changes)

        self.download_assy_changes_button = QtGui.QPushButton("Fetch new assembly changes")
        self.download_assy_changes_button.clicked.connect(self.flow_download_assembly_changes)

        

        # LIVE ASSY DECLARATIONS
        self.proc = None
        doc = FreeCAD.ActiveDocument
        self.valid_freecad_objects = [obj for obj in doc.Objects if hasattr(obj, 'Nucleus_link_usd')]
        #TODO: LIVE ASSY MODE - poll from a running .bat file

        self.layout.addWidget(self.panel_name_text)
        self.layout.addWidget(self.create_new_assembly_button)
        self.layout.addWidget(self.open_existing_assembly_button)

        self.layout.addWidget(self.status_header_text)
        self.layout.addWidget(self.current_project_name_text)
        self.layout.addWidget(self.current_assembly_URL_text)

        self.layout.addWidget(self.upload_assy_changes_button)
        self.layout.addWidget(self.download_assy_changes_button)
        self.layout.addWidget(self.live_mode_button) # comment this out to disable experimental
        self.form.setLayout(self.layout)
        # TODO NEXT - add a new button for create new assembly!!

    def add_new_live_layout(self):
        live_layout = QtGui.QVBoxLayout()
        self.kill_live_process_button = QtGui.QPushButton("Stop live sync")
        self.kill_live_process_button.clicked.connect(self.kill_live_process())
        live_layout.addWidget(self.kill_live_process_button)
        self.layout.addItem(live_layout)

    def flow_create_new_assembly(self):
        uploaded_components_list, uploaded_components_label_list = GetListOfAssemblyObjects(self.currentProjectURL)
        if uploaded_components_list != []:
            form = ChecklistDialog('Create new assembly', uploaded_components_label_list, checked=True)
            if form.exec_() == QtGui.QDialog.Accepted:
                # print(form.choices)
                selected_object_label_list = form.choices
                self.assembly_name = form.assembly_name
                if text_follows_rules(self.assembly_name) ==True:
                    self.selected_objects = GetSelectedAssemblyObjects(uploaded_components_list, uploaded_components_label_list, selected_object_label_list)
                    print(self.assembly_name)
                    for obj in self.selected_objects:
                        print(obj.Label, obj.Nucleus_link_usd, obj.Nucleus_link_stp)
                    self.assembly_items_usd_links = [obj.Nucleus_link_usd for obj in self.selected_objects]
                    self.assembly_items_stp_links = [obj.Nucleus_link_stp for obj in self.selected_objects]

                    stdout, stderr, assembly_usd_link = CreateNewAssemblyOnNucleus(self.currentProjectURL, 
                        assembly_name = self.assembly_name, 
                        assembly_items_usd_links=self.assembly_items_usd_links, 
                        assembly_items_stp_links=self.assembly_items_stp_links)
                    print(stdout)
                    print(stderr)
                    print(assembly_usd_link)
                    FreeCAD.assembly_usd_link = assembly_usd_link
                    self.current_assembly_URL_text.setText(' \u2705 Current assembly: '+FreeCAD.assembly_usd_link)
                    self.status_header_text.setText(' Status: \u2705 Ready')
                else:
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Warning)
                    msgBox.setText("Assembly name must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")
                    msgBox.exec_()
                    self.flow_create_new_assembly()
        else:
            print('[WARN] No components in the current workspace have been pushed to this project! Push each item to Nucleus and try again.')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setText("No components in the current workspace have been pushed to this project! \nPush each item to Nucleus and try again.")
            msgBox.exec_()

    def flow_open_existing_assembly(self):
        stdout, stderr, self.existing_assembly_usd_links = FindExistingAssembliesOnNucleus(self.currentProjectURL)
        if self.existing_assembly_usd_links != None:
            assembly_usd_names = [assy_usdlink.split('/')[-1] for assy_usdlink in self.existing_assembly_usd_links]
            print(self.existing_assembly_usd_links)
            dialog_txt = 'Select an existing assembly to import:'
            assembly_name, ok = QtGui.QInputDialog.getItem(self.form, "Omniverse Connector for FreeCAD", dialog_txt, assembly_usd_names, 0, False)
            if ok and assembly_name:
                print(assembly_name)
                selected_assembly_usd_link = [usdlink for usdlink in self.existing_assembly_usd_links if assembly_name in usdlink][0]
                print(selected_assembly_usd_link)
                FreeCAD.assembly_usd_link = selected_assembly_usd_link
                self.current_assembly_URL_text.setText(' \u2705 Current assembly: '+FreeCAD.assembly_usd_link)
                self.status_header_text.setText(' Status: \u2705 Ready')
                
                start_fetch_xform = time.time()
                stdout, stderr, prim_data =  GetPrimReferenceXForms(selected_assembly_usd_link)
                print('FETCH COMPONENT XFORM:', time.time()-start_fetch_xform, 's.')
                print(prim_data)
                token = str(RandomTokenGenerator())

                for dict_entry in prim_data:
                    stplink = dict_entry['step-path']
                    usdlink = dict_entry['ref-path']
                    start_fetch_geom = time.time()
                    rotation = dict_entry['rot-xyz'][::-1]
                    imported_obj = _DownloadCmdWrapper(stplink, usdlink, token)
                    imported_obj.Placement.Base = FreeCAD.Vector(dict_entry['transform'])
                    imported_obj.Placement.Rotation = FreeCAD.Rotation(*rotation)
                    # add rotation thing here!!
                    print('FETCH SINGLE COMPONENT:', time.time()-start_fetch_geom, 's.')


                
        else:
            print('[WARN] No existing assemblies found for this project!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setText("No existing assemblies found for this project!")
            msgBox.exec_()
    def flow_upload_assembly_changes(self):
        #func to update assembly positions on nucleus
        if FreeCAD.assembly_usd_link!= None:
            assembly_usd_link = FreeCAD.assembly_usd_link

            component_usd_links, base_placement = get_assembly_component_placement(type='base')
            component_usd_links, rotation_placement = get_assembly_component_placement(type='rotation')

            stdout, stderr = MoveAssemblyXformPositions(assembly_usd_link, component_usd_links, base_placement, rotation_placement)

        else:
            print('[WARN] No assembly link for this project specified to push to!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("No assembly link for this project specified to push to!")
            msgBox.exec_()
        return None
    def flow_download_assembly_changes(self):
        if FreeCAD.assembly_usd_link!= None:
            doc = FreeCAD.ActiveDocument
            assembly_usd_link = FreeCAD.assembly_usd_link
            stdout, stderr, prim_data =  GetPrimReferenceXForms(assembly_usd_link)
            valid_freecad_objects = [obj for obj in doc.Objects if hasattr(obj, 'Nucleus_link_stp')]
            for dict_entry in prim_data:
                stplink = dict_entry['step-path']
                usdlink = dict_entry['ref-path']
                rotation = dict_entry['rot-xyz'][::-1]
                freecad_object = [obj for obj in valid_freecad_objects if obj.Nucleus_link_usd == usdlink][0]
                freecad_object.Placement.Base = FreeCAD.Vector(dict_entry['transform'])
                freecad_object.Placement.Rotation = FreeCAD.Rotation(*rotation)
                print('[INFO] Moving and rotating ', str(freecad_object.Label), 'to ', dict_entry['transform'], rotation)

        else:
            print('[WARN] No assembly link specified to fetch from!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("No assembly link specified to fetch from!")
            msgBox.exec_()
        return None



    def flow_start_live_assy_mode(self):
        # blocked function for further development
        if self.live_mode_button.isChecked():
            
            if FreeCAD.assembly_usd_link !=None:
                success, list_of_sessions, error_code = live_get_available_sessions(FreeCAD.assembly_usd_link)
                print('SUCCESS:', success)
                print('List of sessions:', list_of_sessions)
                print('Error code:', error_code)
                if success==True:
                    dialog_txt = 'Select available sessions'
                    session_name, ok = QtGui.QInputDialog.getItem(self.form, "Omniverse Connector for FreeCAD", dialog_txt, list_of_sessions, 0, False)
                    if ok and session_name:
                        cmd = get_qproc_command_start_live(FreeCAD.assembly_usd_link, session_name)
                        if self.proc is None:
                            self.live_mode_button.setText('(EXPERIMENTAL) Live assembly mode ACTIVE')
                            print('Starting live sync..')
                            print(cmd)
                            self.proc = QtCore.QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
                            self.proc.readyReadStandardOutput.connect(self.move_components_on_stdout)
                            self.proc.readyReadStandardError.connect(self.handle_stderr)
                            self.proc.stateChanged.connect(self.handle_state)
                            self.proc.finished.connect(self.process_finished)  # Clean up once complete.
                            self.proc.start("powershell", [cmd])
                    else:
                        self.live_mode_button.setChecked(False)
                        print('No session selected!')

                elif success==False:
                    self.live_mode_button.setChecked(False)
                    print('No sessions found!')
            else:
                self.live_mode_button.setChecked(False)
                print('No assembly link!')
        else:
            self.live_mode_button.setText('(EXPERIMENTAL) Live assembly mode')
            print('Exiting live session process...')
            self.kill_live_process()

    def kill_live_process(self):
        if self.proc is not None:
            print('Sending quit command to live session ...')
            quit_cmd = 'q'
            quit_cmd = bytes(str(quit_cmd)+'\n', 'utf-8')
            self.proc.write(quit_cmd)
            self.proc.waitForReadyRead()
            self.proc.closeWriteChannel()
            self.proc.waitForFinished()
            print('Sent quit command to process.')
    def handle_stderr(self):
        data = self.proc.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        print(stderr)

    def handle_stdout(self):
        data = self.proc.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        print(stdout)

    def handle_state(self, state):
        states = {
            QtCore.QProcess.NotRunning: 'Not running',
            QtCore.QProcess.Starting: 'Starting',
            QtCore.QProcess.Running: 'Running',
        }
        state_name = states[state]
        print(f"State changed: {state_name}")

    def process_finished(self):
        print("Process finished.")
        self.proc = None

    def move_components_on_stdout(self):
        line = self.proc.readAllStandardOutput()
        line = bytes(line).decode("utf8")
        # print(line)
        if self.currentProjectURL in line:
            downstream_data = line.split('|')
            downstream_data = [data.strip() for data in downstream_data][:-1]
            downstream_data_list = [{'ref-path': downstream_data[i], 'transform': ast.literal_eval(downstream_data[i + 1]),'rot-xyz': ast.literal_eval(downstream_data[i + 2])} for i in range(0, len(downstream_data), 3)]
            for downstream_entry in downstream_data_list:
                usdlink = downstream_entry['ref-path']
                rotation = downstream_entry['rot-xyz'][::-1]
                freecad_object = [obj for obj in self.valid_freecad_objects if obj.Nucleus_link_usd == usdlink][0]
                freecad_object.Placement.Base = FreeCAD.Vector(downstream_entry['transform'])
                freecad_object.Placement.Rotation = FreeCAD.Rotation(*rotation)

class live_assy_dialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(live_assy_dialog, self).__init__(parent)
        # Create widgets
        self.edit = QtGui.QLineEdit("Write my name here")
        self.button = QtGui.QPushButton("Show Greetings")
        # Create layout and add widgets
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    # Greets the user
    def greetings(self):
        print(f"Hello {self.edit.text()}")
# class run_live_sync(QtCore.QObject):
#     def __init__(self, project_link, assembly_usd_link, session_name):
#         self.proc = QtCore.QProcess(self)
#         self.cmd = get_qproc_command_start_live(assembly_usd_link, session_name)
#         self.project_link
#     def start_live_sync(self):
#         self.proc.start("powershell", [self.cmd])



def get_qproc_command_start_live(usdlink, session_name):
    doc = FreeCAD.ActiveDocument
    FreeCAD.setActiveDocument(doc.Name)
    currentProjectURL = GetCurrentProjectLinkNoPrint()
    # current_instances = set(doc.findObjects())
    error_code = None
    success=None

    # Batch file where the OV USD fetcher lives
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName(live=True)
    batchfilepath = batchfilepath+batchfilename

    cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --session_name ' + session_name + ' --start_live '
    return cmd    


async def run_live_assembly_listener(assembly_link, session_name):
    asyncio.new_event_loop().create_task(live_start_session(FreeCAD.assembly_usd_link, session_name))



def MoveAssemblyXformPositions(assemblyURL, component_usd_links, xform_translate, xform_rotation):
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName()
    batchfilepath = batchfilepath+batchfilename

    
    component_usd_links = ' '.join(component_usd_links)
    xform_rotation = parse_list_into_set_srt_command_arg(xform_rotation)
    xform_translate = parse_list_into_set_srt_command_arg(xform_translate)

    cmd = batchfilepath + ' --nucleus_url '+ str(assemblyURL) + ' --move_assembly ' + ' --set_rot_xyz ' + str(xform_rotation) + ' --set_transform ' +  str(xform_translate) + ' --asset_usd_links ' + str(component_usd_links)
    print(cmd)
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    # print(stdout[-1])
    stdout = stdout.split('\n')
    stderr = stderr.split('\n')
    return stdout, stderr


def get_freecad_object_from_stp_reference(doc, stp_reference):
    freecad_object = [obj for obj in doc.Objects if obj.Nucleus_link_stp == stp_reference]
    freecad_object = freecad_object[0]
    return freecad_object


def GetSelectedAssemblyObjects(object_list, object_label_list, selected_object_label_list):
    selected_objects = []
    indices_dict = dict((k,i) for i,k in enumerate(object_label_list))
    inter = set(indices_dict).intersection(selected_object_label_list)
    selected_object_indices = [ indices_dict[x] for x in inter ]
    selected_objects = [object_list[i] for i in selected_object_indices]
    return selected_objects

def text_follows_rules(input_string):
    # Regular expression to match the specified rules
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'

    # Check if the input string matches the pattern
    if re.match(pattern, input_string):
        return True
    else:
        return False
def no_restricted_strings_in_project_link(projectlink):
    assembly_in_link = 'assembly' in projectlink
    asset_in_link = 'asset' in projectlink
    return not(asset_in_link or assembly_in_link)

class SpecifyOmniverseURLPanel:
    def __init__(self,widget):

        self.form = widget
        layout = QtGui.QVBoxLayout()
        self.URL_TextLabel = QtGui.QLabel("Input project URL:")
        self.panel_name_text = QtGui.QLabel("Omniverse Connection Settings")

        currentProjectURL = GetCurrentProjectLinkNoPrint()
        currentSTPLink = GetCurrentSTPLinkNoPrint()
        currentUSDLink = GetCurrentUSDLinkNoPrint()
        

        self.currentProjectURL_text = QtGui.QLabel(" \u274c No project Nucleus URL specified ")
        self.selected_asset_text = QtGui.QLabel(" \u274c No STP asset selected.")
        self.selected_asset_usd_text = QtGui.QLabel(' \u274c No corresponding USD asset selected.')

        if currentSTPLink is not None:
            self.selected_asset_text = QtGui.QLabel(" \u2705 Current STP asset URL: "+currentSTPLink)

        if currentProjectURL is not None:
	        self.currentProjectURL_text = QtGui.QLabel(" \u2705 Current project URL: "+currentProjectURL)

        if currentUSDLink is not None:
            self.selected_asset_usd_text = QtGui.QLabel(' \u2705 Corresponding USD: '+ currentUSDLink)

        self.open_existing_project_button = QtGui.QPushButton("Open existing project")
        self.open_existing_project_button.clicked.connect(self.inputProjectURL)
        self.create_new_project_button = QtGui.QPushButton("Create new project")
        self.create_new_project_button.clicked.connect(self.createNewProject)



        # The layout will be horizontal
        # Spin Box that takes doubles
        self.settings_label = QtGui.QLabel('Omniverse Connector Settings')
        self.URL_Text = QtGui.QLineEdit()

        self.create_asset_button = QtGui.QPushButton("Create new asset in project")
        self.create_asset_button.clicked.connect(self.dialogBoxCreateNewAsset)

        self.browse_button = QtGui.QPushButton("Browse project assets")
        self.browse_button.clicked.connect(self.getListItem)
        # todo - maybe turn into refresh connection/check connection
        self.check_button = QtGui.QPushButton("Validate link")
        self.check_button.clicked.connect(self.checkProjectURL)
        # Default value
        self.URL_Text.setPlaceholderText('omniverse://hostname/path/to/your/project')
        
        # suffix to indicate the units
        # layout.addWidget(self.URL_TextLabel)
        # layout.addWidget(self.URL_Text)
        layout.addWidget(self.panel_name_text)
        layout.addWidget(self.open_existing_project_button)
        layout.addWidget(self.create_new_project_button)
        # layout.addWidget(self.check_button)
        layout.addWidget(self.create_asset_button)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.currentProjectURL_text)
        layout.addWidget(self.selected_asset_text)
        layout.addWidget(self.selected_asset_usd_text)

        self.form.setLayout(layout)

    def createNewProject(self):
        dialog = QtGui.QInputDialog(self.form)
        dialog.setWindowTitle('Omniverse Connector for FreeCAD')
        dialog.setLabelText('Create new project on Nucleus')
        dialog.show()

        dialog.findChild(QtGui.QLineEdit).hide()
        # TODO FIX CREATE NEW PROJECT BUG!!
        text_format_rules = QtGui.QLabel("Project names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")

        hostname_prompt = QtGui.QLabel("Nucleus host name:")
        input_hostname = QtGui.QLineEdit()
        projectname_prompt = QtGui.QLabel("New project name:")
        input_projectname = QtGui.QLineEdit()

        dialog.layout().insertWidget(1, hostname_prompt)
        dialog.layout().insertWidget(2, input_hostname)
        dialog.layout().insertWidget(3, projectname_prompt)
        dialog.layout().insertWidget(4, input_projectname)
        dialog.layout().insertWidget(5, text_format_rules)

        dialog.exec_()
        # print(host_name=='')
        hostname_new_project = input_hostname.text()
        name_new_project = input_projectname.text()
        if hostname_new_project!='':
            if name_new_project!='':
                if text_follows_rules(name_new_project) ==True:
                    if no_restricted_strings_in_project_link(name_new_project) == True:
                        ok, stdout, stderr = CreateNewProjectOnNucleus(host_name = hostname_new_project, project_name = name_new_project)
                        if ok==False:
                            print('[WARN] Failed to create new project!')
                            [print('OmniClient:'+line) for line in stdout]
                            print(stderr)
                            msgBox = QtGui.QMessageBox()
                            msgBox.setIcon(QtGui.QMessageBox.Critical)
                            msgBox.setText("Failed to create new project!")
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
                        # print('[WARN] Failed to create new project!')
                        msgBox = QtGui.QMessageBox()
                        msgBox.setIcon(QtGui.QMessageBox.Warning)
                        msgBox.setText("Project names cannot contain the text 'asset' or 'assembly'.")
                        msgBox.exec_()
                        self.createNewProject()
                else:
                    # print('[WARN] Failed to create new project!')
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Warning)
                    msgBox.setText("Project names must start with a letter.\nIt can contain letters, digits, or underscores, and cannot contain spaces.")
                    msgBox.exec_()
                    self.createNewProject()
            else:
                # print('[WARN] Failed to create new project!')
                msgBox = QtGui.QMessageBox()
                msgBox.setIcon(QtGui.QMessageBox.Warning)
                msgBox.setText("No project name specified!")
                msgBox.exec_()
                self.createNewProject()
        else:
            # print('[WARN] Failed to create new project!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("No hostname specified!")
            msgBox.exec_()

    def set_project_link(self):
        self.input_box_project_url.setText(self.last_project_link)

    def inputProjectURL(self):

        dialog = QtGui.QInputDialog(self.form)
        dialog.setWindowTitle('Omniverse Connector for FreeCAD')
        dialog.setLabelText('Input existing project URL')
        dialog.show()

        dialog.findChild(QtGui.QLineEdit).hide()
        # TODO FIX CREATE NEW PROJECT BUG!!

        
        # hostname_prompt = QtGui.QLabel("Nucleus host name:")
        self.input_box_project_url = QtGui.QLineEdit()
        projecturl_prompt_text = QtGui.QLabel("Enter a link with format omniverse://HOST_NAME/PROJECT_PATH")


        dialog.layout().insertWidget(1, self.input_box_project_url)
        dialog.layout().insertWidget(2, projecturl_prompt_text)

        self.last_project_link = GetLastProjectLinkNoPrint()


        if self.last_project_link != None:
            last_project_completer = QtGui.QCompleter([self.last_project_link])
            self.input_box_project_url.setCompleter(last_project_completer)


        dialog.exec_()
        # print(host_name=='')
        projectURL = self.input_box_project_url.text()

        # projectURL, ok = QtGui.QInputDialog.getText(self.form, 'Omniverse Connector for FreeCAD', 'Input existing project URL:')
        if projectURL!='':
            if '.usd' not in projectURL:
                if no_restricted_strings_in_project_link(projectURL) ==True:
                    check_project_ok = self.checkProjectURL(inputProjectURL = projectURL)
                    if check_project_ok ==True:
                        delete_asset_localdata()
                        self.selected_asset_text.setText(' \u274c No STP asset selected.')
                        self.selected_asset_usd_text.setText(' \u274c No corresponding USD asset selected.')
                else:
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Warning)
                    msgBox.setText("Project links cannot contain the text 'asset' or 'assembly'.\nEnter a link with format omniverse://HOST_NAME/PROJECT_DIRECTORY . ")
                    msgBox.exec_()
                    self.inputProjectURL()       
            else:
                msgBox = QtGui.QMessageBox()
                msgBox.setIcon(QtGui.QMessageBox.Warning)
                msgBox.setText("Project links are folder links and must not include .usd in its path.\nEnter a link with format omniverse://HOST_NAME/PROJECT_DIRECTORY . ")
                msgBox.exec_()
                self.inputProjectURL()

    def checkProjectURL(self, inputProjectURL = None):
        self.check_button.setText('\u9203 Validating link ...')
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
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Critical)
                    msgBox.setText("[ERROR] Failed to authenticate with nucleus at "+savedURL)
                    msgBox.exec_()
                    self.currentProjectURL_text.setText('No project Nucleus URL specified.')
                    delete_project_link()
                    ok = False
                else:
                    self.check_button.setText('Link validated. Revalidate?')
                    self.currentProjectURL_text.setText(' \u2705 Project directory: '+savedURL)
                    ok = True

        elif currentProjectURL is not None and inputProjectURL==None:
            SaveProjectLinkAsTextFile(currentProjectURL)
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
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
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Critical)
                    msgBox.setText("[ERROR] Failed to authenticate with nucleus at "+savedURL)
                    msgBox.exec_()
                    self.currentProjectURL_text.setText(' \u274c No Project Nucleus URL specified.')
                    delete_project_link()
                    ok = False
                else:
                    self.check_button.setText('Link validated. Revalidate?')
                    self.currentProjectURL_text.setText('\u2705 Project directory: '+savedURL)
                    ok = True
        else:
            print('[WARN] No project link specified!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setText("No project link specified!")
            msgBox.exec_()
            ok = False

        return ok
    def dialogBoxCreateNewAsset(self):
        currentProjectURL = GetCurrentProjectLinkNoPrint()
        if currentProjectURL:
            dialog = QtGui.QInputDialog(self.form)
            dialog.setWindowTitle('Omniverse Connector for FreeCAD')
            dialog.setLabelText('Create new asset on Nucleus')
            
            dialog.show()

            dialog.findChild(QtGui.QLineEdit).hide()

            assetname_prompt = QtGui.QLabel("New asset name:")
            input_assetname = QtGui.QLineEdit()

            text_format_rules = QtGui.QLabel("Project names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")

            dialog.layout().insertWidget(1, assetname_prompt)
            dialog.layout().insertWidget(2, input_assetname)
            dialog.layout().insertWidget(3, text_format_rules)
            current_project_dialogtext = QtGui.QLabel(' Current project:'+ currentProjectURL)


            dialog.exec_()
            # print(host_name=='')
            asset_name = input_assetname.text()

            token = str(RandomTokenGenerator())

        
            if asset_name!='':
                if text_follows_rules(asset_name)==True:
                    print('Creating new asset '+ asset_name+' on project '+ currentProjectURL)
                    stdout, stderr, stplink, usdlink = CreateNewAssetOnNucleus(asset_name, use_url = True, projectURL=currentProjectURL, token=token)
                    self.selected_asset_text.setText(' \u2705 Selected asset: '+stplink)
                    self.selected_asset_usd_text.setText(' \u2705 Corresponding USD: '+ usdlink)
                    SaveSTPLinkAsTextFile(stplink)
                    SaveUSDLinkAsTextFile(usdlink)

                    GetAuthCheck(stplink,  filetype='stp')
                    GetAuthCheck(usdlink,  filetype='usd')
                else:
                    # print('[WARN] Failed to create new project!')
                    msgBox = QtGui.QMessageBox()
                    msgBox.setIcon(QtGui.QMessageBox.Warning)
                    msgBox.setText("Asset names must start with a letter. \nIt can contain letters, digits, or underscores, and cannot contain spaces.")
                    msgBox.exec_()
                    self.dialogBoxCreateNewAsset()
            else:
                print('[WARN] No asset name specified!')
                msgBox = QtGui.QMessageBox()
                msgBox.setIcon(QtGui.QMessageBox.Warning)
                msgBox.setText("No asset name specified!")
                msgBox.exec_()
        else:
            print('[WARN] No project link specified or found!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("No project link specified or found!")
            msgBox.exec_()


    def getListItem(self):
        # TODO: MAKE BUTTON FOR CREATE NEW ASSET
        currentProjectURL = GetCurrentProjectLinkNoPrint()
        if currentProjectURL is not None:
            FindUSDandSTPFiles(currentProjectURL)
            item_list = GetListOfSTPFiles()
            usd_list = GetListOfUSDFiles()

            if item_list!=None and usd_list!=None:
                usd_list = [link_entry.strip() for link_entry in usd_list]
                item_list = [link_entry.strip() for link_entry in item_list]
                #TODO: change so that the getItem doesnt show the entire URL
                
                new_asset_string = 'Create new asset...'
                item_list.append(new_asset_string)
                if len(item_list)>2:
                    dialog_txt = "Found "+ str(len(item_list)-1) +' geometry assets. Select one or create new asset:'
                else:
                    dialog_txt = "Found " +'1 geometry asset. Select one or create new asset:'
                item, ok = QtGui.QInputDialog.getItem(self.form, "Omniverse Connector for FreeCAD", dialog_txt, item_list, 0, False)
                if ok and item:
                    if item !=new_asset_string:
                        self.selected_asset = item
                        print(item)
                        print(usd_list)
                        usdlink = find_corresponding_element(item, item_list, usd_list)
                        print(usdlink)

                        SaveSTPLinkAsTextFile(item)
                        SaveUSDLinkAsTextFile(usdlink)

                        GetAuthCheck(item,  filetype='stp')
                        GetAuthCheck(usdlink,  filetype='usd')

                        self.selected_asset_text.setText(' \u2705 Selected asset: '+item)
                        self.selected_asset_usd_text.setText(' \u2705 Corresponding USD: '+ usdlink)
                    elif item==new_asset_string:
                        self.dialogBoxCreateNewAsset()
            elif item_list==None and usd_list==None:
                print('No assets found.')
                msg = QtGui.QMessageBox()
                msg.setIcon(QtGui.QMessageBox.Question)
                msg.setText('No assets found. Create new?')
                msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                ret = msg.exec_()
                if ret==QtGui.QMessageBox.Ok:
                    self.dialogBoxCreateNewAsset()
                #TODO: make new function in this class to create new asset (msg input dialog) and then call it.
        else:
            print('[WARN] No project link specified!')
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            msgBox.setText("No project link specified!")
            msgBox.exec_()            
            


    # Ok and Cancel buttons are created by default in FreeCAD Task Panels
    # What is done when we click on the ok button.
    def accept(self):
        FreeCADGui.Control.closeDialog() #close the dialog

class SpecifyAssetItemPanel:
    #DEPRECATED - TEST FUNCTION
    def __init__(self,widget):
        self.form = widget
        layout = QtGui.QVBoxLayout()
        self.URL_TextLabel = QtGui.QLabel("Select asset to edit from list:")
        currentURL = GetCurrentUSDLinkNoPrint()
        self.currentURL = QtGui.QLabel("No asset specified.")
        if currentURL is not None:
            self.currentURL = QtGui.QLabel("Current URL: "+currentURL)
        # else:
        #   self.currentURL = QtGui.QLabel("No Nucleus URL specified.")
        # The layout will be horizontal
        # Spin Box that takes doubles
        self.URL_Text = QtGui.QLineEdit()
        self.browse_button = QtGui.QPushButton("Select available assets")
        self.browse_button.clicked.connect(self.getListItem)

        # Default value
        # self.URL_Text.setPlaceholderText('omniverse://hostname/path/to/your.stp')
        # suffix to indicate the units
        layout.addWidget(self.URL_TextLabel)
        layout.addWidget(self.currentURL)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.URL_Text)
        
        self.form.setLayout(layout)

    def getListItem(self):
        items = ("haha", "hihi", "hoho")
        item, ok = QtGui.QInputDialog.getItem(self.form, "select input", "list of hahas", items, 0, False)
        if ok and item:
            self.URL_Text.setText('\u2705' +str(item))
            self.selected_asset = item

    # Ok and Cancel buttons are created by default in FreeCAD Task Panels
    # What is done when we click on the ok button.
    def accept(self):
        print(self.selected_asset)
        FreeCADGui.Control.closeDialog() #close the dialog



# class SpecifyOmniverseFolderPanel:
#     # DONE - this is a backup that doesnt really work: point to folder instead WIP
#     def __init__(self,widget):
#         self.form = widget
#         layout = QtGui.QVBoxLayout()
#         self.URL_TextLabel = QtGui.QLabel("Omniverse Nucleus Folder URL:")
#         currentURL = GetCurrentUSDLinkNoPrint()
#         self.currentURL = QtGui.QLabel("No Nucleus Folder URL specified.")
#         if currentURL is not None:
#             self.currentURL = QtGui.QLabel("Current URL: "+currentURL)
#         # else:
#         #   self.currentURL = QtGui.QLabel("No Nucleus URL specified.")
#         # The layout will be horizontal
#         # Spin Box that takes doubles
#         self.URL_Text = QtGui.QLineEdit()
#         # Default value
#         self.URL_Text.setPlaceholderText('omniverse://hostname/path/to/your.stp')
#         # suffix to indicate the units
#         layout.addWidget(self.URL_TextLabel)
#         layout.addWidget(self.URL_Text)
#         layout.addWidget(self.currentURL)
#         self.form.setLayout(layout)

#     # Ok and Cancel buttons are created by default in FreeCAD Task Panels
#     # What is done when we click on the ok button.
#     def accept(self):
#         currentURL = GetCurrentUSDLinkNoPrint()
#         hostPath = self.URL_Text.text()
#         if hostPath !='':
#             SaveUSDLinkAsTextFile(hostPath)
#             print('New Omniverse Nucleus USD link at: ', hostPath)
#             savedURL = GetCurrentUSDLinkNoPrint()
#             if savedURL is not None:
#                 GetAuthCheck(savedURL)

#         elif currentURL is not None and hostPath=='':
#             SaveUSDLinkAsTextFile(currentURL)
#             print('[WARN] No USD link specified!')
#             print('Revert to initial Omniverse Nucleus USD link at: ', currentURL)
#             savedURL = GetCurrentUSDLinkNoPrint()
#             if savedURL is not None:
#                 GetAuthCheck(savedURL)
#         else:
#             print('[WARN] No USD link specified!')
            
#         FreeCADGui.Control.closeDialog() #close the dialog

    # What is done when we click on the cancel button.
    # commented because this is the default behaviour
    #def reject(self):
    #   FreeCADGui.Control.closeDialog()

# GUI command that links the Python script
class _GetAssetCmd:
    """Command to create a panel where user specifies URL of nucleus file
    """

    def Activated(self):
        # what is done when the command is clicked
        # creates a panel with a dialog
        baseWidget = QtGui.QWidget()
        panel = SpecifyAssetItemPanel(baseWidget)
        # having a panel with a widget in self.form and the accept and 
        # reject functions (if needed), we can open it:
        FreeCADGui.Control.showDialog(panel)

    def GetResources(self):
        # icon and command information
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'testing item',
            'test item')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'test item',
            'test item')
        return {
            'Pixmap': __dir__ + '/icons/ovConnect_url.svg',
            'MenuText': MenuText,
            'ToolTip': ToolTip}

    def IsActive(self):
        # The command will be active if there is an active document
        return not FreeCAD.ActiveDocument is None

# GUI command that links the Python script
class _GetURLPanel:
    """Command to create a panel where user specifies URL of nucleus file
    """

    def Activated(self):
        # what is done when the command is clicked
        # creates a panel with a dialog
        baseWidget = QtGui.QWidget()
        panel = SpecifyOmniverseURLPanel(baseWidget)
        # having a panel with a widget in self.form and the accept and 
        # reject functions (if needed), we can open it:
        FreeCADGui.Control.showDialog(panel)

    def GetResources(self):
        # icon and command information
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
        # The command will be active if there is an active document
        return not FreeCAD.ActiveDocument is None

class _GetAssemblyPanel:
    """Command to create a panel where user specifies URL of nucleus file
    """

    def Activated(self):
        # what is done when the command is clicked
        # creates a panel with a dialog
        # fc_main_window = FreeCADGui.getMainWindow()

        baseWidget = QtGui.QWidget()
        panel = OmniverseAssemblyPanel(baseWidget)


        # baseWidget = QtGui.QDockWidget()
        # frame = QtGui.QWidget()
        # frame.ui = OmniverseAssemblyPanel(frame)
        # frame.ui.setupUi(frame)
        # baseWidget.setFeatures( QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetFloatable|QtGui.QDockWidget.DockWidgetClosable )
        # baseWidget.setWidget(frame)
        # assy_panel_widget = OmniverseAssemblyPanel(baseWidget)
        # print(type(assy_panel_widget))
        # baseWidget.setWidget(frame)
        # fc_main_window.addDockWidget(QtCore.Qt.LeftDockWidgetArea,baseWidget)
        # having a panel with a widget in self.form and the accept and 
        # reject functions (if needed), we can open it:
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
        # The command will be active if there is an active document
        is_activeDocumentExists = not FreeCAD.ActiveDocument is None
        # is_activeProjectLinkExists = FreeCAD.OV_link_project !=None

        project_permission = GetCurrentProjectPermissions()
        projectURL = GetCurrentProjectLinkNoPrint()

        is_projectPermissionOK = project_permission == 'OK_ACCESS'
        is_projectURLExists = projectURL!= None

        is_checksValid = is_activeDocumentExists == True and is_projectPermissionOK==True and is_projectURLExists==True

        return is_checksValid


FreeCADGui.addCommand('OVconnect_URLPanel', _GetURLPanel())
FreeCADGui.addCommand('OVconnect_push_to_nucleus', _UploadCmd())
FreeCADGui.addCommand('OVconnect_pull_from_nucleus', _DownloadCmd())
FreeCADGui.addCommand('OVconnect_clear_junk_files', _ClearJunkCmd())
FreeCADGui.addCommand('OVconnect_assembly_tools', _GetAssemblyPanel())
# FreeCADGui.addCommand('OVconnect_user_auth', _CheckConnectionCmd())
