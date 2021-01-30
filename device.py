import random
import subprocess
import threading
import time

import aircv as ac

from btnEnModelMapRes import btnEnModelMap, ImgBtnTapModel, PosBtnTapModel
from tcevent import EventObservable
from tconsole import fprint


# Adb设备
class AdbDevice:
    deviceLock = threading.Lock()
    onTriggerCutScreenFun = None
    def __init__(self):
        pass
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

# 设备仿真
class DeviceEmulator(EventObservable):
    adbDevice:AdbDevice = None
    acLock = threading.Lock()
    tryBtnLock = threading.Lock()

    def __init__(self):
        EventObservable.__init__(self)
        fprint("开始监听手机屏幕，请确保手机已经打开USB调试")
        # adb设备
        self.adbDevice = AdbDevice()
        # 保证设备可用
        self.adbDevice.connect()

    def __del__(self):
        # self.adbDevice.disConnect()  # 这个不需要，完毕adb被其他程序使用，关掉服务就影响了
        pass

    # 截图
    def screenshot(self):
        self.adbDevice.cutScreen()
        self.tiggerEvent('screenshot', target=self)
        # def func():
        #     pass
        # _thread.start_new_thread(func)

    # 在stage中识别图片，返回识别结果
    def recognitionImg(self, btnName, stage="screen"):
        self.acLock.acquire()
        recognitionResult = None
        try:
            imsrc = ac.imread(f"./res/stage/{stage}.png")
            imobj = ac.imread(f"./res/btn/{btnName}.png")
            recognitionResult = ac.find_template(imsrc, imobj)

            self.tiggerEvent('recognitionImg', target=self)
        except Exception as e:
            print(e)
        finally:
            self.acLock.release()
        return recognitionResult

    # acceptableConfidence 可信任值
    # return 返回是否找到并触发
    def tryBtnTap(self, btnName, btnCnName=None, stage="screen", sleep=0.05, acceptableConfidence=0.90):
        self.tryBtnLock.acquire()
        try:
            recRes = self.recognitionImg(btnName, stage)
            if recRes and recRes.get('confidence') > acceptableConfidence:
                confidence = recRes.get('confidence')
                w = [recRes['rectangle'][0][0], recRes['rectangle'][2][0]]
                h = [recRes['rectangle'][0][1], recRes['rectangle'][1][1]]
                tapPos = [random.randint(w[0], w[1]), random.randint(h[0], h[1])]  # 随机，模拟人为点击位置不固定
                self.adbDevice.tap(tapPos)

                self.tiggerEvent('tryBtnTap', target=self)

                if btnCnName == None: btnCnName = btnName
                fprint(f'{btnCnName}按钮 tap:{tapPos} confidence:{confidence}')

                if sleep != 0:
                    time.sleep(sleep)
                return True
            return False
        except Exception as e:
            # raise e
            pass
        finally:
            self.tryBtnLock.release()

    # 执行查找动作，返回是否找到
    def doFindAction(self, action: str, showMsg: bool = True, caputureScreen: bool = False) -> bool:
        btnActionModel = btnEnModelMap[action]
        if caputureScreen:
            self.screenshot()
        if showMsg:
            fprint(f'执行动作：{btnActionModel.toString()}')
        recRes = self.recognitionImg(btnActionModel.btnEnName, btnActionModel.stage)
        isFind = recRes and recRes.get('confidence') > btnActionModel.acceptableConfidence

        self.tiggerEvent('doFindAction', target=self)

        return isFind

    # 执行单个行为
    # @param action 动作
    # @return bool 返回是否找到图像元素并发生点击
    def doTryTapAction(self, action: str, showMsg: bool = True, caputureScreen: bool = False):
        btnActionModel = btnEnModelMap[action]
        if caputureScreen:
            self.screenshot()
        if showMsg:
            fprint(f'执行动作：{btnActionModel.toString()}')
        if isinstance(btnActionModel, ImgBtnTapModel):
            flag = self.tryBtnTap(btnActionModel.btnEnName,
                             btnActionModel.btnCnName,
                             btnActionModel.stage,
                             btnActionModel.sleep,
                             btnActionModel.acceptableConfidence)
            self.tiggerEvent('doFindAction', target=self)
            return flag
        elif isinstance(btnActionModel, PosBtnTapModel):
            tapPos = [
                btnActionModel.posX + random.randint(-4, 4),  # 模拟人为非固定点击
                btnActionModel.posY + random.randint(-4, 4)
            ]
            self.adbDevice.tap(tapPos)
            fprint(f'{btnActionModel.btnCnName}按钮 tap:{tapPos} confidence:1')

            self.tiggerEvent('doFindAction', target=self)
            return True

    # 执行一个行为序列列表
    # @param actions 动作序列  第一层动作序列是会捕捉屏幕，但是第二层就不会了（认为是同一个界面上的操作）。
    # @param caputureScreen 是否捕获屏幕
    def doTryTapActionList(self, actions: list, caputureScreen: bool = True):
        for action in actions:
            if caputureScreen == True:
                self.screenshot()
            if isinstance(action, list):
                self.doTryTapActionList(action, caputureScreen=False)
            else:
                self.doTryTapAction(action)
        self.tiggerEvent('doTryTapActionList', target=self)
