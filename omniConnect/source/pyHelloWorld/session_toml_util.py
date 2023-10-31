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
import logging
import os
import stat
import tempfile

import log
import omni.client

LOGGER = log.get_logger("PySessionTomlUtil", level=logging.INFO)
OWNER_KEY = "user_name"
VERSION_KEY = "version"
SUPPORTED_VERSION = "1.0"

def log_session_toml(live_session_toml_url):
    result, versionStr, content =  omni.client.read_file(live_session_toml_url)
    if result == omni.client.Result.OK:
        file_contents = memoryview(content).tobytes().decode('utf-8')
        for line in file_contents.splitlines():
            LOGGER.info(line)

def get_session_value(live_session_toml_url, session_key):
    result, versionStr, content =  omni.client.read_file(live_session_toml_url)
    if result == omni.client.Result.OK:
        file_contents = memoryview(content).tobytes().decode('utf-8')
        for line in file_contents.splitlines():
            if session_key in line:
                return_data_w_quotes = line.rstrip().split("=")[1].lstrip()
                return_data = return_data_w_quotes.replace("\"", "")
                return return_data
    return ""


def get_session_owner(live_session_toml_url):
    return get_session_value(live_session_toml_url, OWNER_KEY)

def get_session_version(live_session_toml_url):
    return get_session_value(live_session_toml_url, VERSION_KEY)

def is_version_compatible(live_session_toml_url):
    """
    Check that a version is compatible [major.minor]
        If major is the same, return true, else return false
        This works under the assumption that future minor versions will still work
    """
    config_version = get_session_value(live_session_toml_url, VERSION_KEY)
    if not config_version:
        return False

    major_minor = config_version.split(".")
    supported_major_minor = SUPPORTED_VERSION.split(".")
    if len(major_minor) > 1 and  major_minor[0] == supported_major_minor[0]:
        return True
    else:
        return False
        

def write_session_toml(live_session_toml_url, session_config_dict):
    """ 
    This function writes the session toml given a dictionary of key/value pairs
        OWNER_KEY = "user_name"
        STAGE_URL_KEY = "stage_url"
        MODE_KEY = "mode" (possible modes - "default" = "root_authoring", "auto_authoring", "project_authoring")
        SESSION_NAME_KEY = "session_name"
        The VERSION_KEY is automatically updated/written
    """
    session_config_dict[VERSION_KEY] = SUPPORTED_VERSION

    toml_str = ""
    for key in session_config_dict:
        toml_str += f"{key} = \"{session_config_dict[key]}\"\n"

    result = omni.client.write_file(live_session_toml_url, bytes(toml_str, 'utf-8'))
    return result == omni.client.Result.OK
