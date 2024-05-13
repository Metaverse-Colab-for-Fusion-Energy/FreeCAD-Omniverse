# -*- coding: utf-8 -*-
# FreeCAD init script for the FreeCAD to Omniverse connector workbench
# This script is based on the FreeCAD workbench tutorial in https://github.com/felipe-m/tutorial_freecad_wb (c) Felipe Machado 2017
# The current script was developed by Raska Soemantoro github.com/raska-s 2023
#***************************************************************************
#*                                                                         *
#*   This file is part of the FreeCAD CAx development system.              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   FreeCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/


class OmniverseConnector (Workbench):
    """Basic 1 workbench object"""
    # this is the icon in XPM format 16x16 pixels 
    Icon = """
    /* XPM */
    static char * ovConnect_xpm[] = {
    "16 16 141 2",
    "   c None",
    ".  c #76B905",
    "+  c #77B906",
    "@  c #77B905",
    "#  c #76B804",
    "$  c #75B605",
    "%  c #81BC07",
    "&  c #76B906",
    "*  c #76B904",
    "=  c #76B900",
    "-  c #76B800",
    ";  c #74B600",
    ">  c #72B200",
    ",  c #6EAC00",
    "'  c #67A100",
    ")  c #73AA02",
    "!  c #78BA14",
    "~  c #75B700",
    "{  c #72B300",
    "]  c #70B000",
    "^  c #6DAC00",
    "/  c #68A300",
    "(  c #609700",
    "_  c #588A00",
    ":  c #73A900",
    "<  c #77BA07",
    "[  c #75B804",
    "}  c #73B400",
    "|  c #71B100",
    "1  c #6EAD00",
    "2  c #6CA900",
    "3  c #629900",
    "4  c #5A8D00",
    "5  c #528100",
    "6  c #4D7700",
    "7  c #7DBC00",
    "8  c #76B803",
    "9  c #74B500",
    "0  c #71B200",
    "a  c #6FAE00",
    "b  c #6DAA00",
    "c  c #6AA702",
    "d  c #68A302",
    "e  c #649C06",
    "f  c #5C8F03",
    "g  c #548300",
    "h  c #4C7800",
    "i  c #456C00",
    "j  c #72A900",
    "k  c #73B508",
    "l  c #70AF00",
    "m  c #6DAB00",
    "n  c #6AA600",
    "o  c #60940C",
    "p  c #517C0F",
    "q  c #477000",
    "r  c #416500",
    "s  c #689D00",
    "t  c #71B00C",
    "u  c #67A200",
    "v  c #4E7A04",
    "w  c #436805",
    "x  c #3C5F00",
    "y  c #6DA200",
    "z  c #6EAA0D",
    "A  c #518000",
    "B  c #4A7109",
    "C  c #3F6107",
    "D  c #395900",
    "E  c #76B100",
    "F  c #78BA0C",
    "G  c #6BA40F",
    "H  c #659F00",
    "I  c #456D00",
    "J  c #4B7407",
    "K  c #3B5B06",
    "L  c #5D8900",
    "M  c #71B000",
    "N  c #77B80E",
    "O  c #659D0D",
    "P  c #619800",
    "Q  c #578800",
    "R  c #476F00",
    "S  c #4C7603",
    "T  c #4E7505",
    "U  c #6FAA00",
    "V  c #74B506",
    "W  c #5F940E",
    "X  c #5D9100",
    "Y  c #538200",
    "Z  c #497100",
    "`  c #4D7800",
    " . c #548110",
    ".. c #629109",
    "+. c #6BA400",
    "@. c #6CAA00",
    "#. c #72B205",
    "$. c #598B01",
    "%. c #548400",
    "&. c #4A7300",
    "*. c #4E7A00",
    "=. c #528000",
    "-. c #578703",
    ";. c #5C8F07",
    ">. c #609507",
    ",. c #639903",
    "'. c #639B00",
    "). c #669F00",
    "!. c #68A400",
    "~. c #6BA800",
    "{. c #6EAD03",
    "]. c #538309",
    "^. c #558500",
    "/. c #4B7500",
    "(. c #4E7B00",
    "_. c #5B8E00",
    ":. c #5D9200",
    "<. c #609600",
    "[. c #629A00",
    "}. c #659E00",
    "|. c #6DAA0B",
    "1. c #527C12",
    "2. c #4F7C00",
    "3. c #5C9100",
    "4. c #5F9400",
    "5. c #649C00",
    "6. c #66A000",
    "7. c #6BA612",
    "8. c #4D7807",
    "9. c #528002",
    "0. c #598C00",
    "a. c #5B8F00",
    "b. c #5E9300",
    "c. c #639B03",
    "d. c #659F09",
    "e. c #568606",
    "f. c #588907",
    "g. c #5C8D0F",
    "h. c #5E900F",
    "i. c #5E9207",
    "j. c #5F9603",
    "          . + @ # $ %           ",
    "      & * = - ; > , ' )         ",
    "    ! = = ~ { ] ^ / ( _ : <     ",
    "  [ = ~ } | 1 2 / 3 4 5 6 7     ",
    "  8 9 0 a b c d e f g h i j @   ",
    "k { l m n o         p q r s = & ",
    "t , 2 u v             w x y - & ",
    "z n u A B             C D E ; F ",
    "G H ( I J             K L M { N ",
    "O P Q R S             T U , | V ",
    "W X Y Z `  .        ..+.n @.a #.",
    "  $.%.&.*.=.-.;.>.,.'.).!.~.{.  ",
    "  ].^./.(.5 Q _.:.<.[.}.u n |.  ",
    "    1.=.2.Y Q 4 3.4.P 5.6.7.    ",
    "      8.9.Y Q 0.a.b.( c.d.      ",
    "          e.f.g.h.i.j.          "};

    """

    MenuText = "Omniverse Connector"
    ToolTip = "FreeCAD connector to NVIDIA Omniverse"

    def Initialize(self) :
        "This function is executed when FreeCAD starts"
        from PySide import QtCore, QtGui
        # python file where the commands are:
        import omniConnectorGui
        # list of commands, only one (it is in the imported omniConnectorGui):
        cmdlist = [ "OVconnect_pull_from_nucleus", "OVconnect_push_to_nucleus", "OVconnect_URLPanel", "OVconnect_assembly_tools"]
        self.appendToolbar(
            str(QtCore.QT_TRANSLATE_NOOP("OmniverseConnector", "OmniverseConnector")), cmdlist)
        self.appendMenu(
            str(QtCore.QT_TRANSLATE_NOOP("OmniverseConnector", "OmniverseConnector")), cmdlist)

        

        current_project_link = omniConnectorGui.GetCurrentProjectLinkNoPrint()
        last_project_link = omniConnectorGui.GetLastProjectLinkNoPrint()
        omniConnectorGui.ClearLocalDirectory()
        FreeCAD.assembly_usd_link=None
        FreeCAD.is_connected_to_nucleus_project = False

        if current_project_link != None:
            omniConnectorGui.SaveLastProjectLinkAsTextFile(current_project_link)
        elif last_project_link!=None:
            omniConnectorGui.SaveLastProjectLinkAsTextFile(last_project_link)

        Log ('Loading Omniverse Connector module... done\n')

    def GetClassName(self):
        return "Gui::PythonWorkbench"

# The workbench is added
Gui.addWorkbench(OmniverseConnector())

