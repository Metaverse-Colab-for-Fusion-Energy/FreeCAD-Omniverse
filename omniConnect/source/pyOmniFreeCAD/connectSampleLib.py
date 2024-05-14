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

# Python built-in
import argparse
import logging
import math
import os
import sys
import time
import re

import open3d as o3d
import numpy as np

# Python 3.8 - can't use PATH any longer
if hasattr(os, "add_dll_directory"):
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    dlldir = os.path.abspath(os.path.join(scriptdir, "../../_build/windows-x86_64/release")) 
    os.add_dll_directory(dlldir)

# USD imports
from pxr import Gf, Kind, Sdf, Tf, Usd, UsdLux, UsdGeom, UsdPhysics, UsdShade, UsdUtils, Ar

# Omni imports
import omni.client
import omni.usd_resolver

# Internal imports
import log, xform_utils, get_char_util

g_connection_status_subscription = None
g_stage = None

LOGGER = log.get_logger("OmniConnectLib", level=logging.INFO)


def logCallback(threadName, component, level, message):
    if logging_enabled:
        LOGGER.setLevel(logging.DEBUG)
        xform_utils.LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug(message)


def connectionStatusCallback(url, connectionStatus):
    if connectionStatus is omni.client.ConnectionStatus.CONNECT_ERROR:
        sys.exit("[ERROR] Failed connection, exiting:" + connectionStatus)


def startOmniverse():
    omni.client.set_log_callback(logCallback)
    if logging_enabled:
        omni.client.set_log_level(omni.client.LogLevel.DEBUG)

    if not omni.client.initialize():
        sys.exit("[ERROR] Unable to initialize Omniverse client, exiting.")

    g_connection_status_subscription = omni.client.register_connection_status_callback(connectionStatusCallback)


def shutdownOmniverse():
    omni.client.live_wait_for_pending_updates()

    g_connection_status_subscription = None

    omni.client.shutdown()


def isValidOmniUrl(url):
    omniURL = omni.client.break_url(url)
    if omniURL.scheme == "omniverse" or omniURL.scheme == "omni":
        return True
    return False


# def createOmniverseModel(path, live_edit):
#     LOGGER.info("Creating Omniverse stage")
#     global g_stage

#     # Use a "".live" extension for live updating, otherwise use a ".usd" extension
#     stageUrl = path + "/helloworld_py" + (".live" if live_edit else ".usd")
#     omni.client.delete(stageUrl)

#     LOGGER.info("Creating stage: %s", stageUrl)

#     g_stage = Usd.Stage.CreateNew(stageUrl)
#     UsdGeom.SetStageUpAxis(g_stage, UsdGeom.Tokens.y)
#     UsdGeom.SetStageMetersPerUnit(g_stage, 0.01)

#     LOGGER.info("Created stage: %s", stageUrl)

#     default_prim_name = '/World'
#     UsdGeom.Xform.Define(g_stage, default_prim_name)
    
#     # Set the /World prim as the default prim
#     default_prim = g_stage.GetPrimAtPath(default_prim_name)
#     g_stage.SetDefaultPrim(default_prim)

#     # Set the default prim as an assembly to support using component references
#     Usd.ModelAPI(default_prim).SetKind(Kind.Tokens.assembly)

#     return stageUrl


