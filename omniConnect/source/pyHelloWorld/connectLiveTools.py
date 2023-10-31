#!/usr/bin/env python3

###############################################################################
#
# Copyright 2020 NVIDIA Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################

###############################################################################
#
# This liveSession sample demonstrates how to connect to a live session using
# the non-destructive live workflow.  A .live layer is used in the stage's session
# layer to contain the changes.  An Omniverse channel is used to broadcast users
# and merge notifications to all clients, and a session config (TOML) file is used
# to determine the "owner" of the session.
#
# * Initialize the Omniverse Resolver Plugin
# * Display existing live sessions for a stage
# * Connect to a live session
# * Set the edit target to the .live layer so changes replicate to other clients
# * Make xform changes to a mesh prim in the .live layer
# * Display the owner of the live session
# * Display the current connected users/peers in the session
# * Emit a GetUsers message to the session channel
# * Display the contents of the session config
# * Merge the changes from the .live session back to the root stage
# * Respond (by exiting) when another user merges session changes back to the root stage
#
###############################################################################

# Python built-in
import argparse
import asyncio
import inspect
import logging
import math
import os
import sys
import time
from contextlib import suppress
from aioconsole import ainput

# Python 3.8 - can't use PATH any longer
if hasattr(os, "add_dll_directory"):
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    dlldir = os.path.abspath(os.path.join(scriptdir, "../../_build/windows-x86_64/release")) 
    os.add_dll_directory(dlldir)

# USD imports
from pxr import Gf, Sdf, Usd, UsdGeom, UsdUtils, Ar

# Omni imports
import carb
import omni.client
import omni.usd_resolver
import omni.asset_validator.core
carb.get_framework().startup([])

# Internal imports
import log, xform_utils, get_char_util, tick_update, session_toml_util
import omni.kit.collaboration.channel_manager as cm
import omni.kit.layers.live_session_channel_manager as lscm
from concurrent.futures import ThreadPoolExecutor

connection_status_subscription = None
g_stage = None
g_stage_merged = False
g_logging_enabled = False
g_channel_manager = None
g_live_session_channel_manager = None
g_end_program = False
g_send_merge_start_message = False
g_send_merge_done_message = False
g_send_get_users_message = False
g_live_session_info = None

LOGGER = log.get_logger("PyLiveSession", level=logging.INFO)


def logCallback(threadName, component, level, message):
    global g_logging_enabled
    if g_logging_enabled:
        LOGGER.setLevel(logging.DEBUG)
        xform_utils.LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug(message)


def connectionStatusCallback(url, connectionStatus):
    if connectionStatus is omni.client.ConnectionStatus.CONNECT_ERROR:
        shutdownOmniverse()
        sys.exit("[ERROR] Failed connection, exiting.")


def startOmniverse():
    global g_logging_enabled
    omni.client.set_log_callback(logCallback)
    if g_logging_enabled:
        omni.client.set_log_level(omni.client.LogLevel.DEBUG)

    if not omni.client.initialize():
        sys.exit("[ERROR] Unable to initialize Omniverse client, exiting.")

    connection_status_subscription = omni.client.register_connection_status_callback(connectionStatusCallback)


def shutdownOmniverse():
    omni.client.live_wait_for_pending_updates()

    connection_status_subscription = None

    omni.client.shutdown()


def isValidOmniUrl(url):
    omniURL = omni.client.break_url(url)
    if omniURL.scheme == "omniverse" or omniURL.scheme == "omni":
        return True
    return False


def save_stage(comment=""):
    global g_stage

    # Set checkpoint message for saving Stage.
    omni.usd_resolver.set_checkpoint_message(comment)

    # Save the proper edit target (in the case that we're live editing)
    edit_target_layer = g_stage.GetEditTarget().GetLayer()
    edit_target_layer.Save()

    # Clear checkpoint message to ensure comment is not used in future file operations.
    omni.usd_resolver.set_checkpoint_message("")
    omni.client.live_process()


