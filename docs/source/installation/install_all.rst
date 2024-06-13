Installation
============================================

Basic installation
--------------------

The basic installation is the recommended method of installation and should work with most systems. 

1.	Git clone the FreeCAD Connector repository to your FreeCAD \Mod directory. Typically, this is ``C:\Users\USER_NAME\AppData\Roaming\FreeCAD\Mod``. 

Command: 

``git clone https://github.com/Metaverse-Colab-for-Fusion-Energy/FreeCAD-Omniverse.git``

2. Navigate to the cloned repository’s directory and launch the installation by running ``install.bat``. This will fetch the dependencies required to run the software. 

Command:

``cd .\FreeCAD-Omniverse``
``.\install.bat``

3.	The installation is complete and the FreeCAD connector for Omniverse is ready for use. 

**Note**: if the ``AppData\Roaming\FreeCAD\Mod`` file directory does not exist, you must first initialise this folder. This happens if no FreeCAD addons have been previously installed. To do this, launch FreeCAD, and on the toolbar click ``Tools`` > ``Addon Manager``. If you are using the Addon Manager for the first time, a dialog box will open, warning you that the addons in the Addon manager are not officially part of FreeCAD. It also presents several options related to the Addon Manager's data usage. Adjust those options to your liking and press the ``OK``button to continue. The ``\Mod`` directory should now exist. 

Advanced installation
-----------------------
This subsection outlines the steps required to install the software manually, without using the automated script. The user will have to have Omniverse Launcher installed prior to carrying out this installation process.

1.	Git clone the FreeCAD Connector repository to your FreeCAD \Mod directory. Typically, this is ``C:\Users\USER_NAME\AppData\Roaming\FreeCAD\Mod``.

Command:

``git clone https://github.com/Metaverse-Colab-for-Fusion-Energy/FreeCAD-Omniverse.git``

2.	Open Omniverse Launcher. Under the Exchange tab, navigate to the Connect Sample page. This can be done using the search bar or under the Connectors tab on the left-hand side of the window. 

 .. figure:: figs/adv1.png
   :class: with-border

3.	Download Connect Sample version 202.0.0 using the Omniverse Launcher. The estimated file size is around 200MB. 

4.	Once downloaded, navigate to the Library tab. On the left-hand side of the page, select Connectors. The user can expect to find the newly downloaded Connect Sample connector visible on the page. 

 .. figure:: figs/adv2.png
   :class: with-border

5.	Click the three horizontal bars to the right of the Connect Sample listing. Click Settings.

 .. figure:: figs/adv3a.png
   :class: with-border

 .. figure:: figs/adv3b.png
   :class: with-border
 	 
6.	Clicking the folder icon to the right of the install path will direct the user to the directory in which the Connect Sample is stored. Alternatively, this is typically stored in ``C:/Users/USERNAME/AppData/Local/ov/pkg/connectsample-202.0.0``

7.	Copy the contents of the directory to the ``/OmniConnect`` folder of the ``FreeCAD-Omniverse`` repository directory, which was previously downloaded in step 1.

8.	Navigate to the ``/OmniConnect`` directory in the FreeCAD-Omniverse repository directory. Under ``/omniConnect/source/PyHelloWorld``, copy the entire ``\omni`` directory to ``/omniConnect/source/pyOmniFreeCAD``. The pyOmniFreeCAD folder should now contain all these files:

 .. figure:: figs/adv4.png
   :class: with-border

9.	Navigate to the /OmniConnect directory, and using a Powershell terminal run the command below to fetch the required NVIDIA dependencies:

Command:

``./repo.bat build --fetch-only``

10.	Still in the /OmniConnect directory, run the following command to fetch the remaining Python dependencies:

Command:

``./_build/target-deps/python/python.exe -m pip install open3d aioconsole``

11.	The installation is complete and the FreeCAD connector for Omniverse is ready for use. 

