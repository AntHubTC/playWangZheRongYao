import math
import sys
import threading
import time
import tkinter as tk
from enum import Enum, unique
from tkinter import messagebox

from PIL import Image, ImageTk

from device import DeviceEmulator
from tcevent import EventObservable
from tconsole import fprint

try:
    @unique
    class GameStopCondition(Enum):  # 游戏停止条件：枚举
        FOREVER = 'FOREVER'  # 一直执行下去
        TIME_SECOND = 'TIME_SECOND'  # 玩游戏的时间
        TIMES = 'TIMES'  # 次数
        COINS = 'COINS'  # 金币收入数量
        EXPR = 'EXPR'  # 经验收入量
except ValueError as e:
    print(e)


# 格式化游戏耗时时间
def getGameTimeFormat(seconds):
    if seconds < 60:
        return f'{seconds}秒'
    elif seconds < 3600:
        return f'{math.floor(seconds / 60)}分{seconds % 60}秒'
    else:
        return f'{math.floor(seconds / 3600)}时{math.floor(seconds % 3600 / 60)}分{seconds % 60}秒'


# 游戏代理
class GamePlayProxy(threading.Thread, EventObservable):
    __gaming__: bool = False  # 是否开始游戏
    __firstProxyPlayTime__: float = None  # 首次开始时间
    __proxyPlayTimes__: int = 0  # 游戏玩的次数
    device: DeviceEmulator = None  # 游戏设备
    gameMode: GameStopCondition = GameStopCondition.FOREVER  # 当前代理模式
    gameActionMonitorFreq: float = 0.5  # 游戏行为检测频率
    restrictPlayTimeSec: int = None  # 限制玩游戏的时间
    restrictPlayCount: int = None  # 限制代打次数
    restrictCoins: int = None  # 限制金币获取数量
    restrictExpr: int = None  # 限制经验获取数量
    gameInCoinsPer: int = 25  # 平均每一局收益金币数量
    gameInExpPer: int = 102  # 平均每一局收益经验数量

    def __init__(self,
                 device: DeviceEmulator = None,  # 游戏设备
                 gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                 restrictValue: int = None,  # 对应模式的限制值
                 gameActionMonitorFreq: float = 0.5  # 游戏行为检测频率
                 ):
        threading.Thread.__init__(self)
        EventObservable.__init__(self)

        # 根据游戏模式，设置限制值
        self.restrictPlayTimeSec = None
        self.restrictPlayCount = None
        self.restrictCoins = None
        self.restrictExpr = None
        if gameMode == GameStopCondition.FOREVER:
            pass  # 一直执行，无限制
        elif gameMode == GameStopCondition.TIME_SECOND:
            self.restrictPlayTimeSec = restrictValue
        elif gameMode == GameStopCondition.TIMES:
            self.restrictPlayCount = restrictValue
        elif gameMode == GameStopCondition.COINS:
            self.restrictCoins = restrictValue
        elif gameMode == GameStopCondition.EXPR:
            self.restrictExpr = restrictValue
        else:
            fprint("非法游戏模式！")
            exit(1)
        self.device = device
        self.gameMode = gameMode
        self.gameActionMonitorFreq = gameActionMonitorFreq

    def __del__(self):
        self.__gaming__ = False
        # self.shp.reqStop() # 停止监测跳过健康系统

    # 打印收入信息
    def __printInCome(self):
        inComeStr = '\n===============结算信息================='
        inComeStr += f'\n游戏次数：{self.__proxyPlayTimes__}'
        inComeStr += f'\n大约累计金币：{self.__proxyPlayTimes__ * self.gameInCoinsPer}'
        inComeStr += f'\n大约累计经验：{self.__proxyPlayTimes__ * self.gameInExpPer}'
        inComeStr += f'\n已经玩游戏{getGameTimeFormat(math.floor(time.time() - self.__firstProxyPlayTime__))}了'
        inComeStr += '\n======================================'

        # 显示收入信息
        self.tiggerEvent('showInCome', msg = inComeStr)
        fprint(inComeStr)

    # 是否继续游戏
    def isContinue(self) -> bool:
        isContinueFlag: bool = True
        # 游戏完毕后做什么
        if self.gameMode == GameStopCondition.FOREVER:
            pass  # 无限制，继续战！
        elif self.gameMode == GameStopCondition.TIME_SECOND:
            if math.floor(time.time() - self.__firstProxyPlayTime__) >= self.restrictPlayTimeSec:
                fprint('温馨提示::已经玩了很久了，已经超过限制时间了!~')
                isContinueFlag = False
        elif self.gameMode == GameStopCondition.TIMES:
            if self.__proxyPlayTimes__ >= self.restrictPlayCount:
                fprint('温馨提示::不能继续玩了，已经达到了限制次数!~')
                isContinueFlag = False
        elif self.gameMode == GameStopCondition.COINS:
            if self.__proxyPlayTimes__ * self.gameInCoinsPer >= self.restrictCoins:
                fprint('温馨提示::已经达到了最高限制金币，继续往下玩可能没有金币收益哦！~')
                isContinueFlag = False
        elif self.gameMode == GameStopCondition.EXPR:
            if self.__proxyPlayTimes__ * self.gameInExpPer >= self.restrictExpr:
                fprint('温馨提示::已经达到了最高限制经验，继续往下玩可能没有经验收益哦！~')
                isContinueFlag = False
        else:
            fprint('目前不支持该模式！')
        return isContinueFlag

    # 游戏代理开始玩游戏
    def run(self) -> None:
        shp = SkipHealthProtection(self.device)
        shp.start()  # 启动健康系统
        self.__gaming__ = False
        self.__firstProxyPlayTime__ = time.time()  # 首次开始时间
        fprint('进入游戏场景...')
        enterSucc = self.enterGame()  # 进入游戏场景
        if not enterSucc:
            fprint('进入游戏场景失败，停止运行！~')
            # TODO 停止整个程序
            return
        fprint('进入游戏场景完毕，进入游戏...')
        self.__gaming__ = True

        self.loadGame()  # 加载游戏
        self.__proxyPlayTimes__ = 1  # 代打次数

        while self.__gaming__ == True:  # 游戏内监测
            self.device.screenshot() # 截屏大概需要两秒
            self.playGaming()  # 游戏内玩游戏
            if self.isGameOver():  # 判定游戏是否结束
                self.__gaming__ = False
                fprint('单局游戏结束！，正在结算...')
                self.__printInCome()  # 打印收入信息

                self.gamePerEndHandle()  # 单局游戏后处理

                # 判断是否再战！
                if self.isContinue():
                    fprint('再战一局！')
                    self.playAgain()  # 再次玩游戏
                    self.__proxyPlayTimes__ += 1
                    self.__gaming__ = True
            # 休息片刻，再次进行下一轮监测
            time.sleep(self.gameActionMonitorFreq)
        # 停止健康系统
        shp.reqStop()

    # 加载游戏
    def loadGame(self):
        fprint('正在加载游戏...')
        time.sleep(8)  # 假定游戏加载界面进行了8秒
        fprint('加载游戏完毕，开始玩游戏')

    # 进入游戏场景
    def enterGame(self):
        pass

    # 游戏内玩游戏
    def playGaming(self):
        pass

    # 单局游戏后处理
    def gamePerEndHandle(self):
        pass

    # 再次进入游戏
    def playAgain(self):
        pass

    # 检测当局是否已经结束
    def isGameOver(self):
        return True

    # 获取当前游戏状态
    def getGameSate(self) -> bool:  # True进行中 False游戏未进行
        return self.__gaming__


