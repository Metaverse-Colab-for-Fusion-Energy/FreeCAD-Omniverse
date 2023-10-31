from subprocess import Popen, PIPE, STDOUT
import sys
import datetime
import time
import asyncio
import sys
# import signal
import os

async def ainput(prompt=None) -> str:
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

cmd = r"C:\Users\mbgm5rs4\AppData\Roaming\FreeCAD\Mod\Omniverse_Connector\omniConnect\run_py_live_session.bat --nucleus_url omniverse://localhost/Users/raska/FreeCAD/iterSample/assembly/mySampleAssembly.usda --start_live --session_name session1 "



p = Popen(['powershell', cmd], stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0)

# THIS ONE WORKS!! DO NOT DELETE JUST COMMENT OUT
counter = 0
for line in iter(p.stdout.readline, b''):
    if counter >=500:
        # p.kill()
        break
    else:
        option = ainput()
        if option !=None:
            # print('writing '+str(option)+' to stdin')
            comm_option = bytes(str(option)+'\n', 'utf-8')
            p.stdin.write(comm_option)
        print(str(datetime.datetime.now())+" | " + line.decode('utf-8'))
        counter+=1
        time.sleep(0.1)
print('done process')
# exit will have to be removed when we do the thing - must figure out way to terminate PROCESS
exit()

# process terminates when 8 q's are run. maybe a test is needed to do this