def createOmniverseModel(stageUrl, live_edit):
    LOGGER.info("Creating Omniverse stage")
    global g_stage

    # Use a "".live" extension for live updating, otherwise use a ".usd" extension
    # stageUrl = path + "/helloworld_py" + (".live" if live_edit else ".usd")
    omni.client.delete(stageUrl)

    LOGGER.info("Creating stage: %s", stageUrl)

    g_stage = Usd.Stage.CreateNew(stageUrl)
    UsdGeom.SetStageUpAxis(g_stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(g_stage, 0.01)

    LOGGER.info("Created stage: %s", stageUrl)

    default_prim_name = '/World'
    UsdGeom.Xform.Define(g_stage, default_prim_name)
    
    # Set the /World prim as the default prim
    default_prim = g_stage.GetPrimAtPath(default_prim_name)
    g_stage.SetDefaultPrim(default_prim)

    # Set the default prim as an assembly to support using component references
    Usd.ModelAPI(default_prim).SetKind(Kind.Tokens.assembly)

    return stageUrl


def logConnectedUsername(stageUrl, output_log = True):
    _, serverInfo = omni.client.get_server_info(stageUrl)

    if serverInfo:
        if output_log:
            # print(dir(serverInfo))
            # print(serverInfo.version)
            LOGGER.info("Connected username: %s", serverInfo.username)
            print("Connected username: "+ serverInfo.username)
        return serverInfo.username
    else:
        return None

def getHostFromURL(stageUrl):
    urlObject = omni.client.break_url(stageUrl)
    host = urlObject.host
    # print(urlObject.path)
    # print(urlObject.port)
    # print(urlObject.scheme)
    # print(urlObject.query)
    # print(urlObject.user)
    return host



def createPhysicsScene():
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    sceneName = "/physicsScene"
    scenePrimPath = default_prim_path + sceneName

    # Create physics scene, note that we dont have to specify gravity
    # the default value is derived based on the scene up Axis and meters per unit.
    # Hence in this case the gravity would be (0.0, -981.0, 0.0) since we have
    # defined the Y up-axis and we are having a scene in centimeters.
    UsdPhysics.Scene.Define(g_stage, scenePrimPath)

def enablePhysics(prim, dynamic):
    if dynamic:
        # Make the cube a physics rigid body dynamic
        UsdPhysics.RigidBodyAPI.Apply(prim)

    # Add collision
    collision_api = UsdPhysics.CollisionAPI.Apply(prim)
    if not collision_api:
        LOGGER.error("Failed to apply UsdPhysics.CollisionAPI, check that the UsdPhysics plugin is located in the USD plugins folders")
        sys.exit(1)

    if prim.IsA(UsdGeom.Mesh):
        meshCollisionAPI = UsdPhysics.MeshCollisionAPI.Apply(prim)
        if dynamic:
            # set mesh approximation to convexHull for dynamic meshes
            meshCollisionAPI.CreateApproximationAttr().Set(UsdPhysics.Tokens.convexHull)
        else:
            # set mesh approximation to none - triangle mesh as is will be used
            meshCollisionAPI.CreateApproximationAttr().Set(UsdPhysics.Tokens.none)

# create dynamic cube
def createDynamicCube(stageUrl, size):
    global g_stage
    # Create the geometry under the default prim
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString
    cubeName = "cube"
    cubePrimPath = default_prim_path + "/" + Tf.MakeValidIdentifier(cubeName)
    cube = UsdGeom.Cube.Define(g_stage, cubePrimPath)

    if not cube:
        sys.exit("[ERROR] Failure to create cube")

    # Move it up
    cube.AddTranslateOp().Set(Gf.Vec3f(65.0, 300.0, 65.0))

    cube.GetSizeAttr().Set(size)
    cube.CreateExtentAttr(size * 0.5 * cube.GetExtentAttr().Get())

    enablePhysics(cube.GetPrim(), True)

    # Make the kind a component to support the assembly/component selection hierarchy
    Usd.ModelAPI(cube.GetPrim()).SetKind(Kind.Tokens.component)

    # Commit the changes to the USD
    save_stage(stageUrl, comment='Created a dynamic cube.')

# Create a simple quad in USD with normals and add a collider
def createQuad(stageUrl, size):
    global g_stage

    # Create the geometry under the default prim
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString
    quadName = "quad"
    quadPrimPath = default_prim_path + "/" + Tf.MakeValidIdentifier(quadName)
    mesh = UsdGeom.Mesh.Define(g_stage, quadPrimPath)

    if not mesh:
        sys.exit("[ERROR] Failure to create cube")

    # Add all of the vertices
    points = [
        Gf.Vec3f(-size, 0.0, -size),
        Gf.Vec3f(-size, 0.0, size),
        Gf.Vec3f(size, 0.0, size),
        Gf.Vec3f(size, 0.0, -size)]
    mesh.CreatePointsAttr(points)
    mesh.CreateExtentAttr(mesh.ComputeExtent(points))

    # Calculate indices for each triangle
    vecIndices = [ 0, 1, 2, 3 ]
    mesh.CreateFaceVertexIndicesAttr(vecIndices)

    # Add vertex normals
    meshNormals = [
        Gf.Vec3f(0.0, 1.0, 0.0),
        Gf.Vec3f(0.0, 1.0, 0.0),
        Gf.Vec3f(0.0, 1.0, 0.0),
        Gf.Vec3f(0.0, 1.0, 0.0) ]
    mesh.CreateNormalsAttr(meshNormals)

    # Add face vertex count
    faceVertexCounts = [ 4 ]
    mesh.CreateFaceVertexCountsAttr(faceVertexCounts)

    # set is as a static triangle mesh
    enablePhysics(mesh.GetPrim(), False)

    # Make the kind a component to support the assembly/component selection hierarchy
    Usd.ModelAPI(mesh.GetPrim()).SetKind(Kind.Tokens.component)

    # Commit the changes to the USD
    save_stage(stageUrl, comment='Created a Quad.')

h = 50.0
boxVertexIndices = [ 0,  1,  2,  1,  3,  2,
                     4,  5,  6,  4,  6,  7,
                     8,  9, 10,  8, 10, 11,
                    12, 13, 14, 12, 14, 15,
                    16, 17, 18, 16, 18, 19,
                    20, 21, 22, 20, 22, 23 ]
boxVertexCounts = [ 3 ] * 12
boxNormals = [ ( 0,  0, -1), ( 0,  0, -1), ( 0,  0, -1), ( 0,  0, -1),
               ( 0,  0,  1), ( 0,  0,  1), ( 0,  0,  1), ( 0,  0,  1),
               ( 0, -1,  0), ( 0, -1,  0), ( 0, -1,  0), ( 0, -1,  0),
               ( 1,  0,  0), ( 1,  0,  0), ( 1,  0,  0), ( 1,  0,  0),
               ( 0,  1,  0), ( 0,  1,  0), ( 0,  1,  0), ( 0,  1,  0),
               (-1,  0,  0), (-1,  0,  0), (-1,  0,  0), (-1,  0,  0)]
boxPoints = [ ( h, -h, -h), (-h, -h, -h), ( h,  h, -h), (-h,  h, -h),
              ( h,  h,  h), (-h,  h,  h), (-h, -h,  h), ( h, -h,  h),
              ( h, -h,  h), (-h, -h,  h), (-h, -h, -h), ( h, -h, -h),
              ( h,  h,  h), ( h, -h,  h), ( h, -h, -h), ( h,  h, -h),
              (-h,  h,  h), ( h,  h,  h), ( h,  h, -h), (-h,  h, -h),
              (-h, -h,  h), (-h,  h,  h), (-h,  h, -h), (-h, -h, -h) ]
boxUVs = [ (0, 0), (0, 1), (1, 1), (1, 0),
           (0, 0), (0, 1), (1, 1), (1, 0),
           (0, 0), (0, 1), (1, 1), (1, 0),
           (0, 0), (0, 1), (1, 1), (1, 0),
           (0, 0), (0, 1), (1, 1), (1, 0),
           (0, 0), (0, 1), (1, 1), (1, 0) ]

def save_stage(stageUrl, comment=""):
    global g_stage

    # Set checkpoint message for saving Stage.
    omni.usd_resolver.set_checkpoint_message(comment)

    # Save the proper edit target (in the case that we're live editing)
    edit_target_layer = g_stage.GetEditTarget().GetLayer()
    edit_target_layer.Save()

    # Clear checkpoint message to ensure comment is not used in future file operations.
    omni.usd_resolver.set_checkpoint_message("")
    omni.client.live_process()

def createEmptyMeshPrim(stageUrl, prim_name, token = None):
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    # Note that Tf.MakeValidIdentifier will change the hyphen to an underscore
    meshUrl = default_prim_path + "/" + Tf.MakeValidIdentifier(str(prim_name))

    meshPrim = UsdGeom.Mesh.Define(g_stage, meshUrl)

    if not meshPrim:
        sys.exit("[ERROR] Failure to create empty mesh.")

    if token ==None:
        checkpoint_descriptor = 'NO_TOKEN - Created empty mesh prim.'
    else:
        checkpoint_descriptor = str(token) + ' - Created empty mesh prim.'

    save_stage(stageUrl, comment=checkpoint_descriptor)
    return meshPrim

def createXformWithReference(stageUrl, prim_name, reference_path, token=None):
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    # Note that Tf.MakeValidIdentifier will change the hyphen to an underscore
    primPath = default_prim_path + "/" + Tf.MakeValidIdentifier(str(prim_name))
    XformPrim = UsdGeom.Xform.Define(g_stage, primPath)
    XformPrim.GetPrim().GetReferences().AddReference(str(reference_path))
    if token==None:
        save_stage(stageUrl, comment = 'NO_TOKEN - Added assembly object with reference to '+('/').join(reference_path.split('/')[-2:]))
    else:
        save_stage(stageUrl, comment = str(token) + ' - Added assembly object with reference to '+('/').join(reference_path.split('/')[-2:]))
    return XformPrim


def createBox(stageUrl, boxNumber=0):
    global g_stage 
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    # Note that Tf.MakeValidIdentifier will change the hyphen to an underscore
    boxUrl = default_prim_path + "/" + Tf.MakeValidIdentifier("box-%d" % boxNumber)

    boxPrim = UsdGeom.Mesh.Define(g_stage, boxUrl)

    boxPrim.CreateDisplayColorAttr([(0.463, 0.725, 0.0)])
    boxPrim.CreatePointsAttr(boxPoints)
    boxPrim.CreateNormalsAttr(boxNormals)
    boxPrim.CreateFaceVertexCountsAttr(boxVertexCounts)
    boxPrim.CreateFaceVertexIndicesAttr(boxVertexIndices)
    boxPrim.CreateExtentAttr(boxPrim.ComputeExtent(boxPoints))
    
    # USD 22.08 changed the primvar API
    if hasattr(boxPrim, "CreatePrimvar"):
        texCoords = boxPrim.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    else:
        primvarsAPI = UsdGeom.PrimvarsAPI(boxPrim)
        texCoords = primvarsAPI.CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
    texCoords.Set(boxUVs)
    texCoords.SetInterpolation("vertex")

    if not boxPrim:
        sys.exit("[ERROR] Failure to create box")

    # Set init transformation
    srt_action = xform_utils.TransformPrimSRT(
        g_stage,
        boxPrim.GetPath(),
        translation=Gf.Vec3d(0.0, 100.0, 0.0),
        rotation_euler=Gf.Vec3d(20.0, 0.0, 20.0),
    )
    srt_action.do()

    enablePhysics(boxPrim.GetPrim(), True)

    # Make the kind a component to support the assembly/component selection hierarchy
    Usd.ModelAPI(boxPrim.GetPrim()).SetKind(Kind.Tokens.component)

    save_stage(stageUrl, comment='Created a box.')

    return boxPrim

# def findGeomMesh(existing_stage, boxNumber=0):
#     global g_stage
#     LOGGER.debug(existing_stage)

#     g_stage = Usd.Stage.Open(existing_stage)

#     if not g_stage:
#         sys.exit("[ERROR] Unable to open stage" + existing_stage)

#     #meshPrim = stage.GetPrimAtPath('/World/box_%d' % boxNumber)
#     for node in g_stage.Traverse():
#         if node.IsA(UsdGeom.Mesh):
#             return UsdGeom.Mesh(node)

#     sys.exit("[ERROR] No UsdGeomMesh found in stage:", existing_stage)
#     return None

def findGeomMesh(existingStage, boxNumber=0):
    global g_stage
    # print(existingStage)
    geom_meshes = []
    mesh_paths = []
    g_stage = Usd.Stage.Open(existingStage)

    if not g_stage:
        sys.exit("[ERROR] Unable to open stage: " + existingStage)

    #meshPrim = stage.GetPrimAtPath('/Root/box_%d' % boxNumber)
    for node in g_stage.Traverse():
        # print(node.GetPath())
        # do not include ground mesh
        if node.IsA(UsdGeom.Mesh) and 'ground' not in str(node):
            geom_meshes.append(node)
            mesh_paths.append(node.GetPath())
    if geom_meshes:
        return geom_meshes, mesh_paths
    if not geom_meshes:    
        sys.exit("[ERROR] No UsdGeomMesh found in stage: "+ existingStage)
        return None, None

def uploadReferences(destination_path):
    # Materials
    uriPath = destination_path + "/Materials"
    omni.client.delete(uriPath)
    omni.client.copy("resources/Materials", uriPath)

    # Referenced Props
    uriPath = destination_path + "/Props"
    omni.client.delete(uriPath)
    omni.client.copy("resources/Props", uriPath)

def createMaterial(mesh, stageUrl):
    global g_stage
    # Create a Materials scope
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString
    UsdGeom.Scope.Define(g_stage, default_prim_path + "/Looks")
    
    # Create a material instance for this in USD
    materialName = "Fieldstone"
    newMat = UsdShade.Material.Define(g_stage, default_prim_path + "/Looks/Fieldstone")

    matPath = default_prim_path + "/Looks/Fieldstone"

    # MDL Shader
    # Create the MDL shader
    mdlShader = UsdShade.Shader.Define(g_stage, matPath+'/Fieldstone')
    mdlShader.CreateIdAttr("mdlMaterial")

    mdlShaderModule = "./Materials/Fieldstone.mdl"
    mdlShader.SetSourceAsset(mdlShaderModule, "mdl")
    mdlShader.GetPrim().CreateAttribute("info:mdl:sourceAsset:subIdentifier", Sdf.ValueTypeNames.Token, True).Set(materialName)

    mdlOutput = newMat.CreateSurfaceOutput("mdl")

    if hasattr(mdlShader, "ConnectableAPI"):
        mdlOutput.ConnectToSource(mdlShader.ConnectableAPI(), "out")
    else:
        mdlOutput.ConnectToSource(mdlShader, "out")

    # USD Preview Surface Shaders

    # Create the "USD Primvar reader for float2" shader
    primStShader = UsdShade.Shader.Define(g_stage, matPath+'/PrimST')
    primStShader.CreateIdAttr("UsdPrimvarReader_float2")
    primStShader.CreateOutput("result", Sdf.ValueTypeNames.Float2)
    primStShader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")

    # Create the "Diffuse Color Tex" shader
    diffuseColorShader = UsdShade.Shader.Define(g_stage, matPath+'/DiffuseColorTex')
    diffuseColorShader.CreateIdAttr("UsdUVTexture")
    texInput = diffuseColorShader.CreateInput("file", Sdf.ValueTypeNames.Asset)
    texInput.Set("./Materials/Fieldstone/Fieldstone_BaseColor.png")
    diffuseColorShader.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("auto")
    diffuseColorShader.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(primStShader.CreateOutput("result", Sdf.ValueTypeNames.Float2))
    diffuseColorShaderOutput = diffuseColorShader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    # Create the "Normal Tex" shader
    normalShader = UsdShade.Shader.Define(g_stage, matPath+'/NormalTex')
    normalShader.CreateIdAttr("UsdUVTexture")
    normalTexInput = normalShader.CreateInput("file", Sdf.ValueTypeNames.Asset)
    normalTexInput.Set("./Materials/Fieldstone/Fieldstone_N.png")
    normalShader.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")
    normalShader.CreateInput("scale", Sdf.ValueTypeNames.Float4).Set((2, 2, 2, 1))
    normalShader.CreateInput("bias", Sdf.ValueTypeNames.Float4).Set((-1, -1, -1, 0))
    normalShader.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(primStShader.CreateOutput("result", Sdf.ValueTypeNames.Float2))
    normalShaderOutput = normalShader.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

    # Create the USD Preview Surface shader
    usdPreviewSurfaceShader = UsdShade.Shader.Define(g_stage, matPath+'/PreviewSurface')
    usdPreviewSurfaceShader.CreateIdAttr("UsdPreviewSurface")
    diffuseColorInput = usdPreviewSurfaceShader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
    diffuseColorInput.ConnectToSource(diffuseColorShaderOutput)
    normalInput = usdPreviewSurfaceShader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)
    normalInput.ConnectToSource(normalShaderOutput)

    # Set the linkage between material and USD Preview surface shader
    usdPreviewSurfaceOutput = newMat.CreateSurfaceOutput()

    if hasattr(mdlShader, "ConnectableAPI"):
        usdPreviewSurfaceOutput.ConnectToSource(usdPreviewSurfaceShader.ConnectableAPI(), "surface")
    else:
        usdPreviewSurfaceOutput.ConnectToSource(usdPreviewSurfaceShader, "surface")

    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(newMat)

    save_stage(stageUrl, comment='Added material to box.')

