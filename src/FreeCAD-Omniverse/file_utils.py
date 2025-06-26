import os
from utils import *
import shutil
import FreeCAD
__dir__ = os.path.dirname(__file__)

def GetFetcherScriptsDirectory():
    workbench_path = os.path.dirname(os.path.realpath(__file__))
    omni_directory = os.path.join(workbench_path, 'omniConnect')
    return omni_directory

def GetLocalDirectoryName():
    workbench_path = os.path.dirname(os.path.realpath(__file__))
    local_directory = os.path.join(workbench_path, 'session_local')
    if not os.path.exists(local_directory):
        os.makedirs(local_directory)
    return local_directory

def GetBatchFileName(live=False):
    if live == False:
        batchfilename = "run_py_omni_client.bat"
    else:
        batchfilename = 'run_py_omni_live_client.bat'
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

def SaveUSDLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_usd = clean_omniverse_path(str(usdlink))
    textfile_name = os.path.join(local_directory, 'usdlink.txt')
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveSecondaryUSDLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_usd = clean_omniverse_path(str(usdlink))
    textfile_name = os.path.join(local_directory, 'secondary_usdlink.txt')
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveLastProjectLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_project= clean_omniverse_path(str(usdlink))
    textfile_name = os.path.join(local_directory, 'last_projectlink.txt')
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveProjectLinkAsTextFile(usdlink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_project= clean_omniverse_path(str(usdlink))
    textfile_name = os.path.join(local_directory, 'projectlink.txt')
    with open(textfile_name, 'w') as f:
        f.write(usdlink)

def SaveSTPLinkAsTextFile(stplink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_stp = clean_omniverse_path(str(stplink))
    textfile_name = os.path.join(local_directory, 'stplink.txt')
    with open(textfile_name, 'w') as f:
        f.write(stplink)

def SaveSecondarySTPLinkAsTextFile(stplink):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_link_stp = clean_omniverse_path(str(stplink))
    textfile_name = os.path.join(local_directory, 'secondary_stplink.txt')
    with open(textfile_name, 'w') as f:
        f.write(stplink)

def SaveUSDPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_usd =permission
    textfile_name = os.path.join(local_directory, 'usd_permission.txt')
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveSecondaryUSDPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_usd =permission
    textfile_name = os.path.join(local_directory, 'secondary_usd_permission.txt')
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveProjectPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_project =permission
    textfile_name = os.path.join(local_directory, 'project_permission.txt')
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveSTPPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_stp =permission
    textfile_name = os.path.join(local_directory, 'stp_permission.txt')
    with open(textfile_name, 'w') as f:
        f.write(permission)

def SaveSecondarySTPPermissionsAsTextFile(permission):
    local_directory = GetLocalDirectoryName()
    FreeCAD.OV_permission_stp =permission
    textfile_name = os.path.join(local_directory, 'secondary_stp_permission.txt')
    with open(textfile_name, 'w') as f:
        f.write(permission)

def delete_project_link():
    local_directory = GetLocalDirectoryName()
    textfile_name = os.path.join(local_directory, 'projectlink.txt')
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
    textfile_names = [
        os.path.join(local_directory, 'usdlink.txt'),
        os.path.join(local_directory, 'usd_permission.txt'),
        os.path.join(local_directory, 'stplink.txt'),
        os.path.join(local_directory, 'stp_permission.txt'),
        os.path.join(local_directory, 'secondary_usd_permission.txt'),
        os.path.join(local_directory, 'secondary_stp_permission.txt'),
        os.path.join(local_directory, 'secondary_usdlink.txt'),
        os.path.join(local_directory, 'secondary_stplink.txt'),
    ]
    
    for asset_data in textfile_names:
        try:
            os.remove(asset_data)
        except FileNotFoundError:
            # print(f"The file '{asset_data}' does not exist.")
            pass
        except PermissionError:
            # print(f"Permission denied. Unable to delete the file '{asset_data}'.")
            pass
        except Exception as e:
            print(f"An error occurred while deleting the file '{asset_data}': {str(e)}")

def GetCurrentUSDPermissions(secondary=False):
    if secondary==False:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'usd_permission.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                permission = lines[0]
            else:
                permission=None
            return permission
        except IOError:
            return None
    elif secondary == True:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'secondary_usd_permission.txt')
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
        textfile_name = os.path.join(local_directory, 'project_permission.txt')
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            permission = lines[0]
        else:
            permission=None
        return permission
    except IOError:
        return None

def GetCurrentSTPPermissions(secondary=False):
    if secondary==False:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'stp_permission.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                permission = lines[0]
            else:
                permission=None
            return permission
        except IOError:
            return None
    elif secondary == True:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'secondary_stp_permission.txt')
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
        textfile_name = os.path.join(local_directory, 'usdlink.txt')
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

def GetCurrentUSDLinkNoPrint(secondary=False):
    if secondary == False:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'usdlink.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                usdlink = lines[0]
            else:
                usdlink=None
            return usdlink
        except IOError:
            return None
    else:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'secondary_usdlink.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                usdlink = lines[0]
            else:
                usdlink=None
            return usdlink
        except IOError:
            return None 

def GetCurrentProjectLinkNoPrint():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = os.path.join(local_directory, 'projectlink.txt')
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
        textfile_name = os.path.join(local_directory, 'last_projectlink.txt')
        with open(textfile_name) as f:
            lines = f.readlines()
        if len(lines) != 0:
            usdlink = lines[0]
        else:
            usdlink=None
        return usdlink
    except IOError:
        return None

def GetCurrentSTPLinkNoPrint(secondary=False):
    if secondary == False:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'stplink.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                usdlink = lines[0]
            else:
                usdlink=None
            return usdlink
        except IOError:
            return None
    else:
        try:
            local_directory = GetLocalDirectoryName()
            textfile_name = os.path.join(local_directory, 'secondary_stplink.txt')
            with open(textfile_name) as f:
                lines = f.readlines()
            if len(lines) != 0:
                usdlink = lines[0]
            else:
                usdlink=None
            return usdlink
        except IOError:
            return None



def check_file_isempty(file_path):
    #Checks whether a file is empty or not. Used for dealing with placeholder files
    expected_content = b'EMPTY_FILE'
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            # print(content)
            return content == expected_content
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False


def GetListOfSTPFiles():
    try:
        local_directory = GetLocalDirectoryName()
        textfile_name = os.path.join(local_directory, 'stplist.txt')
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
        textfile_name = os.path.join(local_directory, 'usdlist.txt')
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