# 冒险玩法游戏代理
class PlayMaoXianWanFaProxy(GamePlayProxy):
    def __init__(self,
                 device: DeviceEmulator = None,  # 游戏设备
                 gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                 restrictValue: int = None,  # 对应模式的限制值
                 gameActionMonitorFreq: float = 0.5  # 游戏行为检测频率
                 ):
        GamePlayProxy.__init__(self, device, gameMode, restrictValue, gameActionMonitorFreq)

    def enterGame(self):
        # 'resetNow': ImgBtnTapModel("resetNow", '立即重置'),
        self.device.doTryTapActionList([
            'wanxiangtiangong', 'maoxianwanfa', 'maoxiantiaozhan',
            'maoxianjxxy', ['maoxianjxxygameLevel', 'nextStep'],
            'chuangguan'
        ])
        return True

    def playGaming(self):  # 玩游戏
        # doAction('notautogame') # 非自动切换为自动，这个识别率太低，有时候会搞错，他游戏本身如果是自动了一场也会是自动的
        self.device.doTryTapAction('maoxiantiaoguo', showMsg=False)  # 跳过游戏中存在的剧情

    def playAgain(self):  # 再次进入游戏
        self.device.doTryTapActionList(['zaicitiaozhan', 'chuangguan'])

    def isGameOver(self):  # 检测当局是否已经结束
        flag1 = self.device.doTryTapAction('clickcontinue', showMsg=False)  # 点击继续
        flag2 = self.device.doTryTapAction('zaicitiaozhan', showMsg=False)  # 再次挑战
        flag3 = self.device.doTryTapAction('gameFail', showMsg=False)  # 游戏失败
        if flag3:  # 游戏失败返回
            fprint('游戏失败！~')
            time.sleep(1)  # 游戏失败后要等一会儿才会出按钮
            self.device.doTryTapActionList(['backBtnYellow', 'nextStep'])
            # TODO：： 失败应该不记录场次和金币经验，这个可以通过返回不同的游戏状态来做处理
        return flag1 or flag2 or flag3


