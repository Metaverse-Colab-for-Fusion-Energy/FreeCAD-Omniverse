System
====================
In this software, geometry is pushed to the Nucleus in a neutral .STP format, which preserves the information initially attached by FreeCAD and does not require importing of tessellated geometry into the FreeCAD workspace. Along with the STP file, the connector uploads a USD file, which is updated whenever a new version of its corresponding STP file is made. However, the connector imports only the stored STP file when pulling from Nucleus. The tessellation process is done only once for each version of the geometry: during the upload process of a STP file.
 
 .. figure:: figs/arch.png
   :class: with-border

USD and STP files are stored in a project folder, which contains single-component assets and assemblies. By default, projects are stored in:

``omniverse://HOST_NAME/Projects/FreeCAD/$PROJECT_NAME`` (public folder)

or if they are set as private projects:

``omniverse://HOST_NAME/Users/$USERNAME/FreeCAD/$PROJECT_NAME`` (private folder)

STP and USD assets are stored in:

``$PROJECT_FOLDER/assets/$ASSET_NAME/``

and assemblies stored as:

``$PROJECT_FOLDER/assembly/$ASSEMBLY_NAME.usda``

This is shown in the image below.

 .. figure:: figs/storage.png
   :class: with-border

Each asset’s USD and STP files are attached to a checkpoint message which can be viewed on any Omniverse application. After every upload, download, or assembly task triggered by the FreeCAD connector, a unique token is attached to the checkpoint message of the file. STP and USD files which are associated with the same task are identical and as such can be used as a way to track different versions of the CAD geometry. 