def findGeomMesh(existing_stage, search_mesh_str=""):
    global g_stage
    LOGGER.debug(existing_stage)

    g_stage = Usd.Stage.Open(existing_stage)

    if not g_stage:
        shutdownOmniverse()
        sys.exit("[ERROR] Unable to open stage" + existing_stage)

    #meshPrim = stage.GetPrimAtPath('/Root/box_%d' % boxNumber)
    for node in g_stage.Traverse():
        if search_mesh_str:
            if node.IsA(UsdGeom.Xformable):
                node_path = str(node.GetPath())
                if search_mesh_str in node_path:
                    return UsdGeom.Xformable(node)
        else:
            if node.IsA(UsdGeom.Mesh):
                    return UsdGeom.Xformable(node)

    shutdownOmniverse()
    sys.exit("[ERROR] No UsdGeomMesh found in stage:", existing_stage)
    return None

def getAllGeomMesh(existing_stage):
    global g_stage
    LOGGER.debug(existing_stage)

    g_stage = Usd.Stage.Open(existing_stage)

    if not g_stage:
        shutdownOmniverse()
        sys.exit("[ERROR] Unable to open stage" + existing_stage)

    #meshPrim = stage.GetPrimAtPath('/Root/box_%d' % boxNumber)
    primList = []
    for node in g_stage.Traverse():
        if node.IsA(UsdGeom.Xformable):
            node_path = str(node.GetPath())
            if node_path != '/World' and 'Light' not in node_path:
                primList.append(UsdGeom.Xformable(node))
    if primList !=[]:
        return primList
    else:
        shutdownOmniverse()
        sys.exit("[ERROR] No UsdGeomMesh found in stage:", existing_stage)
        return None


# Channel message callbacks
def merge_finished_cb(user_name, app_name):
    global g_stage_merged
    LOGGER.warning(f"Exiting since the merge was finished by {user_name} - {app_name}.")
    g_stage_merged = True

def merge_started_cb(user_name, app_name):
    LOGGER.warning(f"The merge was started by {user_name} - {app_name}. Do not make any changes")

def hello_cb(user_name, app_name):
    LOGGER.warning(f"{user_name} - {app_name} is in the live session")

def join_cb(user_name, app_name):
    LOGGER.warning(f"{user_name} - {app_name} has joined the live session")

def left_cb(user_name, app_name):
    LOGGER.warning(f"{user_name} - {app_name} has left the live session")



class LiveSessionInfo:
    """ Live Session Info class
    This class attempts to collect all of the logic around the live session file paths and URLs.
    It should be first instantiated with the stage URL (omniverse://server/folder/stage.usd), then
    get_session_folder_path_for_stage() can be used to list the available sessions.

    Once a session is selected, set_session_name() will finish the initialization of all of the paths
    and the other methods can be used.
    
    In the folder that contains the USD to be live-edited, there exists this folder structure:
    <.live> / < my_usd_file.live> / <session_name> / root.live

    get_session_folder_path_for_stage:  <stage_folder> / <.live> / < my_usd_file.live>
    get_live_session_folder_path:       <stage_folder> / <.live> / < my_usd_file.live> / <session_name>
    get_live_session_url:               <stage_folder> / <.live> / < my_usd_file.live> / <session_name> / root.live
    get_live_session_toml_url:          <stage_folder> / <.live> / < my_usd_file.live> / <session_name> / __session__.toml
    get_message_channel_url:            <stage_folder> / <.live> / < my_usd_file.live> / <session_name> / __session__.channel
    
    
    """
    def __init__(self, stage_url: str):
        self.OMNIVERSE_CHANNEL_FILE_NAME = "__session__.channel"
        self.LIVE_SUBFOLDER = "/.live"
        self.LIVE_SUBFOLDER_SUFFIX = ".live"
        self.DEFAULT_LIVE_FILE_NAME = "root.live"
        self.SESSION_TOML_FILE_NAME = "__session__.toml"


        self.stage_url = stage_url
        self.live_file_url = None
        self.channel_url = None
        self.toml_url = None
        self.session_name = None
        self.omni_url = omni.client.break_url(self.stage_url)
        # construct the folder that would contain sessions - <.live> / < my_usd_file.live> / <session_name> / root.live
        self.omni_session_folder_path = os.path.dirname(self.omni_url.path) + self.LIVE_SUBFOLDER + "/" + self.get_stage_file_name() + self.LIVE_SUBFOLDER_SUFFIX
        self.session_folder_string = omni.client.make_url(self.omni_url.scheme, self.omni_url.user, self.omni_url.host, self.omni_url.port, self.omni_session_folder_path)

    def get_session_folder_path_for_stage(self):
        return self.session_folder_string

    def set_session_name(self, session_name):
        self.session_name = session_name

    def get_live_session_folder_path(self):
        return self.omni_session_folder_path + "/" + self.session_name + self.LIVE_SUBFOLDER_SUFFIX

    def get_stage_file_name(self):
        # find the stage file's root name
        usd_file_root = os.path.splitext(os.path.basename(self.omni_url.path))[0]
        return usd_file_root

    def get_live_session_url(self):
        live_session_path = self.get_live_session_folder_path() + "/" + self.DEFAULT_LIVE_FILE_NAME
        live_session_url = omni.client.make_url(self.omni_url.scheme, self.omni_url.user, self.omni_url.host, self.omni_url.port, live_session_path)
        return live_session_url

    def get_live_session_toml_url(self):
        live_session_toml_path = self.get_live_session_folder_path() + "/" + self.SESSION_TOML_FILE_NAME
        live_session_url = omni.client.make_url(self.omni_url.scheme, self.omni_url.user, self.omni_url.host, self.omni_url.port, live_session_toml_path)
        return live_session_url

    def get_message_channel_url(self):
        live_session_channel_path = self.get_live_session_folder_path() + "/" + self.OMNIVERSE_CHANNEL_FILE_NAME
        live_session_url = omni.client.make_url(self.omni_url.scheme, self.omni_url.user, self.omni_url.host, self.omni_url.port, live_session_channel_path)
        return live_session_url