# 六国远征游戏代理
class PlayLiuGuoYuanZhenProxy(GamePlayProxy):
    curLevel: int = None  # 当前关卡
    MAX_LEVEL: int = 6  # 最高关卡

    def __init__(self,
                 device: DeviceEmulator = None,  # 游戏设备
                 gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                 restrictValue: int = None,  # 对应模式的限制值
                 gameActionMonitorFreq: float = 0.1  # 游戏行为检测频率
                 ):
        GamePlayProxy.__init__(self, device, gameMode, restrictValue, gameActionMonitorFreq)
        self.curLevel = 1  # 默认初始第一关

    def enterGame(self):
        self.device.doTryTapActionList([
            'wanxiangtiangong', 'maoxianwanfa', 'maoxianliuguoyuanzheng'
        ])

        # 下面是判断当前关卡是否已经挑战，如果已经挑战就前往下一关挑战，如果都挑战完毕了，那么就不进入直接返回false
        isLiuGuoYuanZhengMainPage: bool = True
        while self.curLevel <= self.MAX_LEVEL and isLiuGuoYuanZhengMainPage:
            self.device.doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}', caputureScreen=True)
            isLiuGuoYuanZhengMainPage = self.device.doFindAction('liuguoyuanzhengpageflag',
                                                                 caputureScreen=True)  # 判断还是不是在原来的页面，如果是就前往下一关
            if isLiuGuoYuanZhengMainPage:
                # 看一下当前关的宝箱领取没有，没有就将宝箱领取了
                if self.device.doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}_case'):
                    time.sleep(0.5)
                    self.device.doTryTapAction('okBtnBlue', caputureScreen=True)  # 确认收下宝箱
                    time.sleep(1)
                self.curLevel += 1
        if not isLiuGuoYuanZhengMainPage:  # 如果不在主页面了
            self.device.doTryTapActionList([  # 进入关卡挑战
                'tiaozhan', 'okBtnYellow'
            ])
        # 返回是否进入游戏成功
        return not isLiuGuoYuanZhengMainPage

    def gamePerEndHandle(self):  # 每局结束处理
        # 领当前关的宝箱
        if self.device.doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}_case', caputureScreen=True):
            self.device.doTryTapAction('okBtnBlue')  # 确认收下宝箱
            time.sleep(0.5)
        # 前往下一关
        self.curLevel += 1

    def isContinue(self) -> bool:
        return super().isContinue() and self.curLevel <= self.MAX_LEVEL  # 基础条件加不能超过六国远征关数

    def playAgain(self):  # 再次进入游戏
        self.device.doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}', caputureScreen=True)
        self.device.doTryTapActionList([
            'tiaozhan', 'okBtnYellow'
        ])

    def isGameOver(self):  # 检测当局是否已经结束
        flag1 = self.device.doTryTapAction('clickcontinue2', showMsg=False)  # 点击继续
        flag2 = self.device.doTryTapAction('zaicitiaozhan', showMsg=False)  # 再次挑战
        flag3 = self.device.doTryTapAction('gameFail', showMsg=False)  # 游戏失败
        if flag3:  # 游戏失败返回
            fprint('游戏失败！~')
            self.device.doTryTapActionList(['clickcontinue2', 'continue'])
        self.device.doTryTapAction('continue', showMsg=False)
        time.sleep(2)
        return flag1 or flag2 or flag3


# 因为腾讯有健康保护系统（健康系统-时长保护温馨提示），只要在非游戏阶段，什么时候都有可能提示
class SkipHealthProtection(threading.Thread):
    flag: bool = True
    device: DeviceEmulator = None

    def __init__(self, device: DeviceEmulator):
        threading.Thread.__init__(self)
        self.device = device

    def run(self) -> None:
        fprint('提示：健康系统监测线程已经启动！~')
        while self.flag:
            # 由于代理玩游戏线程一直在捕捉画面，所以这里不截图，直接识别
            # 保护眼睛
            if (self.device.doTryTapAction('baohuyanjing', showMsg=False)):
                self.device.doTryTapAction('baohuyanjingok')
            # 禁赛
            if (self.device.doTryTapAction('baohujinshai', showMsg=False)):
                fprint('提示：健康系统监测线程已经关闭！~')
                fprint('已经被系统禁止比赛，程序退出（这里还有问题，不知道为啥这里停止不了）')
                # TODO:: 这里还有问题，不知道为啥这里停止不了
                self.reqStop()
                # self.gamePlayProxy.reqStop()
            # 检测频率（这个任务实时性不高，长一点都可以）
            time.sleep(5)
        fprint('提示：健康系统监测线程已经关闭！~')

    # 请求停止健康系统监测
    def reqStop(self):
        self.flag = False


