# import subprocess
# import threading 
# import queue
# import time
# import urllib.request



# import sys

# cmd = r"C:\Users\raska\AppData\Roaming\FreeCAD\Mod\Omniverse_Connector/omniConnect/run_py_live_session.bat --nucleus_url omniverse://localhost/Users/raska/FreeCAD/iterSample/assembly/myAssembly.usda --start_live --session_name helloSession --mesh divertor"


# with open("test.log", "wb") as f:
#     process = subprocess.Popen(['powershell', cmd], stdout=subprocess.PIPE)
#     for c in iter(lambda: process.stdout.read(1), b""):
#         sys.stdout.buffer.write(c)
#         f.buffer.write(c)

import asyncio

async def _read_stream(stream, cb):  
    while True:
        line = await stream.readline()
        if line:
            cb(line)
        else:
            break

async def _stream_subprocess(cmd, stdout_cb, stderr_cb):  
    process = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    await asyncio.gather(
        _read_stream(process.stdout, stdout_cb),
        _read_stream(process.stderr, stderr_cb)
    )
    return await process.wait()


def execute(cmd, stdout_cb, stderr_cb):  
    loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(
        _stream_subprocess(
            cmd,
            stdout_cb,
            stderr_cb,
    ))
    loop.close()
    return rc

if __name__ == '__main__':  
    cmd = r"C:\Users\raska\AppData\Roaming\FreeCAD\Mod\Omniverse_Connector/omniConnect/run_py_live_session.bat --nucleus_url omniverse://127.0.0.1/Users/raska/FreeCAD/project1/assembly/test_assy.usda --session_name helloSession --start_live"
    print(execute(
        ["powershell", cmd],
        lambda x: print("STDOUT: %s" % x),
        lambda x: print("STDERR: %s" % x),
    ))