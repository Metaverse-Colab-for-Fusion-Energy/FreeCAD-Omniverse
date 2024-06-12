Pre-install: Setting up a local Nucleus server
============================================
The developed software relies on a connection with an Omniverse Nucleus server. Network clients requiring access to a given Nucleus server will require the server’s IP address and hostname to be accessible to it. Using Nucleus behind a firewall and port forwarding network traffic inbound is not supported. 

The FreeCAD connector can run on any Omniverse Nucleus setup. The most basic one can be downloaded using the Omniverse Individual license, which is free to use. The Omniverse Enterprise license requires a paid license subscription. There are some differences between Omniverse Individual and Omniverse Enterprise, however Omniverse Individual allows up to two users to work on the same project per entity. 
Further information regarding the differences between Omniverse Individual and Enterprise is available `here <https://docs.omniverse.nvidia.com/enterprise/latest/benefits.html>`_ [https://docs.omniverse.nvidia.com/enterprise/latest/benefits.html].

**Individual License**
Setting up a local Nucleus service using the Omniverse Individual license can be done through the steps in the following `link <https://docs.omniverse.nvidia.com/nucleus/latest/workstation/installation.html>`_: [https://docs.omniverse.nvidia.com/nucleus/latest/workstation/installation.html]
Once this is done, the user can access the Nucleus server using the newly created ``omniverse://localhost`` server. 

**Enterprise License**
To set up an enterprise Omniverse Nucleus server, an extended user license is required, information regarding this and installation steps of the Omniverse IT-managed launcher can be found `here <https://docs.omniverse.nvidia.com/launcher/latest/it-managed-launcher.html>`_ [https://docs.omniverse.nvidia.com/launcher/latest/it-managed-launcher.html]. 
