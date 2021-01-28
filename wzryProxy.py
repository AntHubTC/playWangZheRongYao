import math
import random
import threading
import time
from enum import Enum, unique

import aircv as ac

import device
from btnEnModelMapRes import btnEnModelMap, ImgBtnTapModel, PosBtnTapModel
from tconsole import fprint

# adb设备
adbDevice = device.AdbDevice()

acLock = threading.Lock()
# 在stage中识别图片，返回识别结果
def recognitionImg(btnName, stage ="screen"):
    acLock.acquire()
    recognitionResult = None
    try:
        imsrc = ac.imread(f"./res/stage/{stage}.png")
        imobj = ac.imread(f"./res/btn/{btnName}.png")
        recognitionResult = ac.find_template(imsrc, imobj)
    finally:
        acLock.release()
    return recognitionResult

tryBtnLock = threading.Lock()
# acceptableConfidence 可信任值
# return 返回是否找到并触发
def tryBtnTap(btnName, btnCnName = None, stage ="screen", sleep = 0.05, acceptableConfidence = 0.90):
    tryBtnLock.acquire()
    try:
        recRes = recognitionImg(btnName, stage)
        if recRes and recRes.get('confidence') > acceptableConfidence:
            confidence = recRes.get('confidence')
            w = [recRes['rectangle'][0][0], recRes['rectangle'][2][0]]
            h = [recRes['rectangle'][0][1], recRes['rectangle'][1][1]]
            tapPos = [random.randint(w[0], w[1]), random.randint(h[0], h[1])] # 随机，模拟人为点击位置不固定
            adbDevice.tap(tapPos)

            if btnCnName == None: btnCnName = btnName
            fprint(f'{btnCnName}按钮 tap:{tapPos} confidence:{confidence}')

            if sleep != 0:
                time.sleep(sleep)
            return True
        return False
    except Exception as e:
        raise e
    finally:
        tryBtnLock.release()

# 执行查找动作，返回是否找到
def doFindAction(action:str, showMsg:bool = True, caputureScreen:bool = False) ->bool:
    btnActionModel = btnEnModelMap[action]
    if caputureScreen:
        adbDevice.cutScreen()
    if showMsg:
        fprint(f'执行动作：{btnActionModel.toString()}')
    recRes = recognitionImg(btnActionModel.btnEnName, btnActionModel.stage)
    isFind = recRes and recRes.get('confidence') > btnActionModel.acceptableConfidence
    return isFind

# 执行单个行为
# @param action 动作
# @return bool 返回是否找到图像元素并发生点击
def doTryTapAction(action:str, showMsg:bool = True, caputureScreen:bool = False):
    btnActionModel = btnEnModelMap[action]
    if caputureScreen:
        adbDevice.cutScreen()
    if showMsg:
        fprint(f'执行动作：{btnActionModel.toString()}')
    if isinstance(btnActionModel, ImgBtnTapModel):
        return tryBtnTap(btnActionModel.btnEnName,
                     btnActionModel.btnCnName,
                     btnActionModel.stage,
                     btnActionModel.sleep,
                     btnActionModel.acceptableConfidence)
    elif isinstance(btnActionModel, PosBtnTapModel):
        tapPos = [
            btnActionModel.posX + random.randint(-4, 4), # 模拟人为非固定点击
            btnActionModel.posY + random.randint(-4, 4)
        ]
        adbDevice.tap(tapPos)
        fprint(f'{btnActionModel.btnCnName}按钮 tap:{tapPos} confidence:1')
        return True

# 执行一个行为序列列表
# @param actions 动作序列  第一层动作序列是会捕捉屏幕，但是第二层就不会了（认为是同一个界面上的操作）。
# @param caputureScreen 是否捕获屏幕
def doTryTapActionList(actions:list, caputureScreen:bool = True):
    for action in actions:
        if caputureScreen == True:
            adbDevice.cutScreen()
        if isinstance(action, list):
            doTryTapActionList(action, caputureScreen = False)
        else:
            doTryTapAction(action)