def list_session_users():
    global g_live_session_channel_manager
    # users are cm.PeerUser types
    users: set(cm.PeerUser)
    users = g_live_session_channel_manager.get_users()
    LOGGER.info("Listing session users: ")
    if len(users) == 0:
        LOGGER.info(" - No other users in session")
    for user in users:
        LOGGER.info(f" - {user.user_name}[{user.from_app}]")


async def join_session_channel():
    """ Join the live session channel
    OmniClientUrl
    """
    global g_channel_manager, g_live_session_channel_manager, g_live_session_info

    channel_file_url = g_live_session_info.get_message_channel_url()
    g_live_session_channel_manager = lscm.LiveSessionChannelManager(channel_file_url, None)
    await g_live_session_channel_manager.start_async(g_channel_manager)

    g_live_session_channel_manager.register_hello_callback(hello_cb)
    g_live_session_channel_manager.register_join_callback(join_cb)
    g_live_session_channel_manager.register_left_callback(left_cb)
    g_live_session_channel_manager.register_merge_start_callback(merge_started_cb)
    g_live_session_channel_manager.register_merge_finished_callback(merge_finished_cb)

async def get_list_of_sessions(stageUrl):
    global g_live_session_info

    g_live_session_info = LiveSessionInfo(stageUrl)
    
    # get the folder contains the sessions
    session_folder_path_for_stage = g_live_session_info.get_session_folder_path_for_stage()

    # list the available sessions, allow the user to pick one
    result, list_entries = await omni.client.list_async(session_folder_path_for_stage)
    if len(list_entries) >=1:
        session_idx = 0
        for entry in list_entries:
            session_name = os.path.splitext(entry.relative_path)[0]
            print('SESSION_ID', session_name)
            # print(f" [{session_idx}] {session_name}")
            session_idx += 1
        return True
    else:
        print('LIVE_INFO NO_SESSION_FOUND')
        return False

