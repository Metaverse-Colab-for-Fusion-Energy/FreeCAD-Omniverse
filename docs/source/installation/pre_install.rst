Pre-installation
============================================

Omniverse Launcher
-------------------
The Omniverse Launcher is a piece of software that is required as a first step for setting up a local Omniverse Nucleus server. The provision of the software is free (at the time of writing of this document in May 2024) and allows access to NVIDIA’s suite of Omniverse connected applications. 

1.	Navigate to the `Omniverse main page <https:\\nvidia.com/omniverse>`_ [nvidia.com/omniverse]. Under Software Development Kit (SDK), click Download now. 

 .. figure:: figs/launcher1.png
   :class: with-border

2.	A prompt to register for the download will appear. Enter the user’s details and select Submit to begin the download. 

 .. figure:: figs/launcher2.png
   :class: with-border
 
3.	A file (omniverse-launcher-win.exe) will begin to download. Execute the file and complete all the necessary steps in the installer. 
4.	The launcher will display after the installation is done. The user may need to log in to the launcher – this is done through an NVIDIA account that the user has to setup. 

Setting up a local Nucleus server
-----------------------------------
The developed software relies on a connection with an Omniverse Nucleus server. Network clients requiring access to a given Nucleus server will require the server’s IP address and hostname to be accessible to it. Using Nucleus behind a firewall and port forwarding network traffic inbound is not supported. 

The FreeCAD connector can run on any Omniverse Nucleus setup. The most basic one can be downloaded using the Omniverse Individual license, which is free to use. The Omniverse Enterprise license requires a paid license subscription. There are some differences between Omniverse Individual and Omniverse Enterprise, however Omniverse Individual allows up to two users to work on the same project per entity. 

Further information regarding the differences between Omniverse Individual and Enterprise is available in the `following link: <https://docs.omniverse.nvidia.com/enterprise/latest/benefits.html>`_ [https://docs.omniverse.nvidia.com/enterprise/latest/benefits.html].

**Individual License**
Setting up a local Nucleus service using the Omniverse Individual license can be done through the steps in the following `link: <https://docs.omniverse.nvidia.com/nucleus/latest/workstation/installation.html>`_: [https://docs.omniverse.nvidia.com/nucleus/latest/workstation/installation.html]

Once this is done, the user can access the Nucleus server using the newly created ``omniverse://localhost`` server. 

**Enterprise License**
To set up an enterprise Omniverse Nucleus server, an extended user license is required, information regarding this and installation steps of the Omniverse IT-managed launcher can be found `here: <https://docs.omniverse.nvidia.com/launcher/latest/it-managed-launcher.html>`_ [https://docs.omniverse.nvidia.com/launcher/latest/it-managed-launcher.html]. 