try:
   @unique
   class GameStopCondition(Enum): # 游戏停止条件：枚举
       FOREVER = 'FOREVER' # 一直执行下去
       TIME_SECOND = 'TIME_SECOND' # 玩游戏的时间
       TIMES = 'TIMES' # 次数
       COINS = 'COINS' # 金币收入数量
       EXPR = 'EXPR' # 经验收入量
except ValueError as e:
   print(e)

# 格式化游戏耗时时间
def getGameTimeFormat(seconds):
    if seconds < 60:
        return f'{seconds}秒'
    elif seconds < 3600:
        return f'{math.floor(seconds/60)}分{seconds%60}秒'
    else:
        return f'{math.floor(seconds/3600)}时{math.floor(seconds%3600/60)}分{seconds%60}秒'

# 游戏代理
class GamePlayProxy(threading.Thread):
    __gaming__:bool = False # 是否开始游戏
    __firstProxyPlayTime__: float = None # 首次开始时间
    __proxyPlayTimes__:int = 0 # 游戏玩的次数
    gameMode: GameStopCondition = GameStopCondition.FOREVER # 当前代理模式
    gameActionMonitorFreq:float = 0.5 # 游戏行为检测频率
    restrictPlayTimeSec: int = None # 限制玩游戏的时间
    restrictPlayCount: int = None # 限制代打次数
    restrictCoins: int = None # 限制金币获取数量
    restrictExpr: int = None # 限制经验获取数量
    gameInCoinsPer: int = 25 # 平均每一局收益金币数量
    gameInExpPer: int = 102 # 平均每一局收益经验数量

    def __init__(self,
                 gameMode:GameStopCondition = GameStopCondition.FOREVER, # 游戏模式
                 restrictValue: int = None, # 对应模式的限制值
                 gameActionMonitorFreq:float = 0.5 # 游戏行为检测频率
                 ):
        threading.Thread.__init__(self)
        # 保证设备可用
        adbDevice.connect()

        # 根据游戏模式，设置限制值
        self.restrictPlayTimeSec = None
        self.restrictPlayCount = None
        self.restrictCoins = None
        self.restrictExpr = None
        if gameMode == GameStopCondition.FOREVER:
            pass # 一直执行，无限制
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
        self.gameMode = gameMode
        self.gameActionMonitorFreq = gameActionMonitorFreq

    def __del__(self):
        # adbDevice.disConnect()  # 这个不需要，完毕adb被其他程序使用，关掉服务就影响了
        self.__gaming__ = False
        self.shp.reqStop() # 停止监测跳过健康系统

    # 打印收入信息
    def __printInCome(self):
        fprint('===============结算信息=================')
        fprint(f'游戏次数：{self.__proxyPlayTimes__}')
        fprint(f'大约累计金币：{self.__proxyPlayTimes__ * self.gameInCoinsPer}')
        fprint(f'大约累计经验：{self.__proxyPlayTimes__ * self.gameInExpPer}')
        fprint(f'已经玩游戏{getGameTimeFormat(math.floor(time.time() - self.__firstProxyPlayTime__))}了')
        fprint('======================================')

    # 是否继续游戏
    def isContinue(self) -> bool:
        isContinue:bool = True
        # 游戏完毕后做什么
        if self.gameMode == GameStopCondition.FOREVER:
            pass  # 无限制，继续战！
        elif self.gameMode == GameStopCondition.TIME_SECOND:
            if math.floor(time.time() - self.__firstProxyPlayTime__) >= self.restrictPlayTimeSec:
                fprint('温馨提示::已经玩了很久了，已经超过限制时间了!~')
                isContinue = False
        elif self.gameMode == GameStopCondition.TIMES:
            if self.__proxyPlayTimes__ >= self.restrictPlayCount:
                fprint('温馨提示::不能继续玩了，已经达到了限制次数!~')
                isContinue = False
        elif self.gameMode == GameStopCondition.COINS:
            if self.__proxyPlayTimes__ * self.gameInCoinsPer >= self.restrictCoins:
                fprint('温馨提示::已经达到了最高限制金币，继续往下玩可能没有金币收益哦！~')
                isContinue = False
        elif self.gameMode == GameStopCondition.EXPR:
            if self.__proxyPlayTimes__ * self.gameInExpPer >= self.restrictExpr:
                fprint('温馨提示::已经达到了最高限制经验，继续往下玩可能没有经验收益哦！~')
                isContinue = False
        else:
            fprint('目前不支持该模式！')
        return isContinue

    # 游戏代理开始玩游戏
    def run(self) -> None:
        shp = SkipHealthProtection()
        shp.start() # 启动健康系统
        self.__gaming__ = False
        self.__firstProxyPlayTime__ = time.time() # 首次开始时间
        fprint('进入游戏场景...')
        enterSucc = self.enterGame() # 进入游戏场景
        if not enterSucc:
            fprint('进入游戏场景失败，停止运行！~')
            # TODO 停止整个程序
            return
        fprint('进入游戏场景完毕，进入游戏...')
        self.__gaming__ = True

        self.loadGame() # 加载游戏
        self.__proxyPlayTimes__ = 1 # 代打次数

        while self.__gaming__ == True: # 游戏内监测
            adbDevice.cutScreen()
            self.playGaming() # 游戏内玩游戏
            if self.isGameOver(): # 判定游戏是否结束
                self.__gaming__ = False
                fprint('单局游戏结束！，正在结算...')
                self.__printInCome() # 打印收入信息

                self.gamePerEndHandle() # 单局游戏后处理

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
        time.sleep(8) # 假定游戏加载界面进行了8秒
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
    def getGameSate(self) -> bool: # True进行中 False游戏未进行
        return self.__gaming__

