from wzryProxy import GameEmulator, GameStopCondition

if __name__ == '__main__':
    ######## 冒险挑战 ######
    gameEmulator = GameEmulator().showGameList().selectMaoXianWanFa()
    ######## 六国远征 ######
    # gameEmulator = GameEmulator().showGameList().selectLiuGuoYuanZhen()

    # 5种模式开始模式
    gameEmulator.startGame()  # 无限制，一直打下去(提示：腾讯有健康时长，久了会禁赛，金币每周也是有上限的)
    # gameEmulator.startGame(GameStopCondition.TIMES, 1000) # 玩1000把游戏
    # gameEmulator.startGame(GameStopCondition.COINS, 5000) # 打5000金币
    # gameEmulator.startGame(GameStopCondition.EXPR, 10000) # 打10000经验
    # gameEmulator.startGame(GameStopCondition.TIME_SECOND, 6 * 60 * 60) # 玩6个小时游戏