async def find_or_create_session(stageUrl):
    """Find or Create Session
    This function displays the existing session and allows the user to create a new session

    It will look for this folder structure (expecting stageUrl to contain 'myfile'):
        <.live> / < my_usd_file.live> / <session_name> / root.live
    If it doesn't find any sessions for the current USD file then it will present the option
    to create a new session.
    """
    global g_live_session_info

    g_live_session_info = LiveSessionInfo(stageUrl)
    
    # get the folder contains the sessions
    session_folder_path_for_stage = g_live_session_info.get_session_folder_path_for_stage()

    # list the available sessions, allow the user to pick one
    result, list_entries = await omni.client.list_async(session_folder_path_for_stage)
    print("Select a live session to join: ")
    session_idx = 0
    for entry in list_entries:
        session_name = os.path.splitext(entry.relative_path)[0]
        print(f" [{session_idx}] {session_name}")
        session_idx += 1
    print(f" [n] Create a new session")
    print(f" [q] Quit")

    session_idx_selected = input("Select a live session to join: ")
    live_stage = None
    live_layer = None
    session_name = None

    # the user picked a session, find the root.live file
    if session_idx_selected.isnumeric() and int(session_idx_selected) < session_idx:
        session_name = os.path.splitext(list_entries[int(session_idx_selected)].relative_path)[0] 
        g_live_session_info.set_session_name(session_name)

        # Check the session config file to verify the version matches the current supported version
        toml_url_str = g_live_session_info.get_live_session_toml_url()
        if not session_toml_util.is_version_compatible(toml_url_str):
            actual_version = session_toml_util.get_session_version(toml_url_str)
            print(f"The session config TOML file version is not compatible, exiting.")
            print(f"Expected: {session_toml_util.SUPPORTED_VERSION} Actual: {actual_version}")
            session_toml_util.log_session_toml(toml_url_str)
            g_end_program = True
            return False

        live_session_url = g_live_session_info.get_live_session_url()
        live_stage = Usd.Stage.Open(live_session_url)

    # the user wants a new session, get the new session name
    elif session_idx_selected == "n":
        session_name = input("Enter the new session name: ")
        if not session_name:
            LOGGER.error(f"Invalid session name - exiting")
            shutdownOmniverse()
            exit(1)

        g_live_session_info.set_session_name(session_name)
        
        # get current user name
        _, serverInfo = omni.client.get_server_info(g_live_session_info.stage_url)
        
        # create a new config session file
        OWNER_KEY = "user_name"
        STAGE_URL_KEY = "stage_url"
        MODE_KEY = "mode"
        SESSION_NAME_KEY = "name"
        
        session_config_dict = {
            OWNER_KEY : serverInfo.username,
            STAGE_URL_KEY : g_live_session_info.stage_url,
            MODE_KEY : "default",
            SESSION_NAME_KEY : session_name,
        }
        toml_url_str = g_live_session_info.get_live_session_toml_url()
        write_success = session_toml_util.write_session_toml(toml_url_str, session_config_dict)
        if not write_success:
            LOGGER.error(f"Unable to create session config file <{toml_url_str} - exiting")
            shutdownOmniverse()
            exit(1)

        # create a new root.live session file
        live_session_url = g_live_session_info.get_live_session_url()
        live_stage = Usd.Stage.CreateNew(live_session_url)
    else:
        print(f"Invalid selection, exiting")
        g_end_program = True
        return False


    # Join the message channel for the session
    await join_session_channel()

    # Get the live layer from the live stage
    live_layer = live_stage.GetRootLayer()
    LOGGER.info(f"Selected session URL: {live_session_url}")

    # construct the layers so that we can join the session
    g_stage.GetSessionLayer().subLayerPaths.append(live_layer.identifier)
    g_stage.SetEditTarget(Usd.EditTarget(live_layer))
    return True

async def join_existing_session(stageUrl, input_session_name):
    #todo fix this
    global g_live_session_info

    g_live_session_info = LiveSessionInfo(stageUrl)
    
    # get the folder contains the sessions
    session_folder_path_for_stage = g_live_session_info.get_session_folder_path_for_stage()

    # list the available sessions, allow the user to pick one
    result, list_entries = await omni.client.list_async(session_folder_path_for_stage)
    # print("Select a live session to join: ")
    
    selected_session = None
    for entry in list_entries:
        session_name = os.path.splitext(entry.relative_path)[0]
        if input_session_name == session_name:
            selected_session = entry

    # session_idx_selected = input("Select a live session to join: ")
    live_stage = None
    live_layer = None
    session_name = None

    # session matches available sessions, find the root.live file
    if selected_session !=None:
        session_name = os.path.splitext(selected_session.relative_path)[0] 
        g_live_session_info.set_session_name(session_name)

        # Check the session config file to verify the version matches the current supported version
        toml_url_str = g_live_session_info.get_live_session_toml_url()
        if not session_toml_util.is_version_compatible(toml_url_str):
            actual_version = session_toml_util.get_session_version(toml_url_str)
            print(f"The session config TOML file version is not compatible, exiting.")
            print(f"Expected: {session_toml_util.SUPPORTED_VERSION} Actual: {actual_version}")
            session_toml_util.log_session_toml(toml_url_str)
            g_end_program = True
            return False, None, None

        live_session_url = g_live_session_info.get_live_session_url()
        live_stage = Usd.Stage.Open(live_session_url)
    else:
        print(f"Invalid session, exiting")
        g_end_program = True
        return False, None, None


    # Join the message channel for the session
    await join_session_channel()

    # Get the live layer from the live stage
    live_layer = live_stage.GetRootLayer()
    LOGGER.info(f"Selected session URL: {live_session_url}")

    # construct the layers so that we can join the session
    g_stage.GetSessionLayer().subLayerPaths.append(live_layer.identifier)
    g_stage.SetEditTarget(Usd.EditTarget(live_layer))
    return True, live_stage, live_layer