# 冒险玩法游戏代理
class PlayMaoXianWanFaProxy(GamePlayProxy):
    def __init__(self,
                 gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                 restrictValue: int = None,  # 对应模式的限制值
                 gameActionMonitorFreq: float = 0.5  # 游戏行为检测频率
                 ):
        GamePlayProxy.__init__(self, gameMode, restrictValue, gameActionMonitorFreq)

    def enterGame(self):
        # 'resetNow': ImgBtnTapModel("resetNow", '立即重置'),
        doTryTapActionList([
            'wanxiangtiangong', 'maoxianwanfa', 'maoxiantiaozhan',
            'maoxianjxxy', ['maoxianjxxygameLevel', 'nextStep'],
            'chuangguan'
        ])
        return True

    def playGaming(self): # 玩游戏
        # doAction('notautogame') # 非自动切换为自动，这个识别率太低，有时候会搞错，他游戏本身如果是自动了一场也会是自动的
        doTryTapAction('maoxiantiaoguo', showMsg = False) # 跳过游戏中存在的剧情

    def playAgain(self): # 再次进入游戏
        doTryTapActionList(['zaicitiaozhan', 'chuangguan'])

    def isGameOver(self): # 检测当局是否已经结束
        flag1 = doTryTapAction('clickcontinue', showMsg=False) # 点击继续
        flag2 = doTryTapAction('zaicitiaozhan', showMsg=False)  # 再次挑战
        flag3 = doTryTapAction('gameFail', showMsg=False)  # 游戏失败
        if flag3: # 游戏失败返回
            fprint('游戏失败！~')
            time.sleep(1) # 游戏失败后要等一会儿才会出按钮
            doTryTapActionList(['backBtnYellow', 'nextStep'])
            # TODO：： 失败应该不记录场次和金币经验，这个可以通过返回不同的游戏状态来做处理
        return flag1 or flag2 or flag3