# Remove a property from a prim
def remove_property(stage, prim_path: Sdf.Path, property_name: Sdf.Path):
    with Sdf.ChangeBlock():
        for layer in stage.GetLayerStack():
            prim_spec = layer.GetPrimAtPath(prim_path)
            if prim_spec:
                property_spec = layer.GetPropertyAtPath(prim_path.AppendProperty(property_name))
                if property_spec:
                    prim_spec.RemoveProperty(property_spec)


# Get the MDL shader prim from a Material prim
def get_shader_from_material(prim, get_prim=False):
    material = UsdShade.Material(prim)
    shader = material.ComputeSurfaceSource("mdl")[0] if material else None
    if shader and get_prim:
        return shader.GetPrim()
    return shader

# Create an input for an MDL shader in a material
def create_material_input(
    prim, name, value, vtype, def_value=None, min_value=None, max_value=None, display_name=None, display_group=None, color_space=None
):
    shader = get_shader_from_material(prim)
    if shader:
        existing_input = shader.GetInput(name)
        if existing_input and existing_input.GetTypeName() != vtype:
            remove_property(prim.GetStage(), shader.GetPrim().GetPath(), existing_input.GetFullName())

        surfaceInput = shader.CreateInput(name, vtype)
        surfaceInput.Set(value)
        attr = surfaceInput.GetAttr()

        if def_value is not None:
            attr.SetCustomDataByKey("default", def_value)
        if min_value is not None:
            attr.SetCustomDataByKey("range:min", min_value)
        if max_value is not None:
            attr.SetCustomDataByKey("range:max", max_value)
        if display_name is not None:
            attr.SetDisplayName(display_name)
        if display_group is not None:
            attr.SetDisplayGroup(display_group)
        if color_space is not None:
            attr.SetColorSpace(color_space)

        return attr

import typing 
def get_local_transform_xform(prim: Usd.Prim) -> typing.Tuple[Gf.Vec3d, Gf.Rotation, Gf.Vec3d]:
    """
    Get the local transformation of a prim using Xformable.
    See https://graphics.pixar.com/usd/release/api/class_usd_geom_xformable.html
    Args:
        prim: The prim to calculate the local transformation.
    Returns:
        A tuple of:
        - Translation vector.
        - Rotation quaternion, i.e. 3d vector plus angle.
        - Scale vector.
    """
    xform = UsdGeom.Xformable(prim)
    local_transformation: Gf.Matrix4d = xform.GetLocalTransformation()
    translation: Gf.Vec3d = local_transformation.ExtractTranslation()
    rotation: Gf.Rotation = local_transformation.ExtractRotation()
    scale: Gf.Vec3d = Gf.Vec3d(*(v.GetLength() for v in local_transformation.ExtractRotationMatrix()))
    return translation, rotation, scale

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


def get_all_xform_reference_paths(stageUrl, token=None):
    global g_stage

    g_stage = Usd.Stage.Open(stageUrl)

    nodelist = []
    asset_paths = []
    
    if not g_stage:
        sys.exit("[ERROR] Unable to open stage: " + stageUrl)
    for node in g_stage.Traverse():
        prim_references = node.GetMetadata('references')

        if prim_references !=None:
            prependedItems = prim_references.prependedItems
            if prependedItems!=[]:
                asset_reference_path = prependedItems[0]
                prim_reference = asset_reference_path.assetPath
                if 'omniverse://' not in prim_reference:
                    # print(stageUrl, prim_reference)
                    prim_reference = resolve_relative_usd_path(stageUrl, prim_reference)

                child_path = node.GetChildren()
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
    checkpoint_descriptor = ' - Sent Xform positions to FreeCAD'
    if token==None:
        token = 'NO_TOKEN'
    checkpoint_descriptor = str(token) + checkpoint_descriptor

    save_stage(stageUrl, comment=checkpoint_descriptor)
    return None

def set_xform_srt_from_reference_asset_path(assembly_stage_url, list_dict_prim_data, token=None):
    global g_stage
    g_stage = Usd.Stage.Open(assembly_stage_url)

    if not g_stage:
        sys.exit("[ERROR] Unable to open stage: " + assembly_stage_url)

    for node in g_stage.Traverse():
        prim_references = node.GetMetadata('references')

        if prim_references !=None:
            prependedItems = prim_references.prependedItems
            if prependedItems!=[]:
                asset_reference_path = prependedItems[0]
                prim_reference = asset_reference_path.assetPath
                if 'omniverse://' not in prim_reference:
                    prim_reference = resolve_relative_usd_path(assembly_stage_url, prim_reference)

                child_path = node.GetChildren()
                child_node = child_path[0]

                list_dict_entry = [list_dict_entry for list_dict_entry in list_dict_prim_data if list_dict_entry['ref-path']==prim_reference]
                print(list_dict_entry)
                if list_dict_entry != []:
                    list_dict_entry = list_dict_entry[0]
                    srt_action = xform_utils.TransformPrimSRT(
                            g_stage,
                            child_node.GetPath(),
                            translation=Gf.Vec3d(list_dict_entry['transform']),
                            rotation_euler=Gf.Vec3d(list_dict_entry['rot-xyz']),
                            rotation_order=Gf.Vec3i(0, 1, 2),
                        )
                    srt_action.do()
                    print(prim_reference, child_node.GetAttribute('xformOp:rotateXYZ').Get(), child_node.GetAttribute('xformOp:translate').Get())

    if token == None:
        checkpoint_descriptor = 'NO_TOKEN - Moved assembly geometry using FreeCAD.'
    else:
        checkpoint_descriptor = str(token) + ' - Moved assembly geometry using FreeCAD'
    save_stage(assembly_stage_url, comment=checkpoint_descriptor)
    return None



