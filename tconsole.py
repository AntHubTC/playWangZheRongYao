import time

def fprint(msm):
    print(f"{time.strftime('%H:%M:%S', time.localtime(time.time()))}>> {msm}")