import os
from utils import *
import shutil
import FreeCAD
import subprocess
import Import
import Mesh
__dir__ = os.path.dirname(__file__)


def CreateNewProjectOnNucleus(host_name, project_name, make_public=False):
    """
    Creates a new project directory on Nucleus.

    Args:
        host_name (str): Nucleus host.
        project_name (str): Name of the project to create.
        make_public (bool): Whether the project should be public.

    Returns:
        tuple: (ok, stdout_lines, stderr_lines)
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    cmd = (
        f'{batch_path} --create_new_project --project_name {project_name} '
        f'--host_name {host_name} {"--make_public" if make_public else ""}'
    )

    print(f'[CMD] {cmd}')
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout_decoded, stderr_decoded = stdout.decode(), stderr.decode()

    ok = "error" not in stdout_decoded.lower()
    return ok, stdout_decoded.split('\n'), stderr_decoded.split('\n')

def CreateNewAssetOnNucleus(asset_name, use_url=True, projectURL=None, host_name=None, project_name=None, token=None):
    """
    Creates a new asset on Nucleus and returns associated links and any error.

    Returns:
        tuple: (stdout_lines, stderr_lines, stplink, usdlink, error)
    """
    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())

    if use_url:
        cmd = f'{batch_path} --create_new_asset --nucleus_url {projectURL} --asset_name {asset_name}'
    else:
        cmd = f'{batch_path} --create_new_asset --project_name {project_name} --host_name {host_name} --asset_name {asset_name}'
    if token:
        cmd += f' --token {token}'
    print(f'[CMD] {cmd}')
    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout_lines = stdout.decode().split('\n')
    stderr_lines = stderr.decode().split('\n')

    stplink = usdlink = error = None
    for line in map(str.strip, stdout_lines):
        if '.usd' in line:
            usdlink = line
            print(usdlink)
        elif '.stp' in line:
            stplink = line
            print(stplink)
        elif 'ERROR' in line:
            error = line
            usdlink = stplink = None
    return stdout_lines, stderr_lines, stplink, usdlink, error

def UploadUSDToNucleus(usdlink, selected_object, token, secondary=False, overwrite_history=False):
    """
    Uploads a mesh (converted to STL) to a Nucleus USD location using a batch script.

    Args:
        usdlink (str): Nucleus USD URL (primary or secondary depending on 'secondary').
        selected_object (FreeCAD object): The object to export and upload.
        token (str): Unique identifier for the upload session.
        secondary (bool): Whether this is a secondary (fallback) USD location.
        overwrite_history (bool): If True, creates a fresh USd with zero version history

    Returns:
        tuple: (stdout_output, stderr_output)
    """
    # Get permissions for primary or secondary USD
    permission = GetCurrentUSDPermissions(secondary=secondary)

    if permission == 'NO_ACCESS':
        print(f'[ERROR] NO_PERMISSION: Cannot access USD file: {usdlink}')
        print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
        return 'FAIL', 'NO_PERMISSION'

    if permission is None:
        print(f'[ERROR] PERMISSION_NOT_FOUND: Cannot access USD file: {usdlink}')
        print('[ERROR] You have not entered a valid USD link.')
        return 'FAIL', 'PERMISSION_NOT_FOUND'

    if permission == 'OK_ACCESS':
        script_dir = GetFetcherScriptsDirectory().replace(" ", "` ")
        batch_file = GetBatchFileName()
        batch_path = os.path.join(script_dir, batch_file)

        local_dir = GetLocalDirectoryName()
        stl_filename = f'{token}upload.stl'
        stl_path = os.path.join(local_dir, stl_filename)

        print(f'[INFO] Exporting mesh to: {stl_path}')
        print(f'[INFO] Upload token: {token}')

        # Export to STL file
        Mesh.export([selected_object], stl_path)

        # Select push or overwrite mode
        action_flag = '--create_new_usd' if overwrite_history else '--push'

        # Build command
        cmd = f'{batch_path} --nucleus_url {usdlink} --local_directory {local_dir.replace(" ", "` ")} {action_flag} --token {token}'
        print(f'[CMD] {cmd}')

        process = subprocess.Popen(
            ['powershell', cmd],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8'), stderr.decode('utf-8')

    return 'FAIL', 'UNKNOWN_PERMISSION_STATUS'


def UploadSTPToNucleus(stplink, selected_object, token, custom_checkpoint=None, secondary=False):
    """
    Uploads a STEP file to Nucleus using the batch uploader.

    Args:
        stplink (str): The Nucleus STP destination URL.
        selected_object (FreeCAD object): The object to export and upload.
        token (str): Unique identifier for the upload session.
        custom_checkpoint (str, optional): A string to tag this upload with a custom label.
        secondary (bool): Use secondary permission rules if True.

    Returns:
        tuple: (stdout_output, stderr_output)
    """

    permission = GetCurrentSTPPermissions(secondary=secondary)

    if permission == 'NO_ACCESS':
        print(f'[ERROR] NO_PERMISSION: Cannot access STP file: {stplink}')
        print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
        return 'FAIL', 'NO_PERMISSION'

    if permission is None:
        print(f'[ERROR] PERMISSION_NOT_FOUND: Cannot access STP file: {stplink}')
        print('[ERROR] You have not entered a valid Nucleus link.')
        return 'FAIL', 'PERMISSION_NOT_FOUND'

    if permission != 'OK_ACCESS':
        return 'FAIL', 'UNKNOWN_PERMISSION_STATUS'

    # Setup paths
    script_dir = GetFetcherScriptsDirectory().replace(" ", "` ")
    batch_file = GetBatchFileName()
    batch_path = os.path.join(script_dir, batch_file)
    local_dir = GetLocalDirectoryName()
    stp_filename = f'{token}upload.stp'
    stp_path = os.path.join(local_dir, stp_filename)

    print('Unique version identifier:', token)
    print('local_STP_filepath:', stp_path)

    # Export to .stp
    Import.export([selected_object], stp_path)

    # Build command
    cmd = (
        f'{batch_path} --nucleus_url {stplink} '
        f'--local_non_usd_filename {stp_path.replace(" ", "` ")} '
        f'--push_non_usd --token {token}'
    )

    if custom_checkpoint:
        checkpoint_escaped = f'"{custom_checkpoint}"'
        cmd += f' --custom_checkpoint {checkpoint_escaped}'

    print(f'[CMD] {cmd}')

    process = subprocess.Popen(
        ['powershell', cmd],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8')


def GetAuthCheck(usdlink, filetype='usd', secondary=False):
    """
    Calls a nucleus instance and checks if the user has valid permissions.
    """
    error_codes = {'NO_PERMISSION', 'NOT_FOUND', 'NO_AUTH'}
    print(f'Validating connection with {usdlink}')

    batchfilepath = os.path.join(
        GetFetcherScriptsDirectory().replace(" ", "` "),
        GetBatchFileName()
    )
    auth_flag = '--auth_project' if filetype == 'project' else '--auth'
    cmd = f'{batchfilepath} --nucleus_url {usdlink} {auth_flag}'

    process = subprocess.Popen(
        ['powershell', cmd],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    stdout_lines = stdout.decode('utf-8').split('\r\n')
    stderr_output = stderr.decode('utf-8')

    no_access = sum(1 for line in stdout_lines if any(code in line for code in error_codes))
    permission = 'OK_ACCESS' if no_access == 0 else 'NO_ACCESS'

    save_functions = {
        ('usd', False): SaveUSDPermissionsAsTextFile,
        ('stp', False): SaveSTPPermissionsAsTextFile,
        ('project', False): SaveProjectPermissionsAsTextFile,
        ('usd', True): SaveSecondaryUSDPermissionsAsTextFile,
        ('stp', True): SaveSecondarySTPPermissionsAsTextFile
    }

    save_func = save_functions.get((filetype, secondary))
    if save_func:
        save_func(permission)

    print('[ERRORS]', stderr_output)
    return stdout_lines, stderr_output, permission

def DownloadSTPFromNucleus(stplink, token, custom_checkpoint=None):
    """
    Downloads a STEP (.stp) file from Nucleus and inserts it into the active FreeCAD document.
    """
    imported_object, fc_err = None, None
    permission = GetCurrentSTPPermissions()
    print(f'File permission: {permission}')

    if permission != 'OK_ACCESS':
        err_map = {
            'NO_ACCESS': '[ERROR] NO_PERMISSION',
            None: '[ERROR] PERMISSION_NOT_FOUND'
        }
        fc_err = f"{err_map.get(permission, '[ERROR] UNKNOWN')} : Cannot access STP file: {stplink}"
        print(fc_err)
        return False, None, 'FAIL', err_map.get(permission, 'UNKNOWN'), fc_err

    batch_path = os.path.join(GetFetcherScriptsDirectory().replace(" ", "` "), GetBatchFileName())
    local_dir = GetLocalDirectoryName()
    stp_path = os.path.join(local_dir, f'{token}download.stp')

    cmd = (
        f'{batch_path} --nucleus_url {stplink} --pull_non_usd '
        f'--local_non_usd_filename {stp_path.replace(" ", "` ")} --token {token}'
    )
    if custom_checkpoint:
        cmd += f' --custom_checkpoint "{custom_checkpoint}"'
    print(f'[CMD] {cmd}')

    p = subprocess.Popen(['powershell', cmd], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()

    if os.path.exists(stp_path) and not check_file_isempty(stp_path):
        imported_object= Import.insert(stp_path, FreeCAD.ActiveDocument.Name, useLinkGroup=True, merge=False)
        imported_object = imported_object[0][0]
        return True, imported_object, stdout, stderr, None

    fc_err = '[ERROR] EMPTY_ASSET: Placeholder or failed download.' if os.path.exists(stp_path) else '[ERROR] DLOAD_FAIL: STP download failed!'
    print(fc_err)
    return False, None, stdout, stderr, fc_err


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