def end_and_merge_session():
    """
    End and Merge Session - This function will check that it has ownership (from the TOML file), then merge live deltas to the root layer

    """
    global g_live_session_info, g_send_merge_start_message, g_send_merge_done_message, g_stage_merged

    # Do we have authority (check TOML)?
    # Gather the latest changes from the live stage
    # Send a MERGE_STARTED channel message
    # Create a checkpoint on the live layer (don't force if no changes)
    # Create a checkpoint on the root layer (don't force if no changes)
    # Merge the live deltas to the root layer
    # Save the root layer
    # Clear the live layer
    # Create a checkpoint on the root layer
    # Send a MERGE_FINISHED channel message

    # get current user name
    _, serverInfo = omni.client.get_server_info(g_live_session_info.stage_url)
    if not serverInfo:
        LOGGER.error("Invalid server info while retrieving username")
        return

    # get the session owner user name
    live_session_toml_url = g_live_session_info.get_live_session_toml_url()
    session_owner = session_toml_util.get_session_owner(live_session_toml_url)
    
    # stop the merge if they are not the same
    if session_owner != serverInfo.username:
        LOGGER.warning(f"The session owner is: {session_owner}, your user name is {serverInfo.username}, stopping the merge")
        return

    # gather the latest changes from the live stage
    omni.client.live_process()

    # send a merge started message
    g_send_merge_start_message = True
    while g_send_merge_start_message:
        time.sleep(0.1)
    
    # checkpoint the live layer
    omni.client.create_checkpoint(g_live_session_info.live_file_url, f"Pre-merge for {g_live_session_info.session_name} session", False)

    # checkpoint the root layer (don't force if there are no changes)
    omni.client.create_checkpoint(g_live_session_info.stage_url, f"Pre-merge for {g_live_session_info.session_name} session", False)

    # UsdUtilsFlattenLayerStack
    def resolve_asset_path(layer, asset_path):
        absolute_path = layer.ComputeAbsolutePath(asset_path)
        result, list_entry = omni.client.stat(absolute_path)
        if result != omni.client.Result.OK:
            LOGGER.info(f"[resolve_asset_path]:\n asset_path: {asset_path}")
            return asset_path

        # Make this path relative to current layer
        real_path = g_stage.GetRootLayer().realPath
        relative_path = omni.client.make_relative_url(real_path, absolute_path)

        #relative_path = relative_path.replace("\\", "/")
        LOGGER.info(f"[resolve_asset_path]:\n asset_path: {asset_path}\n absolute_path: {absolute_path}\n realPath: {real_path}\n relative path: {relative_path}")

        return relative_path

    flatten_stage = Usd.Stage.CreateInMemory()
    flatten_stage.GetRootLayer().subLayerPaths.append(g_stage.GetEditTarget().GetLayer().identifier)
    flatten_stage.GetRootLayer().subLayerPaths.append(g_stage.GetRootLayer().identifier)

    flattened_layer = UsdUtils.FlattenLayerStack(flatten_stage, resolve_asset_path)

    # merge the live layer changes to the root layer
    Sdf.CopySpec(flattened_layer, Sdf.Path.absoluteRootPath, g_stage.GetRootLayer(), Sdf.Path.absoluteRootPath)
    
    # change the edit target to the root layer
    live_edit_target = g_stage.GetEditTarget()
    g_stage.SetEditTarget(Usd.EditTarget(g_stage.GetRootLayer()))
    # save and checkpoint the root layer (but not this way)
    save_stage(f"After merging the live session: {g_live_session_info.session_name}")

    # clear the changes and flush the live layer to Nucleus
    live_edit_target.GetLayer().Clear()
    omni.client.live_process()

    # send a merge finished message
    g_send_merge_done_message = True
    while g_send_merge_done_message:
        time.sleep(0.1)

    g_stage_merged = True

