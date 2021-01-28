import sys

from tconsole import fprint
from wzryProxy import PlayMaoXianWanFaProxy, PlayLiuGuoYuanZhenProxy, GameStopCondition

if __name__ == '__main__':
    fprint("程序启动，开始监听手机屏幕，请确保手机已经打开USB调试")

    ######## 冒险挑战 ######
    gameProxy = PlayMaoXianWanFaProxy() # 无限制，一直打下去(提示：腾讯有健康时长，久了会禁赛，金币每周也是有上限的)
    # gameProxy = PlayMaoXianWanFaProxy(GameStopCondition.TIMES, 1000) # 玩1000把游戏
    # gameProxy = PlayMaoXianWanFaProxy(GameStopCondition.COINS, 5000) # 打5000金币
    # gameProxy = PlayMaoXianWanFaProxy(GameStopCondition.EXPR, 10000) # 打10000经验
    # gameProxy = PlayMaoXianWanFaProxy(GameStopCondition.TIME_SECOND, 6 * 60 * 60) # 玩6个小时游戏

    ######## 六国远征 ######
    # gameProxy = PlayLiuGuoYuanZhenProxy()
    gameProxy.start()
    try:
        gameProxy.join()
    except KeyboardInterrupt:
        sys.exit(0)