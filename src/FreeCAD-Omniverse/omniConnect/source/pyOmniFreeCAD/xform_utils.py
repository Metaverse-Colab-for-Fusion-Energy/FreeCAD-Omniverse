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
from typing import Union, Optional, List, Tuple

from pxr import Gf, Sdf, Tf, Usd, UsdGeom

import log


LOGGER = log.get_logger("PyXformUtils", level=logging.INFO)


class TransformPrimSRT:
    """Transform primitive.
    This class is ported and modified from omni.command.usd.TransformPrimSRTCommand

    Args:
        prim_path (str): Prim path.
        translation (Gf.Vec3d): New local translation.
        rotation_euler (Gf.Vec3d): New local rotation euler angles (in degree).
        rotation_order (Gf.Vec3i): New rotation order (e.g. (0, 1, 2) means XYZ). Set to None to stay the same.
        scale (Gf.Vec3d): New scale.
        time_code (Usd.TimeCode): TimeCode to set transform to.
        had_transform_at_key (bool): If there's key for transform.
    """

    def __init__(self,
            stage: Usd.Stage,
            prim_path: str,
            translation: Optional[Gf.Vec3d] = Gf.Vec3d(),
            rotation_euler: Optional[Gf.Vec3d] = Gf.Vec3d(),
            rotation_order: Optional[Gf.Vec3i] = Gf.Vec3i(0, 1, 2),
            scale: Optional[Gf.Vec3d] = Gf.Vec3d(1),
            time_code: Optional[Usd.TimeCode] = Usd.TimeCode.Default(),
            had_transform_at_key: Optional[bool] = False,
        ):
        LOGGER.debug("init Transform SRT Command")
        self._stage = stage
        self._prim_path = prim_path
        self._translation = translation
        self._rotation_euler = rotation_euler
        self._rotation_order = rotation_order
        self._scale = scale
        self._time_code = time_code
        self._had_transform_at_key = had_transform_at_key

        if not self.prim:
            error_msg = "Invalid prim path to transform"
            LOGGER.error(error_msg)
            # TODO Handle error type
            raise Exception(error_msg)

    @property
    def prim(self):
        """Prim to transform"""
        return self._stage.GetPrimAtPath(self._prim_path)

    @property
    def xform(self):
        """UsdGeom.Xformable of self.prim"""
        return UsdGeom.Xformable(self.prim)

    @property
    def xform_ops(self):
        """Ordered UsdGeom.XformOp from self.xform"""
        return self.xform.GetOrderedXformOps()

    def _get_rotation_order_type(self,
            rotation_order: Optional[Gf.Vec3i] = None,
            default: Optional[UsdGeom.XformOp.Type] = UsdGeom.XformOp.TypeInvalid
        ) -> UsdGeom.XformOp.Type:
        if rotation_order is None:
            rotation_order = self._rotation_order

        rotation_order_to_type_map = {
            Gf.Vec3i(0, 1, 2): UsdGeom.XformOp.TypeRotateXYZ,
            Gf.Vec3i(0, 2, 1): UsdGeom.XformOp.TypeRotateXZY,
            Gf.Vec3i(1, 0, 2): UsdGeom.XformOp.TypeRotateYXZ,
            Gf.Vec3i(1, 2, 0): UsdGeom.XformOp.TypeRotateYZX,
            Gf.Vec3i(2, 0, 1): UsdGeom.XformOp.TypeRotateZXY,
            Gf.Vec3i(2, 1, 0): UsdGeom.XformOp.TypeRotateZYX,
        }
        return rotation_order_to_type_map.get(rotation_order, default)

    def _set_value_with_precision(self,
            xform_op: UsdGeom.XformOp,
            value: List[Union[int, float]],
            time_code: Optional[Usd.TimeCode] = None,
            skip_equal_set_for_timesample: Optional[bool] = False,
        ) -> bool:

        if time_code is None:
            time_code = self._time_code

        # No timesample on xform_op, force using default time
        if not self._xform_op_is_time_sampled(xform_op) and not time_code.IsDefault():
            LOGGER.warning("%s is not time sampled. Force using default time.", xform_op)
            time_code = Usd.TimeCode.Default()

        old_value = xform_op.Get(time_code)

        if old_value is None:
            LOGGER.debug("Setting %s to %s at time %s", xform_op.GetName(), value, time_code)
            return xform_op.Set(value, time_code)

        # If xform_op exists already, make sure the value type is consistent
        value_type = type(old_value)
        if skip_equal_set_for_timesample:
            if not time_code.IsDefault() and not self._has_time_sample(xform_op, time_code):
                if Gf.IsClose(value_type(value), old_value, 1e-6):
                    LOGGER.warning("xform op value not set - %s, %s", xform_op.GetName(), value)
                    return False

        LOGGER.debug("Setting %s to %s at time %s", xform_op.GetName(), value, time_code)
        return xform_op.Set(value_type(value), time_code)

    @staticmethod
    def _xform_op_is_time_sampled(xform_op: UsdGeom.XformOp) -> bool:
        return xform_op.GetNumTimeSamples() > 0

    @staticmethod
    def _has_time_sample(xform_op, time_code) -> bool:
        if time_code.IsDefault():
            return False
        time_samples = xform_op.GetTimeSamples()
        time_code_value = time_code.GetValue()
        if round(time_code_value) != time_code_value:
            LOGGER.warning(
                "Error: try to identify attribute %s has time sample on a non round key %s",
                str(xform_op.GetName()), time_code_value
            )
            return False
        if time_code_value in time_samples:
            return True
        return False

    @staticmethod
    def construct_transform_matrix_from_srt(
            translation: Gf.Vec3d,
            rotation_euler: Gf.Vec3d,
            rotation_order: Gf.Vec3i,
            scale: Gf.Vec3d
        ) -> Gf.Matrix4d:
        """Convert srt args to transform matrix4"""

        trans_mtx = Gf.Matrix4d()
        rot_mtx = Gf.Matrix4d()
        scale_mtx = Gf.Matrix4d()

        trans_mtx.SetTranslate(translation)

        axes = [Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis()]
        rotation = (
            Gf.Rotation(axes[rotation_order[0]], rotation_euler[rotation_order[0]])
            * Gf.Rotation(axes[rotation_order[1]], rotation_euler[rotation_order[1]])
            * Gf.Rotation(axes[rotation_order[2]], rotation_euler[rotation_order[2]])
        )
        rot_mtx.SetRotate(rotation)
        scale_mtx.SetScale(scale)
        return scale_mtx * rot_mtx * trans_mtx

    def get_transform_matrix(self) -> Gf.Matrix4d:
        """Get the transform matrix4"""
        return self.construct_transform_matrix_from_srt(
            self._translation, self._rotation_euler, self._rotation_order, self._scale
        )

    def _xform_is_time_sampled(self) -> bool:
        for xform_op in self.xform_ops:
            if self._xform_op_is_time_sampled(xform_op):
                return True
        return False

    def set_transform(self, skip_equal_set_for_timesample: Optional[bool] = False) -> None:
        """Setting xform as matrix4 or srt"""
        for xform_op in self.xform_ops:
            if xform_op.GetOpType() == UsdGeom.XformOp.TypeTransform:
                self._set_transform_as_matrix(xform_op, skip_equal_set_for_timesample)
                return

        # If xform op isn't a UsdGeom.XformOp.TypeTransform (matrix4), do srt
        self._set_transform_as_srt(skip_equal_set_for_timesample)

    def _set_transform_as_matrix(self,
            xform_op: UsdGeom.XformOp,
            skip_equal_set_for_timesample: Optional[bool] = False,
        ) -> bool:
        """Set transform matrix4 on the xform_op - UsdGeom.XformOp.TypeTransform"""
        with Sdf.ChangeBlock():
            matrix = self.get_transform_matrix()

            # Only the new matrix4 xform is valid. Ignore other xform ops to avoid double xform.
            self.xform.SetXformOpOrder([xform_op], self.xform.GetResetXformStack())

            return self._set_value_with_precision(
                xform_op, matrix, skip_equal_set_for_timesample=skip_equal_set_for_timesample)

    def _find_or_add(self,
            xform_op_type: UsdGeom.XformOp.Type,
            create_if_not_exist: bool,
            precision: UsdGeom.XformOp.Precision,
            op_suffix: str=""
        ) -> Tuple[UsdGeom.XformOp, UsdGeom.XformOp.Precision]:
        for xform_op in self.xform_ops:
            if xform_op.GetOpType() == xform_op_type:
                if (not op_suffix and str(xform_op.GetOpName()).count(":") == 1) or \
                    (op_suffix and str(xform_op.GetOpName()).endswith(op_suffix)):
                    # Found and return
                    return xform_op

        # Not found, and no create
        if not create_if_not_exist:
            return None

        try:
            xform_op = self.xform.AddXformOp(xform_op_type, precision, op_suffix)
        except Tf.ErrorException:
            # Xform attribute doesn't exist, but the xform_op exists in the xformOpOrder attribute.
            # Reset the xformOpOrder
            self.xform.SetXformOpOrder(
                [xform_op for xform_op in self.xform_ops], self.xform.GetResetXformStack()
            )
            xform_op = self.xform.AddXformOp(xform_op_type, precision, op_suffix)
        return xform_op

    def _get_first_rotate_type(self) -> Tuple[UsdGeom.XformOp.Type, UsdGeom.XformOp.Precision]:
        for xform_op in self.xform_ops:
            op_type = xform_op.GetOpType()
            if UsdGeom.XformOp.TypeRotateX <= op_type <= UsdGeom.XformOp.TypeOrient:
                return op_type, xform_op.GetPrecision()

        # Get rotate type from given rotation order if possible. Otherwise use TypeOrient for rotation
        first_rotate_op_type = self._get_rotation_order_type()
        if first_rotate_op_type == UsdGeom.XformOp.TypeInvalid:
            first_rotate_op_type = UsdGeom.XformOp.TypeOrient

        return first_rotate_op_type, UsdGeom.XformOp.PrecisionDouble

    def _get_srt_xform_op_values(self):
        # Collect all xform ops
        xform_op_values = []

        # Translate op
        xform_op = self._find_or_add(UsdGeom.XformOp.TypeTranslate, True, UsdGeom.XformOp.PrecisionDouble)
        xform_op_values.append((xform_op, self._translation))

        # Rotate op
        first_rotate_op_type, precision = self._get_first_rotate_type()

        # Rotate XYZ as 3 xform ops
        if first_rotate_op_type in (UsdGeom.XformOp.TypeRotateX,
                                    UsdGeom.XformOp.TypeRotateY, UsdGeom.XformOp.TypeRotateZ):
            # Add in reverse order
            axis_type = (UsdGeom.XformOp.TypeRotateX, UsdGeom.XformOp.TypeRotateY, UsdGeom.XformOp.TypeRotateZ)
            for i in range(2, -1, -1):
                axis = self._rotation_order[i]
                xform_op = self._find_or_add(axis_type[axis], True, precision)
                xform_op_values.append((xform_op, self._rotation_euler[axis]))

        # Rotate XYZ as 1 xform op
        elif first_rotate_op_type in (UsdGeom.XformOp.TypeRotateXYZ, UsdGeom.XformOp.TypeRotateXZY,
                                      UsdGeom.XformOp.TypeRotateYXZ, UsdGeom.XformOp.TypeRotateYZX,
                                      UsdGeom.XformOp.TypeRotateZXY,UsdGeom.XformOp.TypeRotateZYX):
            # Make sure the given rotation order is same as the xformOp attribute one.
            provided_rotation_order = self._get_rotation_order_type(default=first_rotate_op_type)
            if provided_rotation_order != first_rotate_op_type:
                LOGGER.warning(
                    "Existing rotation order %s on prim %s is different than desired %s, overriding...",
                    first_rotate_op_type, self._prim_path, provided_rotation_order
                )
            xform_op = self._find_or_add(first_rotate_op_type, True, precision)
            xform_op_values.append((xform_op, self._rotation_euler))

        elif first_rotate_op_type == UsdGeom.XformOp.TypeOrient:
            xform_op = self._find_or_add(first_rotate_op_type, True, precision)
            axes = [Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis()]
            rotation = (
                Gf.Rotation(axes[self._rotation_order[0]], self._rotation_euler[self._rotation_order[0]])
                * Gf.Rotation(axes[self._rotation_order[1]], self._rotation_euler[self._rotation_order[1]])
                * Gf.Rotation(axes[self._rotation_order[2]], self._rotation_euler[self._rotation_order[2]])
            )
            xform_op_values.append((xform_op, rotation.GetQuat()))
        else:
            LOGGER.error("Failed to determine rotation order and type from %s", first_rotate_op_type)

        # Scale op
        xform_op = self._find_or_add(UsdGeom.XformOp.TypeScale, True, UsdGeom.XformOp.PrecisionDouble)
        xform_op_values.append((xform_op, self._scale))

        return xform_op_values

    def _set_transform_as_srt(self, skip_equal_set_for_timesample: Optional[bool] = False) -> None:
        """Set srt xform ops to UsdGeom.Xformable object
        Don't use UsdGeomXformCommonAPI. It can only manipulate a very limited subset of
        xformOpOrder combinations. Do it manually as non-destructively as possible
        """
        # Note: this has to be run out side of Sdf.ChangeBlock. _get_srt_xform_op_values might add
        # xform ops above sdf level. That might make USD unhappy.
        # It is not safe to create new xformOps inside of SdfChangeBlocks, since
        # new attribute creation via anything above Sdf API requires the PcpCache
        # to be up to date.
        xform_op_values = self._get_srt_xform_op_values()

        # Setting all srt xform ops
        with Sdf.ChangeBlock():
            new_xform_ops = []
            for xform_op, value in xform_op_values:
                self._set_value_with_precision(
                    xform_op, value, skip_equal_set_for_timesample=skip_equal_set_for_timesample)
                new_xform_ops.append(xform_op)

            # Add pivot if it exists. Note DO NOT run self._find_or_add(create_if_not_exist=True)
            # It is dangerous and might crash since we are in Sdf.ChangeBlock context.
            pivot_op = self._find_or_add(
                UsdGeom.XformOp.TypeTranslate, False, UsdGeom.XformOp.PrecisionDouble, "pivot"
            )
            # Pivot is the last one
            if pivot_op:
                new_xform_ops.append(pivot_op)

            # Add new xform ops to the xform order list. Keep the xform order as is.
            new_xform_order = []
            for xform_op in self.xform_ops:
                if xform_op in new_xform_ops:
                    new_xform_order.append(new_xform_ops.pop(new_xform_ops.index(xform_op)))
            new_xform_order.extend(new_xform_ops)

            self.xform.SetXformOpOrder(new_xform_order, self.xform.GetResetXformStack())

    def _clear_transform_at_time(self, time_code: Optional[Usd.TimeCode] = None):
        if time_code is None:
            time_code = self._time_code

        if time_code.IsDefault():
            return

        for xform_op in self.xform_ops:
            if self._has_time_sample(xform_op, time_code):
                xform_op.GetAttr().ClearAtTime(time_code)

    def do(self):
        with Usd.EditContext(self._stage):
            self.set_transform(skip_equal_set_for_timesample=True)

    def undo(self):
        # TODO
        raise NotImplementedError