def get_primwise_xform_reference_paths(prim):
    global g_stage
    omni.client.live_process()
    prim_references = prim.GetMetadata('references')

    if prim_references !=None:
        prependedItems = prim_references.prependedItems
        if prependedItems!=[]:
            asset_reference_path = prependedItems[0]
            prim_reference = asset_reference_path.assetPath

            child_path = prim.GetChildren()
            child = child_path[0]

            translate = child.GetAttribute('xformOp:translate').Get()
            rot_xyz = child.GetAttribute('xformOp:rotateXYZ').Get()
            scale = child.GetAttribute('xformOp:scale').Get()

            if translate==None:
                translate = (0,0,0)
            else:
                translate = tuple(translate)

            if rot_xyz==None:
                rot_xyz = (0,0,0)
            else:
                rot_xyz = tuple(rot_xyz)

            if scale==None:
                scale = (1,1,1)
            else:
                scale = tuple(scale)

            print(prim_reference, ' | ', translate, ' | ', rot_xyz, ' | ', scale)
    return None


def resolve_relative_usd_path(this_path, relative_reference_path):
    # Remove the filename from this_path
    # Remove the filename from this_path and replace backslashes with forward slashes
    base_directory = '/'.join(this_path.split('/')[:-1])

    # Combine the base_directory with the relative_reference_path and normalize the path
    full_absolute_path = os.path.normpath(os.path.join(base_directory, relative_reference_path))

    # Replace backslashes with forward slashes in the result
    full_absolute_path = full_absolute_path.replace('\\', '/')
    if 'omniverse://' not in full_absolute_path:
        full_absolute_path = full_absolute_path.replace('omniverse:/', 'omniverse://')
    return full_absolute_path

def get_all_prim_xform_reference_paths(stageUrl, primList):
    global g_stage
    omni.client.live_process()
    all_prim_str = ''
    for prim in primList:
        prim = prim.GetPrim()
        prim_references = prim.GetMetadata('references')

        if prim_references !=None:
            prependedItems = prim_references.prependedItems
            if prependedItems!=[]:
                asset_reference_path = prependedItems[0]
                prim_reference = asset_reference_path.assetPath
                if 'omniverse://' not in prim_reference:
                    # print(stageUrl, prim_reference)
                    prim_reference = resolve_relative_usd_path(stageUrl, prim_reference)

                child_path = prim.GetChildren()
                child = child_path[0]

                translate = child.GetAttribute('xformOp:translate').Get()
                rot_xyz = child.GetAttribute('xformOp:rotateXYZ').Get()
                # scale = child.GetAttribute('xformOp:scale').Get()

                if translate==None:
                    translate = (0,0,0)
                else:
                    translate = tuple(translate)

                if rot_xyz==None:
                    rot_xyz = (0,0,0)
                else:
                    rot_xyz = tuple(rot_xyz)

                prim_str = str(prim_reference)+ ' | '+ str(translate)+ ' | '+ str(rot_xyz) + '|'
                all_prim_str+=prim_str

                # if scale==None:
                #     scale = (1,1,1)
                # else:
                #     scale = tuple(scale)

    print(all_prim_str)
    return None

# def listener_quit_session():



class Periodic:
    def __init__(self, func, time):
        self.func = func
        self.time = time
        self.is_started = False
        self._task = None

    async def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        while True:
            await asyncio.sleep(self.time)
            self.func()

# async def ainput(prompt=None) -> str:
#     return await g_loop.run_in_executor(
#             g_thread_pool_executor, sys.stdin.readline)

