How-to guide
================
Activating the FreeCAD-Omniverse Connector
------------------------------------------------
1.	Create or open a new document on FreeCAD. 
2.	Using the Workbench selector, select the Omniverse Connector Workbench.

 .. figure:: figs/activation1.png
   :class: with-border

3.	The Omniverse Connector is now active. The ribbon menu should show the Settings Panel and Clear Session buttons active with others greyed out. 

 .. figure:: figs/activation2.png
   :class: with-border

Establishing a connection with Nucleus
---------------------------------------
Establishing a connection with a component stored on the Nucleus is done through a project-based process. Users can create a new project or connect with an existing one. 

Creating a new project
_______________________

1.	Select the Settings Panel on the ribbon menu and click ‘Create New Project’.

 .. figure:: figs/createProject1.png
   :class: with-border

2.	This will prompt the user to input the Nucleus hostname and the new project name. An option to make the project private will appear in this prompt. If this is checked, the project will be saved in the Nucleus’s ``/Users/USERNAME/FreeCAD`` directory. If it is left unchecked (as the default option), the project will be saved in the Nucleus’s ``/Projects/FreeCAD`` directory.  

 .. figure:: figs/createProject2.png
   :class: with-border

3.	Click OK in the pop-up prompt. If the user has not logged in to the Nucleus server previously, a prompt to log in using the user’s credentials will appear on the user’s default web browser. 

 .. figure:: figs/createProject3.png
   :class: with-border

4.	If the connection is successful and the project has been successfully created, the Project Directory indicator on the Settings Panel will change into a green tick box. The connection with Nucleus has been established. 

 .. figure:: figs/createProject4.png
   :class: with-border

Connecting to an existing project
____________________________________

1.	Select the Settings Panel on the ribbon menu and click ‘Open existing project’.
2.	A pop-up window will appear prompting the user to input the existing project path. 

 .. figure:: figs/connectProject1.png
   :class: with-border

3.	If the user has not logged in to the Nucleus server previously, a prompt to log in using the user’s credentials will appear on the user’s default web browser. 
4.	If the connection is successful, the Project Directory indicator on the Settings Panel will change into a green tick box.  The connection with Nucleus has been established. 

 .. figure:: figs/createProject4.png
   :class: with-border

Disconnecting from an existing project
_______________________________________

1.	Select the Settings Panel on the ribbon menu and click ‘Disconnect from project’.
2.	The connection with the Nucleus server is now terminated. This will reflect in the Settings Panel showing no green tick marks.

 .. figure:: figs/createProject1.png
   :class: with-border


Interacting with Nucleus assets
--------------------------------------

Nucleus assets are geometry files that can be imported into FreeCAD for editing and sent back to Nucleus for storage. A user must be connected to a project prior to interacting with its assets. 

Creating an asset
_________________
1.	Using the Settings Panel, click ‘Create new asset in project’.

 .. figure:: figs/createAsset1.png
   :class: with-border
 
2.	A pop-up window will appear prompting the user to input a new name for the asset. 

 .. figure:: figs/createAsset2.png
   :class: with-border
 
3.	Clicking OK will show the Settings Panel with three green tick boxes. It will also indicate the name of the newly created asset. The user is now connected to the new asset. 

Uploading geometry to an asset
____________________________________

1.	The newly created asset is empty, and as such the user needs to upload new geometry to it. To do this, the user needs to create or import new geometry in FreeCAD. 
2.	Switch back to the Omniverse Connector Workbench and click the object to be uploaded in the FreeCAD Model view or the workspace. The object should be highlighted green.

 .. figure:: figs/uploadAsset1.png
   :class: with-border

3.	Click the ‘Push to Nucleus’ button on the ribbon menu to upload the geometry. 
4.	The geometry is now uploaded to the specified asset. The user can also check for this information in the FreeCAD object’s property tab.
 
 .. figure:: figs/uploadAsset2.png
   :class: with-border

Connecting to an existing asset
____________________________________

1.	Using the Settings Panel, click ‘Browse project assets’.
2.	A pop-up window will appear prompting the user to select an asset. Select the desired asset and click OK.

 .. figure:: figs/connectAsset1.png
   :class: with-border

3.	Clicking OK will show three green tick boxes in the Settings Panel along with the selected asset’s name.

 .. figure:: figs/connectAsset2.png
   :class: with-border

4.	The user is now connected to the existing asset.

Importing an existing asset
_____________________________

1.	Once an asset is connected, the associated asset geometry can be imported into the FreeCAD workspace if it is not an empty asset. Importing the asset is done using the ‘Pull from Nucleus’ button on the ribbon Menu.

 .. figure:: figs/importAsset1.png
   :class: with-border

2.	The asset should now be imported and appear in the FreeCAD workspace.

 .. figure:: figs/importAsset2.png
   :class: with-border

Assembly tools
-------------------

The push-pull assembly workflow provides a way for the FreeCAD user to use the various assembly functionalities of FreeCAD such as that found on the standard Part workbench, A2plus, Assembly3, or Assembly4, and propagate the component placement to a USD file on the Omniverse Nucleus. 

The main user interface for the assembly feature in the FreeCAD connector is the Assembly Tools panel. The panel contains 5 different buttons. 

 .. figure:: figs/assemblyPanel.png
   :class: with-border