def do_xform_translation_rotation(prim, transform, rotate):
    prim.GetPrim()
    prim.GetAttribute('xformOp:translate').Set(transform)
    prim.GetAttribute('xformOp:rot-xyz').Set(rotate)
    return prim


# Create references and modify an OmniPBR material
def createReferenceAndPayload(stageUrl):
    # the referenced prop is in /Props/Coaster/Coaster_Hexagon.usd
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    # create a reference
    coaster_xform_prim = UsdGeom.Xform.Define(g_stage, default_prim_path + "/Coaster_Hexagon_Reference")
    coaster_xform_prim.GetPrim().GetReferences().AddReference("./Props/Coaster/Coaster_Hexagon.usda")
    enablePhysics(coaster_xform_prim.GetPrim(), True)
    UsdPhysics.RigidBodyAPI.Apply(coaster_xform_prim.GetPrim()).CreateAngularVelocityAttr(Gf.Vec3f(0, 1000, 0));

    # Set srt transform
    srt_action = xform_utils.TransformPrimSRT(
        g_stage,
        coaster_xform_prim.GetPath(),
        translation=Gf.Vec3d(200, 100, -200),
        rotation_euler=Gf.Vec3d(3, 0, 8),
        rotation_order=Gf.Vec3i(0, 1, 2),
        scale=Gf.Vec3d(10),
    )
    srt_action.do()

    # create a payload reference
    coaster_xform_prim = UsdGeom.Xform.Define(g_stage, default_prim_path + "/Coaster_Hexagon_Payload")
    coaster_xform_prim.GetPrim().GetPayloads().AddPayload("./Props/Coaster/Coaster_Hexagon.usda")
    enablePhysics(coaster_xform_prim.GetPrim(), True)
    UsdPhysics.RigidBodyAPI.Apply(coaster_xform_prim.GetPrim()).CreateAngularVelocityAttr(Gf.Vec3f(-1000, 0, 0));
    # Set srt transform
    srt_action = xform_utils.TransformPrimSRT(
        g_stage,
        coaster_xform_prim.GetPath(),
        translation=Gf.Vec3d(-200, 180, 200),
        rotation_euler=Gf.Vec3d(-4, 90, 8),
        rotation_order=Gf.Vec3i(0, 1, 2),
        scale=Gf.Vec3d(10),
    )
    srt_action.do()

    # Modify the payload's material in Coaster_Hexagon/Looks/M_Coaster_Hexagon
    material_prim_path = default_prim_path + "/Coaster_Hexagon_Payload/Looks/M_Coaster_Hexagon"
    material_prim = g_stage.GetPrimAtPath(material_prim_path)
    create_material_input(material_prim, "diffuse_tint", Gf.Vec3f(1, 0.1, 0), Sdf.ValueTypeNames.Color3f)

    # We could just save the stage here, but we'll learn about CoalescingDiagnosticDelegate first...
    #  We collect all of the warnings/errors from the USD warnings stream and only print if 
    #  there's a larger issue than the "crate file upgrade" WARNING that is emitted
    delegate = UsdUtils.CoalescingDiagnosticDelegate()
    save_stage(stageUrl, comment='Added Reference, Payload, and modified OmniPBR')
    stageSaveDiagnostics = delegate.TakeUncoalescedDiagnostics()
    if len(stageSaveDiagnostics) > 1:
        for diag in stageSaveDiagnostics:
            msg = f"In {diag.sourceFunction} at line {diag.sourceLineNumber} of {diag.sourceFileName} -- {diag.commentary}"
            if "ERROR" in diag.diagnosticCodeString:
                LOGGER.error(msg)
            else:
                LOGGER.warning(msg)

# Create a distant light in the scene.
def createDistantLight(stageUrl):
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString
    newLight = UsdLux.DistantLight.Define(g_stage, default_prim_path + "/DistantLight")
    angleValue = 0.53
    colorValue = Gf.Vec3f(1.0, 1.0, 0.745)
    intensityValue = 500.0

    newLight.CreateIntensityAttr(intensityValue)
    newLight.CreateAngleAttr(angleValue)
    newLight.CreateColorAttr(colorValue)

    # Also write the new UsdLux Schema attributes if using an old USD lib (pre 21.02)
    if newLight.GetPrim().HasAttribute("intensity"):
        newLight.GetPrim().CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float, custom=False).Set(intensityValue)
        newLight.GetPrim().CreateAttribute("inputs:angle", Sdf.ValueTypeNames.Float, custom=False).Set(angleValue)
        newLight.GetPrim().CreateAttribute("inputs:color", Sdf.ValueTypeNames.Color3f, custom=False).Set(colorValue)
    else: # or write the old UsdLux Schema attributes if using a new USD lib (post 21.02)
        newLight.GetPrim().CreateAttribute("intensity", Sdf.ValueTypeNames.Float, custom=False).Set(intensityValue)
        newLight.GetPrim().CreateAttribute("angle", Sdf.ValueTypeNames.Float, custom=False).Set(angleValue)
        newLight.GetPrim().CreateAttribute("color", Sdf.ValueTypeNames.Color3f, custom=False).Set(colorValue)

    # Set rotation on directlight
    xForm = newLight
    rotateOp = xForm.AddXformOp(UsdGeom.XformOp.TypeRotateXYZ, UsdGeom.XformOp.PrecisionDouble)
    rotateOp.Set(Gf.Vec3d(139, 44, 190))

    # Make the kind a component to support the assembly/component selection hierarchy
    Usd.ModelAPI(newLight.GetPrim()).SetKind(Kind.Tokens.component)

    save_stage(stageUrl, comment='Created a DistantLight.')


# Create a dome light in the scene.
def createDomeLight(stageUrl, texturePath):
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString
    newLight = UsdLux.DomeLight.Define(g_stage, default_prim_path + "/DomeLight")
    intensityValue = 900.0
    newLight.CreateIntensityAttr(intensityValue)
    newLight.CreateTextureFileAttr(texturePath)
    newLight.CreateTextureFormatAttr(UsdLux.Tokens.latlong) 

    # Also write the new UsdLux Schema attributes if using an old USD lib (pre 21.02)
    if newLight.GetPrim().HasAttribute("intensity"):
        newLight.GetPrim().CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float, custom=False).Set(intensityValue)
        newLight.GetPrim().CreateAttribute("inputs:texture:file", Sdf.ValueTypeNames.Asset, custom=False).Set(texturePath)
        newLight.GetPrim().CreateAttribute("inputs:texture:format", Sdf.ValueTypeNames.Token, custom=False).Set(UsdLux.Tokens.latlong)
    else:
        newLight.GetPrim().CreateAttribute("intensity", Sdf.ValueTypeNames.Float, custom=False).Set(intensityValue)
        newLight.GetPrim().CreateAttribute("texture:file", Sdf.ValueTypeNames.Asset, custom=False).Set(texturePath)
        newLight.GetPrim().CreateAttribute("texture:format", Sdf.ValueTypeNames.Token, custom=False).Set(UsdLux.Tokens.latlong)

    # Set rotation on domelight
    xForm = newLight
    rotateOp = xForm.AddXformOp(UsdGeom.XformOp.TypeRotateXYZ, UsdGeom.XformOp.PrecisionDouble)
    rotateOp.Set(Gf.Vec3d(270, 270, 0))

    # Make the kind a component to support the assembly/component selection hierarchy
    Usd.ModelAPI(newLight.GetPrim()).SetKind(Kind.Tokens.component)

    save_stage(stageUrl, comment='Created a DomeLight.')

def createNoBoundsCube(stageUrl, size):
    global g_stage
    default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

    cubeName = "no_bounds_cube"
    cubePrimPath = default_prim_path + "/" + Tf.MakeValidIdentifier(cubeName)
    LOGGER.info("Adding a cube with no extents to generate a validation failure: %s", cubePrimPath)

    cube = UsdGeom.Cube.Define(g_stage, cubePrimPath)
    cube.GetSizeAttr().Set(size)

    # Commit the changes to the USD
    save_stage(stageUrl, comment='Created a cube with no extents to fail asset.')