def run_live_edit(prim, stageUrl):
    global g_stage, g_end_program, g_stage_merged, g_send_get_users_message
    angle = 0
    prim_path = prim.GetPath()
    # prompt_msg = inspect.cleandoc(
    #     """

    #     Enter an option:
    #      [t] transform the mesh
    #      [o] list session owner/admin
    #      [u] list session users
    #      [g] emit a GetUsers message (note there will be no response unless another app is connected to the same session)
    #      [c] log contents of the session config file
    #      [v] validate the current state of the session layer
    #      [m] merge changes and end the session
    #      [q] quit.
    #      """
    # )
    LOGGER.info(f"Begin Live Edit on {prim_path}")
    # LOGGER.info(f"{prompt_msg}")




    while True:

        option = get_char_util.getChar()
        # option = ainput()

        translate, rot_xyz, scale = xform_utils.get_srt_xform_from_prim(prim)

        
        # print(' | ', translate, ' | ', rot_xyz, ' | ', scale)


        if g_stage_merged:
            LOGGER.info(f"Exiting since a merge has completed")
            option = b'q'

        omni.client.live_process()
        if option == b't':
            angle = (angle + 15) % 360
            radians = angle * 3.1415926 / 180.0
            x = math.sin(radians) * 10.0
            y = math.cos(radians) * 10.0

            # Get srt transform from prim
            translate, rot_xyz, scale = xform_utils.get_srt_xform_from_prim(prim)

            # Translate and rotate
            translate += Gf.Vec3d(x, 0.0, y)
            rot_xyz = Gf.Vec3d(rot_xyz[0], angle, rot_xyz[2])

            LOGGER.info(f"Setting pos [{translate[0]:.2f}, {translate[1]:.2f}, {translate[2]:.2f}] and rot [{rot_xyz[0]:.2f}, {rot_xyz[1]:.2f}, {rot_xyz[2]:.2f}]")
            
            # Set srt transform
            srt_action = xform_utils.TransformPrimSRT(
                g_stage,
                prim.GetPath(),
                translation=translate,
                rotation_euler=rot_xyz,
                rotation_order=Gf.Vec3i(0, 1, 2),
                scale=scale,
            )
            srt_action.do()
            
            # Send live updates to the server and process live updates received from the server
            omni.client.live_process()

        ## \todo: Add renaming for parity with C++ sample

        elif option == b'o':
            session_owner = session_toml_util.get_session_owner(g_live_session_info.get_live_session_toml_url())
            LOGGER.info(f"Session Owner: {session_owner}")

        elif option == b'u':
            list_session_users()

        elif option == b'g':
            LOGGER.info("Blasting GET_USERS message to channel")
            # send a get_users message
            g_send_get_users_message = True
            while g_send_get_users_message:
                time.sleep(0.1)

        elif option == b'c':
            LOGGER.info("Retrieving session config file: ")
            live_session_toml_url = g_live_session_info.get_live_session_toml_url()
            session_toml_util.log_session_toml(live_session_toml_url)

        elif option == b'v':
            LOGGER.info("Validating current state")
            results = omni.asset_validator.core.ValidationEngine().validate(g_stage)
            if not results.issues():
                LOGGER.info("The stage is valid")
            for issue in results.issues(omni.asset_validator.core.IssuePredicates.IsFailure()):
                # str(issue) also works, but this is formatted for readability like it appears in Kit
                LOGGER.error(f"--------------------------------------------------------------------------------")
                if issue.rule:
                    LOGGER.error(f"Rule:  {issue.rule.__name__}")
                if issue.message:
                    LOGGER.error(f"Issue: {issue.message}")
                if issue.at:
                    LOGGER.error(f"At:    {issue.at.as_str()}")
                if issue.suggestion:
                    LOGGER.error(f"Fix:   {issue.suggestion.message}")

        elif option == b'm':
            LOGGER.info("Ending session and Merging live changes to root layer: ")
            end_and_merge_session()
    
        elif option == b'q' or option == chr(27).encode():
            LOGGER.info("Live edit complete")
            g_end_program = True
            break
        # else:
            # LOGGER.info(prompt_msg)


async def control_session():
    option = await ainput()
    option = option.strip()
    if option =='q':
        LOGGER.info("Live edit complete")
        g_end_program = True
    return option