# 六国远征游戏代理
class PlayLiuGuoYuanZhenProxy(GamePlayProxy):
    curLevel: int = None  # 当前关卡
    MAX_LEVEL: int = 6 # 最高关卡
    def __init__(self,
                 gameMode: GameStopCondition = GameStopCondition.FOREVER,  # 游戏模式
                 restrictValue: int = None,  # 对应模式的限制值
                 gameActionMonitorFreq: float = 0.5  # 游戏行为检测频率
                 ):
        GamePlayProxy.__init__(self, gameMode, restrictValue, gameActionMonitorFreq)
        self.curLevel = 1  # 默认初始第一关

    def enterGame(self):
        doTryTapActionList([
            'wanxiangtiangong', 'maoxianwanfa', 'maoxianliuguoyuanzheng'
        ])

        # 下面是判断当前关卡是否已经挑战，如果已经挑战就前往下一关挑战，如果都挑战完毕了，那么就不进入直接返回false
        isLiuGuoYuanZhengMainPage:bool = True
        while self.curLevel <= self.MAX_LEVEL and isLiuGuoYuanZhengMainPage:
            doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}', caputureScreen=True)
            isLiuGuoYuanZhengMainPage = doFindAction('liuguoyuanzhengpageflag', caputureScreen=True) # 判断还是不是在原来的页面，如果是就前往下一关
            if isLiuGuoYuanZhengMainPage:
                # 看一下当前关的宝箱领取没有，没有就将宝箱领取了
                if doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}_case'):
                    time.sleep(0.5)
                    doTryTapAction('okBtnBlue', caputureScreen=True)  # 确认收下宝箱
                    time.sleep(1)
                self.curLevel += 1
        if not isLiuGuoYuanZhengMainPage: # 如果不在主页面了
            doTryTapActionList([ # 进入关卡挑战
                'tiaozhan', 'okBtnYellow'
            ])
        # 返回是否进入游戏成功
        return not isLiuGuoYuanZhengMainPage

    def gamePerEndHandle(self): # 每局结束处理
        # 领当前关的宝箱
        if doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}_case', caputureScreen=True):
            doTryTapAction('okBtnBlue') # 确认收下宝箱
            time.sleep(0.5)
        # 前往下一关
        self.curLevel+=1

    def isContinue(self) -> bool:
        return super().isContinue() and self.curLevel <= self.MAX_LEVEL # 基础条件加不能超过六国远征关数

    def playAgain(self):  # 再次进入游戏
        doTryTapAction(f'maoxianlgyzLevel_{self.curLevel}', caputureScreen=True)
        doTryTapActionList([
            'tiaozhan', 'okBtnYellow'
        ])

    def isGameOver(self):  # 检测当局是否已经结束
        flag1 = doTryTapAction('clickcontinue2', showMsg=False)  # 点击继续
        flag2 = doTryTapAction('zaicitiaozhan', showMsg=False)  # 再次挑战
        flag3 = doTryTapAction('gameFail', showMsg=False)  # 游戏失败
        if flag3:  # 游戏失败返回
            fprint('游戏失败！~')
            doTryTapActionList(['clickcontinue2', 'continue'])
        doTryTapAction('continue', showMsg=False)
        time.sleep(2)
        return flag1 or flag2 or flag3

# 因为腾讯有健康保护系统（健康系统-时长保护温馨提示），只要在非游戏阶段，什么时候都有可能提示
class SkipHealthProtection(threading.Thread):
    flag:bool = True
    def run(self) -> None:
        fprint('提示：健康系统监测线程已经启动！~')
        while self.flag:
            # 由于代理玩游戏线程一直在捕捉画面，所以这里不截图，直接识别
            # 保护眼睛
            if(doTryTapAction('baohuyanjing', showMsg = False)):
                doTryTapAction('baohuyanjingok')
            # 禁赛
            if (doTryTapAction('baohujinshai', showMsg=False)):
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