The ‘Create new assembly’ button allows the user to create a USDA file on the Nucleus server which references the USD objects in the current FreeCAD workspace. Clicking this button opens a pop-up menu that prompts the user to input an assembly name and to select items in the workspace to include in the assembly. A new USDA file will be made in ``$PROJECT_FOLDER/assembly/``, containing only references to the USD component, that can be visualised on Omniverse in the same placement as that on FreeCAD. 

The ‘Import existing assembly’ button will open a pop-up menu that prompts the user to select an existing assembly from the current project folder. Upon selection, the entire assembly and its components will be imported into the FreeCAD workspace.  

Under these two buttons, status indicators are given, detailing the current project and assembly in use in the given session. If both current project and assembly elements are valid, the status will show the ‘Ready’ indicator, which allows users to access the ‘Upload assembly changes’, ‘Fetch assembly changes’, and ‘Live assembly mode features’ buttons. 

The remaining buttons allow the user to transfer positional information (translation and rotation) to and from the Nucleus server. 

The ‘Upload assembly changes’ button sends the cartesian coordinates and rotation of each component in the current FreeCAD assembly to the assembly USDA file stored on the Nucleus and alters the position of each referenced single component within the assembly USDA file. 

Meanwhile, the ‘Fetch new assembly changes’ button requests the coordinates and rotation of each element in the assembly USDA file stored in the Nucleus server and adjusts each component’s rotation and translation in the FreeCAD workspace. These two buttons allow for simple manipulation of position and angle of the components, integrated with the Omniverse environment. 

Creating a new assembly
_____________________________


**Prerequisites:**

-	The user must be connected to an existing Nucleus project.

-	All components intended to be included in the assembly must have already been uploaded to the Nucleus project.

**Steps:**

1.	Using the Assembly Tools button in the ribbon menu, click ‘Create new assembly from workspace objects’

 .. figure:: figs/createAssembly1.png
   :class: with-border
 
2.	A pop-up window will appear prompting the user to input a new name for the assembly and select geometry in the workspace to include in the new assembly. Note: only geometry that has been pushed to the Nucleus project will appear. 

 .. figure:: figs/createAssembly2.png
   :class: with-border

3.	The assembly panel will show three tickboxes and the status text will show ‘Ready’. This indicates positional and rotational changes in the geometry can be synced from FreeCAD and Omniverse.

 .. figure:: figs/createAssembly3.png
   :class: with-border

Importing an existing assembly
____________________________________

**Prerequisites:**

-	The user must be connected to an existing Nucleus project.

-	The Nucleus project must contain an existing assembly.

**Steps:**

1.	Select ‘Import existing assembly into workspace’ on the Assembly Panel.
2.	A pop-up window will appear prompting the user to select an existing assembly from a list. Only assemblies associated with the user’s project will appear from the list. Select an assembly file and click OK to confirm.

 .. figure:: figs/importAssembly1.png
   :class: with-border

3.	The assembly file will be imported into FreeCAD and will appear on the FreeCAD workspace. The assembly panel will show three tickboxes and the status text will show ‘Ready’. This indicates positional and rotational changes in the geometry can be synced from FreeCAD to Omniverse.

 .. figure:: figs/createAssembly3.png
   :class: with-border

Synchronising assembly changes
____________________________________

An assembly file created or imported using the FreeCAD connector can by synchronised with its counterpart hosted on a Nucleus server. The user has to ensure that the ‘Ready’ status indicator is shown in the Assembly Panel for this to be possible.

- To obtain updates in positional and rotational information of the components within the geometry, the user can use the Assembly Panel’s ‘Fetch New Assembly Changes’ button. Doing so will move the objects in the FreeCAD workspace to match that found in its Nucleus counterpart. 

- To update the positional and rotational information stored on Nucleus, the user can click the ‘Upload Assembly Changes’ button on the Assembly Panel. This button changes the position and rotation of the geometry stored in the selected assembly file stored on Nucleus to match that in the FreeCAD workspace.

Connecting with a live session
____________________________________

The ‘Live assembly mode’ button allows for live real-time communication between the FreeCAD workspace and Omniverse environment. 

**Prerequisites:**

1.	The user must be connected to an existing Nucleus project.
2.	The user must have an existing Nucleus assembly imported into the FreeCAD workspace.
3.	The Nucleus assembly has to have an existing live session. Creation of a new live session can be done using any Omniverse application. Steps to create an Omniverse live session can be found in the following `link <https://docs.omniverse.nvidia.com/extensions/latest/ext_core/ext_live/sessions.html>`_: [https://docs.omniverse.nvidia.com/extensions/latest/ext_core/ext_live/sessions.html]

**Steps:**

1.	Using the Assembly Panel, click on the ‘Live assembly mode’ button. This will open a pop-up window prompting the user to select an existing live session. 

 .. figure:: figs/live1.png
   :class: with-border

2.	On FreeCAD, the Live Assembly Mode button will show that it is active and toggled in blue. Movement of components in the live session on Omniverse will be streamed to the FreeCAD workspace in real-time.
3.	If the assembly USDA file is opened on Omniverse USD Composer and a user is logged into the same Live Session as the FreeCAD user, a small user icon will appear near the Live button of the USD Composer app. Also, a message will appear on the USD Composer notifying the user that another user has joined the session.
 
 .. figure:: figs/live2.png
   :class: with-border

 .. figure:: figs/live3.png
   :class: with-border

4.	Clicking the ‘Live assembly mode’ button again on FreeCAD deactivates Live mode, triggering the Omniverse Client to quit the Live Session and thus turning the button white in the process.
