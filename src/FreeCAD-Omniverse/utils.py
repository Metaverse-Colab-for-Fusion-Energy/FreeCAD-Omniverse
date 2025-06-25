import re
import os
import FreeCADGui
__dir__ = os.path.dirname(__file__)

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

def RandomTokenGenerator():
    characters = string.ascii_letters + string.digits  # letters and numbers
    token = ''.join(random.choices(characters, k=5))
    return token

def strip_suffixes(item):
    return re.sub(r'\.(usd|usda|usdc|usdz|stp|step)$', '', item, flags=re.IGNORECASE)

def text_follows_rules(input_string):
    # Function to make sure names of Nucleus files follow rules
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

def clean_omniverse_path(path):
    # Use regex to find any double slashes after the protocol part and replace with a single slash
    cleaned_path = re.sub(r'(?<!:)//+', '/', path)
    return cleaned_path

def parse_list_into_set_srt_command_arg(input_list):
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