def createEmptyFolder(emptyFolderPath):
    # LOGGER.info("Creating new folder: %s", emptyFolderPath)
    result = omni.client.create_folder(emptyFolderPath)

    LOGGER.info("Create empty folder [ %s ]", result.name)
    return result.name


def run_live_edit(prim, stageUrl):
    global g_stage
    angle = 0
    omni.client.live_process()
    prim_path = prim.GetPath()
    LOGGER.info(f"Begin Live Edit on {prim_path} - \nEnter 't' to transform, 'm' to send a channel message, 'l' to leave the channel, or 'q' to quit.\n")

    # Message channel callback responsds to channel events
    def message_channel_callback(result: omni.client.Result, channel_event: omni.client.ChannelEvent, user_id: str, content: omni.client.Content):
        LOGGER.info(f"Channel event: {channel_event}")
        if channel_event == omni.client.ChannelEvent.MESSAGE:
            # Assume that this is an ASCII message from another client
            text_message = memoryview(content).tobytes().decode('ascii')
            LOGGER.info(f"Channel message received: {text_message}")

    # We aren't doing anything in particular when the channel messages are finished sending
    def on_send_message_cb(result):
        pass

    # Join a message channel to communicate text messages between clients
    join_request = omni.client.join_channel_with_callback(stageUrl+".__omni_channel__", message_channel_callback)

    while True:
        option = get_char_util.getChar()

        omni.client.live_process()
        if option == b't':
            angle = (angle + 15) % 360
            radians = angle * 3.1415926 / 180.0
            x = math.sin(radians) * 100.0
            y = math.cos(radians) * 100.0

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
            save_stage(stageUrl)

        elif option == b'm':
            if join_request:
                LOGGER.info("Enter a channel message: ")
                message = input()
                omni.client.send_message_with_callback(join_request.id, message.encode('ascii'), on_send_message_cb)
            else:
                LOGGER.info("The message channel is disconnected.")

        elif option == b'l':
            LOGGER.info("Leaving message channel")
            if join_request:
                join_request.stop()
                join_request = None

        elif option == b'q' or option == chr(27).encode():
            LOGGER.info("Live edit complete")
            break
        else:
            LOGGER.info("Enter 't' to transform, 'm' to send a channel message, 'l' to leave the channel, or 'q' to quit.")
def convertMeshPrimToO3dTriMesh(mesh_prim):
    mesh_prim_properties = mesh_prim.GetPropertyNames()

    mesh_points = np.array(mesh_prim.GetAttribute('points').Get())
    mesh_faceVertexIndices = np.array(mesh_prim.GetAttribute('faceVertexIndices').Get())

    # If cannot pickle mesh points, assume stored as a timeSample
    if mesh_points.size == 1:
        mesh_points = np.array(mesh_prim.GetAttribute('points').Get(0))
    # If cannot pickle mesh faceVertexIndices, assume stored as a timeSample
    if mesh_faceVertexIndices.size == 1:
        mesh_faceVertexIndices = np.array(mesh_prim.GetAttribute('faceVertexIndices').Get(0))
    # If it still doesn't work, 
    if mesh_points.size + mesh_faceVertexIndices.size <= 2:
        print('[ERROR] USD_INCOMPAT: Mesh points pickling failed.')
        print('[ERROR] USD_INCOMPAT: Mesh faceVertexIndices pickling failed.')
        return None
    else:
        mesh_triangleCount = int(len(mesh_faceVertexIndices)/3)

        mesh_faceVertexIndices_o3d = np.reshape(mesh_faceVertexIndices, (mesh_triangleCount, 3))
        
        triangle_mesh = o3d.geometry.TriangleMesh()
        triangle_mesh.vertices = o3d.utility.Vector3dVector(mesh_points)
        triangle_mesh.triangles = o3d.utility.Vector3iVector(mesh_faceVertexIndices_o3d)
        triangle_mesh = o3d.geometry.TriangleMesh.compute_vertex_normals(triangle_mesh)
        # triangle_mesh = triangle_mesh.compute_vertex_normals()

        return triangle_mesh

class o3dSTLMesh:
    def __init__(self, triangle_mesh):
        self.triangle_mesh = triangle_mesh
        self.vertices = np.asarray(triangle_mesh.vertices)
        self.triangles = np.asarray(triangle_mesh.triangles)
        self.triangle_mesh = self.triangle_mesh.compute_triangle_normals()
        self.vertex_normals = np.asarray(triangle_mesh.vertex_normals)

    def asUSDGeomMeshFormat(self):
        # defining facevertexindices to assign points to triangles
        usdFormFaceVertexIndicesCount = np.shape(self.triangles)[0]*np.shape(self.triangles)[1]
        usdFormFaceVertexIndices = np.reshape(self.triangles, (usdFormFaceVertexIndicesCount,))
        
        # defining fvc to make sure each face is a triangle 
        usdFormFaceVertexCounts = np.ones((np.shape(self.triangles)[0],))*3
        
        # defining vertex normals
        usdFormNormals = self.vertex_normals
        
        # defining vertex positions
        usdFormPoints = self.vertices
        
        # defining colour (WIP - ST, UV issues need to still consider)
        usdFormSurfaceTexture = np.ones((len(self.vertices),2))
        
        return usdFormFaceVertexIndices, usdFormFaceVertexCounts, usdFormNormals, usdFormPoints, usdFormSurfaceTexture

    def convertToUSDGeomMesh(self, input_prim, stageUrl, empty_prim = False):
        usdFormFaceVertexIndices, usdFormFaceVertexCounts, usdFormNormals, usdFormPoints, usdFormSurfaceTexture = self.asUSDGeomMeshFormat()
        if empty_prim==False:
            # Check to see if USD is set as a strange time-sampled animation (somehow USDs from Paraview do this!)
            input_prim_points = np.array(input_prim.GetAttribute('points').Get())
            input_prim_faceVertexIndices = np.array(input_prim.GetAttribute('faceVertexIndices').Get())
            # If it is a time-sampled animation then we just change the first frame (Paraview does this). If so the size will return as 1 instead of 0
            if input_prim_points.size + input_prim_faceVertexIndices.size <= 2:
                input_prim.GetAttribute('points').Set(time=0, value=usdFormPoints)
                input_prim.GetAttribute('faceVertexIndices').Set(time=0, value=usdFormFaceVertexIndices)
                input_prim.GetAttribute('faceVertexCounts').Set(time=0, value=usdFormFaceVertexCounts)
                input_prim.GetAttribute('normals').Set(time=0, value=usdFormNormals)
            # if it isnt a paraview outputted USD then we can just set attributes to the default time sample:
            else:
                input_prim.GetAttribute('points').Set(usdFormPoints)
                input_prim.GetAttribute('faceVertexIndices').Set(usdFormFaceVertexIndices)
                input_prim.GetAttribute('faceVertexCounts').Set(usdFormFaceVertexCounts)
                input_prim.GetAttribute('normals').Set(usdFormNormals)
        # else if the Mesh prim is empty 
        elif empty_prim ==True:
            input_prim.CreatePointsAttr(usdFormPoints)
            input_prim.CreateFaceVertexIndicesAttr(usdFormFaceVertexIndices)
            input_prim.CreateFaceVertexCountsAttr(usdFormFaceVertexCounts)
            input_prim.CreateNormalsAttr(usdFormNormals)
            input_prim.CreateExtentAttr(input_prim.ComputeExtent(usdFormPoints))
        
        return input_prim

def splitURLGetUSDFileName(usd_link):
    usd_link_split = usd_link.split('/')
    usd_filename = usd_link_split[-1]
    return usd_filename

def strip_suffixes(item):
    return re.sub(r'\.(usd|usda|usdc|usdz|stp|step)$', '', item, flags=re.IGNORECASE)


def parse_srt_list(raw_srt_list, step = 3):
    parse_list = [(stringval.replace('min', '-') if 'min' in stringval else stringval)for stringval in raw_srt_list ]
    float_list = [float(stringval) for stringval in parse_list]
    composite_list = [float_list[x:x+step] for x in range(0, len(float_list),step)]
    return composite_list

