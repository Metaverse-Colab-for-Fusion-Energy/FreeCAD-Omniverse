import re
import os
import FreeCAD
import string
import random
__dir__ = os.path.dirname(__file__)



def RandomTokenGenerator():
    # func for generating token
    characters = string.ascii_letters + string.digits  # letters and numbers
    token = ''.join(random.choices(characters, k=5))
    return token

def strip_suffixes(item):
    # helper func to get base name of file
    return re.sub(r'\.(usd|usda|usdc|usdz|stp|step)$', '', item, flags=re.IGNORECASE)

def text_follows_rules(input_string):
    # func to make sure names of Nucleus files follow rules: must start with a letter - can contain letters, digits, or underscores, and cannot contain spaces
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    if re.match(pattern, input_string):
        return True
    else:
        return False

def no_restricted_strings_in_project_link(projectlink):
    # helper func to determine if projectname is OK
    assembly_in_link = 'assembly' in projectlink
    asset_in_link = 'asset' in projectlink
    return not(asset_in_link or assembly_in_link)

def clean_omniverse_path(path):
    # helper func to use regex to find any double slashes after the protocol part and replace with a single slash
    cleaned_path = re.sub(r'(?<!:)//+', '/', path)
    return cleaned_path

def parse_list_into_set_srt_command_arg(input_list):
    # helper func to parse S-R-T transform message from Omniverse into Freecad format transform
    fixed_list = []
    for group in input_list:
        for item in group:
            str_item = str(item)
            if item < 0:
                str_item = 'min'+ str_item[1:]
            fixed_list.append(str_item)

    input_list_str = str(fixed_list)
    no_brackets = input_list_str.replace("]", " ").replace("[", " ")
    no_parentheses = no_brackets.replace(")", " ").replace("(", " ")
    return no_parentheses

def find_corresponding_element(selected_item, first_list, second_list):
    for first_item, second_item in zip(first_list, second_list):
        if strip_suffixes(selected_item) == strip_suffixes(second_item):
            return second_item

def get_full_link_from_short(selected_item, first_list, second_list):
    for first_item, second_item in zip(first_list, second_list):
        if selected_item in second_item:
            return second_item

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

def GetComponentNameFromStplink(stplink):
    # function to get just the component name from the stplink. Used for UI boxes on freecad
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

def get_assembly_component_placement(type='base'):
    """
    Returns USD links and placements (position or rotation) of valid FreeCAD objects (that have been uploaded to omniverse) in the active document.
    """
    objects = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj, 'Nucleus_link_usd')]
    extract = (
        lambda o: tuple(o.Placement.Base) if type == 'base'
        else tuple(o.Placement.Rotation.getYawPitchRoll())
    )
    return [obj.Nucleus_link_usd for obj in objects], [extract(obj) for obj in objects]

def GetListOfAssemblyObjects(projectURL):
    doc = FreeCAD.ActiveDocument
    object_list = []
    object_label_list = []
    for obj in doc.Objects:
        if 'Nucleus_link_usd' in dir(obj):
            if clean_omniverse_path(projectURL) in str(obj.Nucleus_link_usd):
                object_list.append(obj)
                object_label_list.append(obj.Label)
    return object_list, object_label_list


def make_live_start_command(usdlink, session_name):
    # Returns the command needed to start live process
    doc = FreeCAD.ActiveDocument
    FreeCAD.setActiveDocument(doc.Name)
    currentProjectURL = GetCurrentProjectLinkNoPrint()
    error_code = None
    success=None

    # Batch file where the OV USD fetcher lives
    batchfilepath = GetFetcherScriptsDirectory().replace(" ","` ")
    batchfilename = GetBatchFileName(live=True)
    batchfilepath = os.path.join(batchfilepath, batchfilename)

    cmd = batchfilepath + ' --nucleus_url'+' '+ usdlink + ' --session_name ' + session_name + ' --start_live '
    return cmd