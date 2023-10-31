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

import asyncio
from contextlib import suppress

_global_instance = None

class TickUpdate:
    def __init__(self):
        self.is_started = False
        self._task = None

    def setup_tick(self, interval):
        global _global_instance
        _global_instance = self

        self.update_callbacks = []
        self.interval = interval

    def start(self):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    def register_update_callback(self, update_callback):
        self.update_callbacks.append(update_callback)

    def unregister_update_callback(self, update_callback):
        self.update_callbacks.remove(update_callback)

    async def _run(self):
        while True:
            await asyncio.sleep(self.interval)
            for callback in self.update_callbacks:
                callback(self.interval)

    @staticmethod
    def _get_instance():
        global _global_instance
        return _global_instance


def get_instance():
    return TickUpdate._get_instance()