#
# 如果导入不了tkinter， 这个时候使用 sudo apt-get install python3-tk
#
class MainGUI:
    curImage: ImageTk.PhotoImage # 当前图片
    imageLabel:tk.Label = None # image标签
    textInfoLabel:tk.Label = None # 游戏状态信息
    def __init__(self):
        # 不然调用结束后photo就被回收了
        # global imgPng

        self.winRoot = tk.Tk()
        self.winRoot.title('王者荣耀辅助助手')

        try:
            self.curImage = MainGUI.__getNewestImg()
            self.imageLabel = tk.Label(self.winRoot, image=self.curImage)
        except:
            self.imageLabel = tk.Label(self.winRoot)

        self.imageLabel.pack(side = 'top')

        self.textInfoLabel = tk.Label(self.winRoot, text='等待第一局完毕，显示结算信息...', height=10)
        self.textInfoLabel.pack(side='bottom')

        # 监听窗口关闭
        self.winRoot.protocol("WM_DELETE_WINDOW", self.onRootGUIClosing)

    @staticmethod
    def __getNewestImg():
        image_open = Image.open('./res/stage/screen.png')
        image_open = image_open.resize((int(300 / image_open.height * image_open.width), 300))
        return ImageTk.PhotoImage(image_open)

    def updateImg(self, eventName, **kwargs):
        try:
            self.curImage = MainGUI.__getNewestImg()
            self.imageLabel.config(image=self.curImage)
        except Exception as e:
            print(e)

    # 更新文字信息
    def updateTextInfo(self, eventName, **kwargs):
        self.textInfoLabel.config(text=kwargs['msg'])

    def onRootGUIClosing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.winRoot.destroy()
            # TODO:: 结束整个程序

    def mainloop(self) -> None:
        self.winRoot.mainloop()

# 游戏模拟器
class GameEmulator:
    __deviceEmulator__: DeviceEmulator = None  # 游戏设备
    __gameProxy__: GamePlayProxy = None  # 游戏代理
    __selectGameList__ = None  # 选择游戏列表
    __isShowGUI__:bool = True # 是否显示界面
    gameScreen:MainGUI = None # 游戏界面

    def __init__(self, isShowGUI:bool = True):
        self.__deviceEmulator__ = DeviceEmulator()
        self.__selectGameList__ = SelectGameList(self)
        self.__isShowGUI__ = isShowGUI
        if isShowGUI:
            self.gameScreen = MainGUI()
            self.__deviceEmulator__.addListener('screenshot', self.gameScreen.updateImg)

    # 显示游戏列表
    def showGameList(self):
        return self.__selectGameList__

    # 开始游戏
    def startGame(self, gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                  restrictValue: int = None,  # 对应模式的限制值
                  gameActionMonitorFreq: float = 0.01  # 游戏行为检测频率
                  ):
        if self.__selectGameList__.isSelectGameOpt(SelectGameList.MAO_XIAN_WAN_FA):  # 冒险玩法
            self.__gameProxy__ = PlayMaoXianWanFaProxy(self.__deviceEmulator__,
                                                       gameMode, restrictValue, gameActionMonitorFreq)
        elif self.__selectGameList__.isSelectGameOpt(SelectGameList.LIU_GUO_YUAN_ZHEN):  # 六国远征
            self.__gameProxy__ = PlayLiuGuoYuanZhenProxy(self.__deviceEmulator__,
                                                         gameMode, restrictValue, gameActionMonitorFreq)
        else:
            fprint('请选择游戏才进行游戏!')
            return

        # 监听显示最新数据事件
        self.__gameProxy__.addListener('showInCome', self.gameScreen.updateTextInfo)

        self.__gameProxy__.start()
        if self.__isShowGUI__:
            self.gameScreen.mainloop()
        else:
            try:
                self.__gameProxy__.join()
            except KeyboardInterrupt:
                sys.exit(0)

# 游戏列表
class SelectGameList:
    MAO_XIAN_WAN_FA = 1  # 冒险玩法
    LIU_GUO_YUAN_ZHEN = 2  # 六国远征
    # ...
    opt: int = None  # 选择选项

    def __init__(self, ge: GameEmulator):
        self.ge = ge

    def selectMaoXianWanFa(self) -> GameEmulator:  # 冒险玩法
        self.opt = SelectGameList.MAO_XIAN_WAN_FA
        return self.ge

    def selectLiuGuoYuanZhen(self) -> GameEmulator:  # 六国远征
        self.opt = SelectGameList.LIU_GUO_YUAN_ZHEN
        return self.ge

    def isSelectGameOpt(self, val) -> bool:
        return self.opt == val
