import subprocess
import threading

from tconsole import fprint

# Adb设备
class AdbDevice:
    deviceLock = threading.Lock()
    # 连接
    def connect(self):
        self.deviceLock.acquire()
        try:
            subprocess.run("adb start-server", capture_output=True, shell=True)
            subprocess.run("adb device", capture_output=True, shell=True)
        finally:
            self.deviceLock.release()

    # 释放
    def disConnect(self):
        self.deviceLock.acquire()
        try:
            subprocess.run("adb kill-server", capture_output=True, shell=True)
        finally:
            self.deviceLock.release()

    # 从手机端截屏，并将图片返回到程序资源目录
    def cutScreen(self):
        self.deviceLock.acquire()
        try:
            cp = subprocess.run("adb shell screencap -p /sdcard/screen.png", capture_output=True, shell=True)
            if cp.returncode == 0:
                cp = subprocess.run("adb pull /sdcard/screen.png ./res/stage/", capture_output=True, shell=True)
                if cp.returncode == 0:
                    # fprint("截图成功")
                    return True
            fprint(f"截图失败！{cp.stderr}")
        finally:
            self.deviceLock.release()
        return False

    # 点击屏幕
    def tap(self, pos):
        self.deviceLock.acquire()
        try:
            width, height = pos[0], pos[1]
            subprocess.run(f'adb shell input tap {width} {height}', capture_output=True, shell=True)
        finally:
            self.deviceLock.release()