def extract_srt_xform_from_matrix4(
        matrix4: Gf.Matrix4d,
        rotation_order: Optional[Gf.Vec3i]=Gf.Vec3i(0, 1, 2)
    ) -> Tuple[Gf.Vec3d,  Gf.Vec3d,  Gf.Vec3d]:

    matrix4.Orthonormalize()
    gf_transform = Gf.Transform(matrix4)
    translate = Gf.Vec3d(gf_transform.GetTranslation())
    scale = Gf.Vec3d(gf_transform.GetScale())
    rotate = decompose_rotation(gf_transform.GetRotation(), rotation_order)
    return translate, scale, rotate


def decompose_rotation(
        rotation: Gf.Rotation,
        rotation_order: Optional[Gf.Vec3i]=Gf.Vec3i(0, 1, 2)
    ) -> Gf.Vec3d:
    axes = [Gf.Vec3d.XAxis(), Gf.Vec3d.YAxis(), Gf.Vec3d.ZAxis()]
    rotate = rotation.Decompose(
        axes[rotation_order[0]],
        axes[rotation_order[1]],
        axes[rotation_order[2]]
    )
    return Gf.Vec3d(rotate)


def get_srt_xform_from_prim(
        prim: Usd.Prim,
        defaults: Optional[Tuple[Gf.Vec3d,  Gf.Vec3d,  Gf.Vec3d]] = None
    ) -> Tuple[Gf.Vec3d,  Gf.Vec3d,  Gf.Vec3d]:
    """Getting the transformation from the givem prim and returns as Translate RotateXYZ, Scale formate.

    NOTE This function extracts Rotation from Transform(matrix4) and/or Orient/Quaternion(vec4)
    into RotationXYZ. It IGNORES other rotation orders (XZY, YXZ, YZX, ZXY, ZYX).
    """
    xform = UsdGeom.Xformable(prim)

    # set default
    if defaults is None:
        defaults = (Gf.Vec3d(0, 0, 0), Gf.Vec3d(0, 0, 0), Gf.Vec3d(1, 1, 1))
    translate, rot_xyz, default_scale = defaults
    scale = None

    # Get current
    xform_ops = xform.GetOrderedXformOps()
    for xop in xform_ops:
        if xop.GetOpType() == UsdGeom.XformOp.TypeTransform:
            _translate, _scale, _rot_xyz = extract_srt_xform_from_matrix4(xop.Get())
            translate += _translate
            rot_xyz += _rot_xyz
            scale = Gf.Vec3d(0, 0, 0) + _scale if scale is None else scale + _scale
        elif xop.GetOpType() == UsdGeom.XformOp.TypeOrient:
            rot_xyz += decompose_rotation(Gf.Rotation(xop.Get()))
        elif xop.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate += Gf.Vec3d(xop.Get())
        elif xop.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
            rot_xyz += Gf.Vec3d(xop.Get())
        elif xop.GetOpType() == UsdGeom.XformOp.TypeScale:
            _scale = Gf.Vec3d(xop.Get())
            scale = Gf.Vec3d(0, 0, 0) + _scale if scale is None else scale + _scale

    if scale is None:
        scale = default_scale

    return translate, rot_xyz, scale