def parse_srt_and_ref_into_dict(transform_list, rotation_list, asset_reference_list):
    dict_list = []
    for transform, rotation, asset_reference in zip(transform_list, rotation_list, asset_reference_list):
        reference_dict = {
        "ref-path": str(asset_reference),
        "transform": transform,
        "rot-xyz": rotation[::-1]
        }
        dict_list.append(reference_dict)
    return dict_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Omniverse Client Sample",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    default_local_directory = './session_local'

    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-e", "--nucleus_url", action="store")
    parser.add_argument("-d", "--local_directory", action="store", default=default_local_directory)
    parser.add_argument("-f", "--fail", action='store_true', default=False)
    parser.add_argument("--pull", action="store_true", default=False)
    parser.add_argument("--push", action="store_true", default=False)
    parser.add_argument("--auth", action="store_true", default=False)
    parser.add_argument("--auth_project", action="store_true", default=False)
    parser.add_argument("--test", action="store_true", default=False)
    parser.add_argument("--move_assembly", action="store_true", default=False)
    parser.add_argument("--push_non_usd", action="store_true", default=False)
    parser.add_argument("--pull_non_usd", action="store_true", default=False)
    parser.add_argument("--logout", action="store_true", default=False)    
    parser.add_argument('--token', action="store", default=None)
    parser.add_argument('--host_name', action="store", default=None)
    parser.add_argument('--project_name', action="store", default=None)
    parser.add_argument('--asset_name', action="store", default=None)
    parser.add_argument("--local_non_usd_filename", action="store")
    parser.add_argument("--create_new_usd", action="store_true", default=False)
    parser.add_argument("--find_stp_and_usd_files", action="store_true", default=False)
    parser.add_argument("--find_existing_assemblies", action="store_true", default=False)
    parser.add_argument("--create_new_project", action="store_true", default=False)
    parser.add_argument("--create_new_asset", action="store_true", default=False)
    parser.add_argument("--assembly_name", action="store")
    parser.add_argument("--create_new_assembly", action="store_true", default=False)
    parser.add_argument("--get_prim_reference_xforms", action="store_true", default=False)
    parser.add_argument("--asset_usd_links", nargs ='+', action="store")
    parser.add_argument("--asset_stp_links", nargs ='+', action="store")
    parser.add_argument("--set_transform", nargs ='+', action="store")
    parser.add_argument("--set_rot_xyz", nargs ='+', action="store")
    parser.add_argument("--make_public", action="store_true", default=False)
    parser.add_argument("--custom_checkpoint", nargs ='+', action="store")
    parser.add_argument("--add_checkpoint_to_usd", action="store_true", default=False)
    parser.add_argument("--add_checkpoint_to_non_usd", action="store_true", default=False)

    args = parser.parse_args()

    get_prim_reference_xforms = args.get_prim_reference_xforms
    existing_stage = args.nucleus_url
    find_stp_and_usd_files = args.find_stp_and_usd_files
    find_existing_assemblies = args.find_existing_assemblies
    nucleus_url = args.nucleus_url
    logging_enabled = args.verbose
    insert_validation_failure = args.fail
    localSTLPath = args.local_directory
    auth_op = args.auth
    auth_project_op = args.auth_project
    pull_op = args.pull
    push_op = args.push
    test_op = args.test
    push_non_usd = args.push_non_usd
    pull_non_usd = args.pull_non_usd
    logout_op = args.logout
    token = args.token
    local_non_usd_filename = args.local_non_usd_filename
    create_new_usd = args.create_new_usd
    project_name = args.project_name
    host_name = args.host_name
    asset_name = args.asset_name
    create_new_project = args.create_new_project
    create_new_asset = args.create_new_asset
    assembly_name = args.assembly_name
    create_new_assembly = args.create_new_assembly
    asset_usd_links = args.asset_usd_links
    asset_stp_links = args.asset_stp_links
    set_transform = args.set_transform
    set_rot_xyz = args.set_rot_xyz
    set_rot_xyz = args.set_rot_xyz
    custom_checkpoint = args.custom_checkpoint
    make_public = args.make_public
    move_assembly = args.move_assembly
    add_checkpoint_to_usd = args.add_checkpoint_to_usd
    add_checkpoint_to_non_usd = args.add_checkpoint_to_non_usd

    # print(args)

    startOmniverse()
    if not os.path.exists(localSTLPath):
        # If it doesn't exist, create it
        os.makedirs(localSTLPath)

    # if not existing_stage:
        # LOGGER.info(f"[I] No USD stage specified")
        
### AUTHENTICATION FUNCTION
    if existing_stage and auth_op==True:
        LOGGER.info(f"Connecting to "+existing_stage)
        print("Connecting to "+existing_stage)
        username = logConnectedUsername(existing_stage, output_log=True)
        if not username:
            LOGGER.error(f"Cannot access file: {existing_stage}, authentication failed")
            print("[ERROR] NO_AUTH: Cannot authenticate with "+existing_stage)
            sys.exit("[ERROR] NO_AUTH: Cannot authenticate with "+existing_stage)
        acls = omni.client.get_acls(existing_stage)
        result = acls[0]
        acl_dict = list(acls[1])
        does_usd_exist = not str(omni.client.stat(existing_stage)[0]) == 'Result.ERROR_NOT_FOUND'
        if does_usd_exist == False:
            print('[ERROR] NOT_FOUND: Provided file link at: \n' +existing_stage+ '\n Cannot be found! Double check link or ensure nucleus server is added to portal.')
            sys.exit('[ERROR] NOT_FOUND: Provided file link at: \n' +existing_stage+ '\n Cannot be found! Double check link or ensure nucleus server is added to portal.')
        access = 0
        for entries in acl_dict:
            if entries.name == username:
                stringentry = str(entries)
                print('You have the following permissions to access this file:')
                print(stringentry)
                access+=1
        if access!=1:
            print('[ERROR] NO_PERMISSION: Cannot access file: '+ existing_stage)
            print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
            print('Try logging in under a different username: log out through the nucleus.')

    if existing_stage and auth_project_op==True:
        LOGGER.info(f"Connecting to "+existing_stage)
        print("Connecting to "+existing_stage)
        username = logConnectedUsername(existing_stage, output_log=True)
        if not username:
            LOGGER.error(f"Cannot access project directory: {existing_stage}, authentication failed")
            print("[ERROR] NO_AUTH: Cannot authenticate with "+existing_stage)
            sys.exit("[ERROR] NO_AUTH: Cannot authenticate with "+existing_stage)
        acls = omni.client.get_acls(existing_stage)
        result = acls[0]
        acl_dict = list(acls[1])
        does_usd_exist = not str(omni.client.stat(existing_stage)[0]) == 'Result.ERROR_NOT_FOUND'
        if does_usd_exist == False:
            print('[ERROR] NOT_FOUND: Provided project directory link at: \n' +existing_stage+ '\n Cannot be found! Double check link or ensure nucleus server is added to portal.')
            sys.exit('[ERROR] NOT_FOUND: Provided project directory link at: \n' +existing_stage+ '\n Cannot be found! Double check link or ensure nucleus server is added to portal.')
        access = 0
        for entries in acl_dict:
            if entries.name == username:
                stringentry = str(entries)
                print('You have the following permissions to access this file:')
                print(stringentry)
                access+=1
        if access!=1:
            print('[ERROR] NO_PERMISSION: Cannot access project directory file: '+ existing_stage)
            print('[ERROR] You do not have permissions to access this file! Contact your Nucleus administrator.')
            print('Try logging in under a different username: log out through the nucleus.')

    # if existing_stage and logout_op==True:
    #   LOGGER.info(f"Logging out of "+existing_stage)
    #   print(dir(omni.client.ConnectionStatus))


    #   omni.client.sign_out(existing_stage)

    #   print(omni.client.ConnectionStatus.CONNECTED==True)
    #   print(omni.client.ConnectionStatus.SIGNED_OUT==True)

        # print('readable file?', omni.client.ItemFlags.READABLE_FILE==True)
        # print('writeable file?', omni.client.ItemFlags.WRITEABLE_FILE==True)
        # print(omni.client.AccessFlags.READ==True)