async def main():
    global g_logging_enabled, g_end_program, g_channel_manager, g_send_merge_start_message, g_send_merge_done_message, g_send_get_users_message

    parser = argparse.ArgumentParser(description="Python Omniverse Client Sample",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-e", "--nucleus_url", action="store", required=True)
    parser.add_argument("-m", "--mesh", action="store", required=False, default="")
    parser.add_argument("--find_sessions", action = 'store_true', required=False, default=False)
    parser.add_argument("--session_name", action="store", required=False)
    parser.add_argument("--start_live", action = 'store_true', required=False, default=False)

    args = parser.parse_args()

    stage_url = args.nucleus_url
    g_logging_enabled = args.verbose
    search_mesh_str = args.mesh
    find_sessions = args.find_sessions
    input_session_name = args.session_name
    start_live = args.start_live

    startOmniverse()

    if stage_url and not isValidOmniUrl(stage_url):
        msg = ("This is not an Omniverse Nucleus URL: %s \n"
                "Correct Omniverse URL format is: omniverse://server_name/Path/To/Example/Folder/helloWorld_py.usd")
        LOGGER.error(msg, stage_url)
        shutdownOmniverse()
        exit(-1)

    # Setup a tick update for the async channel messages
    app_update = tick_update.TickUpdate()
    app_update.setup_tick(0.01666)
    app_update.start()


    # ::: SIMPLE CHECKING REQUESTS :::
    if find_sessions ==True:
        success = await get_list_of_sessions(stage_url)
        await app_update.stop()
        shutdownOmniverse()
        if not success:
            exit(1)
        else:
            exit(0)


    # selected_mesh = None

    LOGGER.debug("Stage url: %s", stage_url)
    # selected_mesh = findGeomMesh(stage_url, search_mesh_str) #dont comment this out yet or else run_live_edit will break
    mesh_list = getAllGeomMesh(stage_url)
    # print(mesh_list)

    # This was in the Kit extension, but putting it here because we don't need a 
    # ChannelManager outside of this context
    g_channel_manager = cm.ChannelManager(app_name = "Python OV Connect Live") 
    g_channel_manager.on_startup()

    if input_session_name and start_live ==True:
        success_join, live_stage, live_layer = await join_existing_session(stage_url, input_session_name)
        LOGGER.info(f"Join success: {success_join}")
        # print('live stage', live_stage)
        # print('live layer', live_layer)

        
        if success_join==True:
            # Run a CPU bound operation (or I/O bound in this case) in the ThreadPoolExecutor
            # This will make the coroutine block, but won't block
            # the event loop; other coroutines can run in meantime.

            srt_listener = Periodic(lambda: get_all_prim_xform_reference_paths(stage_url, mesh_list), 1)
            await srt_listener.start()
            while True:
                opt = await control_session()
                if opt =='q':
                    await srt_listener.stop()
                    g_live_session_channel_manager.stop()
                    await asyncio.sleep(0.1)
                    
                    g_channel_manager.on_shutdown()
                    g_channel_manager = None

                    await asyncio.sleep(0.1)

                    await app_update.stop()
                    
                    shutdownOmniverse()                    
                    break
            exit(0)
                # if opt == b'q':
                #     g_end_program = True
                #     break

            # input_listener = Periodic(lambda:input(), 1)
            # await input_listener.start()
            # uncomment the below to restore quit function
            # for prim in mesh_list:
            #     g_loop.run_in_executor(g_thread_pool_executor, run_live_edit, prim.GetPrim(), stage_url)
        else:
            if success_join==False:
                LOGGER.info("Failed to join session, exiting")
            exit(1)



    while not g_end_program:
        await asyncio.sleep(0.1)
        if g_send_merge_start_message:
            await g_live_session_channel_manager.broadcast_merge_started_message_async()
            g_send_merge_start_message = False
        if g_send_merge_done_message:
            await g_live_session_channel_manager.broadcast_merge_done_message_async()
            g_send_merge_done_message = False
        if g_send_get_users_message:
            await g_live_session_channel_manager.broadcast_get_users_message_async()
            g_send_get_users_message = False

    # g_live_session_channel_manager.stop()
    # await asyncio.sleep(0.1)
    
    # g_channel_manager.on_shutdown()
    # g_channel_manager = None

    # await asyncio.sleep(0.1)

    # await app_update.stop()
    
    # shutdownOmniverse()




if __name__ == "__main__":
    g_loop = asyncio.get_event_loop()
    g_thread_pool_executor = ThreadPoolExecutor() # Create a ThreadPool with !2 threads
    g_loop.run_until_complete(main())