### PULL FUNCTION - DEPRECATED IN V2
    elif existing_stage and pull_op==True:
        geom_mesh_prims, geom_mesh_paths = findGeomMesh(existing_stage)
        if not geom_mesh_prims:
            sys.exit("[ERROR] Unable to find mesh at " + existing_stage)
        geom_mesh_prims = geom_mesh_prims[0]
        geom_mesh_paths = geom_mesh_paths[0]

        if token is not None:
            local_fname = localSTLPath+'/'+str(token)+'download.stl'
            checkpoint_descriptor = str(token) + " - Pull to FreeCAD"
        else:
            local_fname = localSTLPath+'/download.stl'
            checkpoint_descriptor = "NO_TOKEN - Pull to FreeCAD"
        o3d_triangle_mesh = convertMeshPrimToO3dTriMesh(geom_mesh_prims)
        # o3d.visualization.draw_geometries([o3d_triangle_mesh])
        # print(local_fname)
        o3d.io.write_triangle_mesh(local_fname, o3d_triangle_mesh)
        save_stage(existing_stage, comment=checkpoint_descriptor)
        print(checkpoint_descriptor)

    elif add_checkpoint_to_usd and nucleus_url and custom_checkpoint:
        g_stage = Usd.Stage.Open(nucleus_url)
        if token:
            checkpoint_descriptor = str(token) + ' - ' + custom_checkpoint[0]
            save_stage(nucleus_url, comment=checkpoint_descriptor)
        else:
            checkpoint_descriptor = 'NO_TOKEN - ' + custom_checkpoint[0]
            save_stage(nucleus_url, comment=checkpoint_descriptor)

    elif add_checkpoint_to_non_usd and nucleus_url and custom_checkpoint:
        read_output_from_nucleus = omni.client.read_file(url=nucleus_url)
        read_output_content = read_output_from_nucleus[2]
        read_output_result = read_output_from_nucleus[0]

        read_output_bin = bytearray(read_output_content)
        if token is not None:
            checkpoint_descriptor = str(token) + ' - ' + custom_checkpoint[0]
        else:
            checkpoint_descriptor = 'NO_TOKEN - ' + custom_checkpoint[0]

        upload_result = omni.client.write_file(url=nucleus_url, 
            content=read_output_bin, 
            message=checkpoint_descriptor)

### PUSH FUNCTION
    elif existing_stage and push_op==True:
        geom_mesh_prims, geom_mesh_paths = findGeomMesh(existing_stage)
        if not geom_mesh_prims:
            sys.exit("[ERROR] Unable to find mesh at" + existing_stage)
        geom_mesh_prims = geom_mesh_prims[0]
        geom_mesh_paths = geom_mesh_paths[0]

        if token is not None:
            local_fname = localSTLPath+'/'+str(token)+'upload.stl'
            checkpoint_descriptor = str(token) + " - Push from FreeCAD"
        else:
            local_fname = localSTLPath+'/upload.stl'
            checkpoint_descriptor = "NO_TOKEN - Push from FreeCAD"
        new_mesh = o3d.io.read_triangle_mesh(local_fname)
        o3dToUSDConverter = o3dSTLMesh(new_mesh)
        geom_mesh_prims = o3dToUSDConverter.convertToUSDGeomMesh(geom_mesh_prims, existing_stage)
        save_stage(existing_stage, comment=checkpoint_descriptor)
        print(checkpoint_descriptor)

### FUNCTION TO CREATE NEW USD
    elif nucleus_url and create_new_usd==True:
        nucleus_url = createOmniverseModel(nucleus_url, live_edit=False)
        prim_name = 'testMesh'
        if token is not None:
            meshPrim = createEmptyMeshPrim(nucleus_url, prim_name, token = token)
        else:
            meshPrim = createEmptyMeshPrim(nucleus_url, prim_name)


        if token is not None:
            local_fname = localSTLPath+'/'+str(token)+'upload.stl'
            checkpoint_descriptor = str(token) + " - Created new asset on FreeCAD"
        else:
            local_fname = localSTLPath+'/upload.stl'
            checkpoint_descriptor = "NO_TOKEN - Created new asset on FreeCAD"

        new_mesh = o3d.io.read_triangle_mesh(local_fname)
        o3dToUSDConverter = o3dSTLMesh(new_mesh)
        meshPrim = o3dToUSDConverter.convertToUSDGeomMesh(meshPrim, nucleus_url, empty_prim = True)
        save_stage(nucleus_url, comment=checkpoint_descriptor)
        print(checkpoint_descriptor)

    elif nucleus_url and find_stp_and_usd_files==True and localSTLPath:
        folder_url = nucleus_url
        result, project_folder_contents = omni.client.list(url=folder_url)
        list_of_stp_urls = []
        list_of_usd_urls = []
        for folder_items in project_folder_contents:
            # TODO: ERROR HANDLING IF RESULT NOT OK!
            result, resolved_folder_info, resolved_absolute_url= omni.client.resolve(url=folder_items.relative_path, search_urls=[folder_url])
            if 'assembly' not in resolved_absolute_url:
                result, asset_folder_contents = omni.client.list(url=resolved_absolute_url)
                for asset_items in asset_folder_contents:
                    result, resolved_item_folder_info, resolved_item_folder_absolute_url= omni.client.resolve(url=asset_items.relative_path, search_urls=[resolved_absolute_url])
                    result, single_asset_folder_contents = omni.client.list(url=resolved_item_folder_absolute_url)
                    for stp_or_usd_file in single_asset_folder_contents:
                        result, resolved_item_usd_or_stp_folder_info, resolved_item_usd_or_stp_absolute_url= omni.client.resolve(url=stp_or_usd_file.relative_path, search_urls=[resolved_item_folder_absolute_url])
                        if ".stp" in resolved_item_usd_or_stp_absolute_url:
                            list_of_stp_urls.append(resolved_item_usd_or_stp_absolute_url)
                        if ".usd" in resolved_item_usd_or_stp_absolute_url:
                            list_of_usd_urls.append(resolved_item_usd_or_stp_absolute_url)
        if list_of_usd_urls == []:
            print('[ERROR] No USD files found!')
        if list_of_stp_urls ==[]:
            print('[ERROR] No STP files found!')
        local_file_path = localSTLPath
        local_step_list_txt = localSTLPath + '/stplist.txt'
        local_usd_list_txt = localSTLPath + '/usdlist.txt'
        with open(local_step_list_txt, 'w') as stp_file_txt:
            for stp_link in list_of_stp_urls:
                stp_file_txt.write(stp_link + '\n')
        with open(local_usd_list_txt, 'w') as usd_file_txt:
            for usd_link in list_of_usd_urls:
                usd_file_txt.write(usd_link + '\n')

### FUNC TO CREATE NEW PROJECT
    elif create_new_project ==True and project_name and host_name:
        base_url = new_url = omni.client.make_url(scheme = 'omniverse', host = host_name)
        app_name = 'FreeCAD'
        username = None
        username = logConnectedUsername(base_url, output_log = False)
        if make_public==False:
            newpath = '/Users/'+str(username)+'/'+str(app_name)+'/'+str(project_name)
        elif make_public==True:
            newpath = '/Projects/'+str(app_name)+'/'+str(project_name)
        new_url = omni.client.make_url(scheme = 'omniverse', host = host_name, path = newpath)
        print(new_url)
        result = createEmptyFolder(new_url)
        if result != 'OK':
            print('ERROR: '+ str(result)+' A project with that name already exists! Connect to the existing project or use a different project name.')

### FUNC TO CREATE NEW ASSET
    elif create_new_asset ==True and asset_name:
        if host_name and project_name:
            print('Creating new asset at host: '+ host_name+' project name: '+ project_name)
            base_url = omni.client.make_url(scheme = 'omniverse', host = host_name)
            app_name = 'FreeCAD'
            username = None
            # username = logConnectedUsername(base_url, output_log = False) # commented out because decided to stick to a static freeCAD directory
            if username:
                asset_path = '/Users/'+str(username)+'/'+str(app_name)+'/'+str(project_name)+'/assets/'+str(asset_name)
            else:
                asset_path = '/Projects/'+str(app_name)+'/'+str(project_name)+'/assets/'+str(asset_name)
            asset_path_url = omni.client.make_url(scheme = 'omniverse', host = host_name, path = asset_path)
        elif nucleus_url:
            print('Creating new asset at existing project: ', nucleus_url)
            asset_path_url = nucleus_url +'/assets/'+str(asset_name)
            asset_path_url_item = omni.client.break_url(url = asset_path_url)
            asset_path = str(asset_path_url_item.path)
            
        result = createEmptyFolder(asset_path_url)
        if result != 'OK':
            print('ERROR: Asset with this name already exists! '+str(result))
            exit()
        else:
            if host_name and project_name:
                full_usd_asset_url = asset_path+'/'+asset_name+'.usda'
                full_stp_asset_url = asset_path+'/'+asset_name+'.stp'

                full_usd_asset_url = omni.client.make_url(scheme = 'omniverse', host = host_name, path = full_usd_asset_url)
                full_stp_asset_url = omni.client.make_url(scheme = 'omniverse', host = host_name, path = full_stp_asset_url)
            elif nucleus_url:
                full_usd_asset_url = asset_path_url + '/'+asset_name+'.usda'
                full_stp_asset_url = asset_path_url + '/'+asset_name+'.stp'
            # Create new USD file
            full_usd_asset_url = createOmniverseModel(full_usd_asset_url, live_edit=False)
            if token is not None:
                meshPrim = createEmptyMeshPrim(full_usd_asset_url, asset_name, token = token)
            else:
                meshPrim = createEmptyMeshPrim(full_usd_asset_url, asset_name)

            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            starttime = time.time()
            if token is not None:
                local_fname = localSTLPath+'/'+str(token)+'upload.stl'
                checkpoint_descriptor = str(token) + " - Created new asset on FreeCAD"
            else:
                local_fname = localSTLPath+'/upload.stl'
                checkpoint_descriptor = "NO_TOKEN - Created new asset on FreeCAD"

            save_stage(full_usd_asset_url, comment=checkpoint_descriptor)
            print(checkpoint_descriptor)

            placeholder_bin_data = str.encode('EMPTY_FILE')
            upload_result = omni.client.write_file(url=full_stp_asset_url, content=placeholder_bin_data, message=checkpoint_descriptor)
            print('STP write to Nucleus: ' +str(upload_result))
            #DO NOT UNCOMMENT!!!
            print(full_stp_asset_url)
            print(full_usd_asset_url)

    elif create_new_assembly ==True and nucleus_url:
        #parse url and make new assembly folder if it doesn't exist
        project_url = nucleus_url
        assembly_folder_url = project_url + '/assembly'
        result = createEmptyFolder(assembly_folder_url)

        # if assembly name wasn't provided, assign a name to it and create a new omniverse stage
        if assembly_name:
            assembly_usd_url = assembly_folder_url+ '/'+ str(assembly_name)+'.usda'
        else:
            assembly_usd_url = assembly_folder_url+'/assembly.usda'
        assembly_usd_url = createOmniverseModel(assembly_usd_url, live_edit=False)
        if token is not None:
            save_stage(assembly_usd_url, comment = str(token) + ' - Created new assembly file.')
        else:
            save_stage(assembly_usd_url, comment = 'NO_TOKEN - Created new assembly file.')

        default_prim_path = g_stage.GetDefaultPrim().GetPath().pathString

        # searching for components to make assembly from
        if not asset_usd_links or not asset_stp_links: #if all of the project components are selected
            list_of_stp_urls = []
            list_of_usd_urls = []
            result, project_folder_contents = omni.client.list(url=project_url)#looking for the 'assets' folder
            for folder_items in project_folder_contents:
                # TODO: ERROR HANDLING IF RESULT NOT OK!
                result, resolved_folder_info, resolved_absolute_url= omni.client.resolve(url=folder_items.relative_path, search_urls=[folder_url]) #getting the full URL of the 'assets' folder
                if 'assembly' not in resolved_absolute_url:
                    result, asset_folder_contents = omni.client.list(url=resolved_absolute_url) #looking for a list of available assets in the assets folder
                    for asset_items in asset_folder_contents:
                        result, resolved_item_folder_info, resolved_item_folder_absolute_url= omni.client.resolve(url=asset_items.relative_path, search_urls=[resolved_absolute_url]) #getting full URL of component folder
                        result, single_asset_folder_contents = omni.client.list(url=resolved_item_folder_absolute_url) #listing the available USD and STP files in the folder
                        for stp_or_usd_file in single_asset_folder_contents:
                            result, resolved_item_usd_or_stp_folder_info, resolved_item_usd_or_stp_absolute_url= omni.client.resolve(url=stp_or_usd_file.relative_path, search_urls=[resolved_item_folder_absolute_url]) #getting the full URL of STP and USD files in the asset folder
                            if ".stp" in resolved_item_usd_or_stp_absolute_url:
                                list_of_stp_urls.append(resolved_item_usd_or_stp_absolute_url)
                            if ".usd" in resolved_item_usd_or_stp_absolute_url:
                                list_of_usd_urls.append(resolved_item_usd_or_stp_absolute_url)

        elif asset_usd_links and asset_stp_links: #alternate scenario where user wants to create assembly from specific items (read usd list or something)
            if len(asset_usd_links)==len(asset_stp_links):
                list_of_stp_urls = asset_stp_links
                list_of_usd_urls = asset_usd_links

        if list_of_stp_urls and list_of_usd_urls:
            prim_name_list = []
            prim_list = []
            for asset_usd_link in list_of_usd_urls:
                usd_filename=splitURLGetUSDFileName(asset_usd_link)
                prim_name = strip_suffixes(usd_filename)
                prim_name_list.append(strip_suffixes(usd_filename))
                if token is not None:
                    XformPrim = createXformWithReference(assembly_usd_url, prim_name, asset_usd_link, token = token)
                else:
                    XformPrim = createXformWithReference(assembly_usd_url, prim_name, asset_usd_link)
            # print(prim_name_list)
        print(assembly_usd_url)
    elif find_existing_assemblies==True and nucleus_url:
        #test opening existing assembly
        #find existing assemblies 
        project_url = nucleus_url

        result, project_folder_contents = omni.client.list(url=project_url)
        list_of_stp_urls = []
        list_of_usd_urls = []

        for folder_items in project_folder_contents:
            # TODO: ERROR HANDLING IF RESULT NOT OK!
            result, resolved_folder_info, resolved_absolute_url= omni.client.resolve(url=folder_items.relative_path, search_urls=[project_url])
            if 'assembly' in resolved_absolute_url:
                result, assembly_folder_contents = omni.client.list(url=resolved_absolute_url)
                for assembly_item_file in assembly_folder_contents:
                     result, resolved_item_info, resolved_item_absolute_url= omni.client.resolve(url=assembly_item_file.relative_path, search_urls=[resolved_absolute_url])
                     if ".usd" in resolved_item_absolute_url:
                        print(resolved_item_absolute_url)
                        list_of_usd_urls.append(resolved_item_absolute_url)

    elif get_prim_reference_xforms ==True and nucleus_url:
        #func to get location, attitude, and reference of items in a assembly USD
        assembly_url = nucleus_url
        if token is not None:
            get_all_xform_reference_paths(assembly_url, token = token)
        else:
            get_all_xform_reference_paths(assembly_url)
    elif move_assembly ==True and set_rot_xyz and set_transform and asset_usd_links:
        # func to set location and rotation for individual items in a given assembly USD
        # print(args)
        assembly_url = nucleus_url
        # print(set_rot_xyz)
        set_rot_xyz = parse_srt_list(set_rot_xyz)
        set_transform = parse_srt_list(set_transform)
        prim_data = parse_srt_and_ref_into_dict(set_transform, set_rot_xyz, asset_usd_links)
        if token is not None:
            set_xform_srt_from_reference_asset_path(assembly_url, prim_data, token = token)
        else:
            set_xform_srt_from_reference_asset_path(assembly_url, prim_data)
 
    elif nucleus_url and push_non_usd ==True and local_non_usd_filename:
        local_upload_file_path = local_non_usd_filename
        try:
            local_bin_f = open(local_upload_file_path, "rb")
            bin_data = local_bin_f.read()
            print('Read from '+ local_upload_file_path + ' OK')
            data = bytearray(bin_data)
        except FileNotFoundError:
            print('[ERROR] FileNotFoundError. Check file name.')
        if custom_checkpoint is not None:
            checkpoint_descriptor = str(token) + ' - ' + custom_checkpoint[0]
        else:
            if token is not None:
                checkpoint_descriptor = str(token) + " - Push from FreeCAD"
            else:
                checkpoint_descriptor = "NO_TOKEN - Push from FreeCAD"

        upload_result = omni.client.write_file(url=nucleus_url, 
            content=data, 
            message=checkpoint_descriptor)
        print('Write to Nucleus: ' +str(upload_result))
        local_bin_f.close()

    elif nucleus_url and pull_non_usd==True and local_non_usd_filename:
        local_download_file_path = local_non_usd_filename
        local_bin_f = open(local_download_file_path, 'wb')
        read_output_from_nucleus = omni.client.read_file(url=nucleus_url)
        read_output_content = read_output_from_nucleus[2]
        read_output_result = read_output_from_nucleus[0]
        print('Read from Nucleus: '+ str(read_output_result))
        read_output_bin = bytearray(read_output_content)
        if custom_checkpoint is not None:
            checkpoint_descriptor = str(token) + ' - ' + custom_checkpoint[0] 
        else:
            if token is not None:
                checkpoint_descriptor = str(token) + " - Pull to FreeCAD"
            else:
                checkpoint_descriptor = "NO_TOKEN - Pull to FreeCAD"

        try:
            local_bin_f.write(read_output_bin)
            print('Write to '+local_download_file_path+' OK')
            upload_result = omni.client.write_file(url=nucleus_url, 
                content=read_output_bin, 
                message=checkpoint_descriptor)

        except FileNotFoundError:
            print('[ERROR] FileNotFoundError. Check file name.')
            os.makedirs(os.path.dirname(local_download_file_path), exist_ok=True)
            local_bin_f.write(read_output_bin)
            print('Write to '+local_download_file_path+' OK')
        local_bin_f.close()

    shutdownOmniverse()