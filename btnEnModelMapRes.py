####
#   按钮模型资源
####

class BtnTapModel:
    def __init__(self, btnEnName:str, btnCnName:str, sleep:float = 0.05):
        self.btnEnName = btnEnName
        self.btnCnName = btnCnName
        self.sleep = sleep
    def toString(self):
        return f'(btnEnName={self.btnEnName},btnCnName={self.btnCnName},sleep={self.sleep})'

# 图标按钮点击模型
class ImgBtnTapModel(BtnTapModel):
    def __init__(self, btnEnName:str, btnCnName:str, stage:str ="screen", sleep:float = 0.05, acceptableConfidence:float = 0.90):
        BtnTapModel.__init__(self, btnEnName, btnCnName, sleep)
        self.stage = stage
        self.acceptableConfidence = acceptableConfidence
    def toString(self):
        return f'(btnEnName={self.btnEnName},btnCnName={self.btnCnName},stage={self.stage},sleep={self.sleep},acceptableConfidence={self.acceptableConfidence})'

# 位置按钮点击模型
class PosBtnTapModel(BtnTapModel):
    def __init__(self, btnEnName:str, btnCnName:str, posX:float, posY:float, sleep:float = 0.05):
        BtnTapModel.__init__(self, btnEnName, btnCnName, sleep)
        self.posX = posX
        self.posY = posY
    def toString(self):
        return f'(btnEnName={self.btnEnName},btnCnName={self.btnCnName},sleep={self.sleep},pos=({self.posX}, {self.posY}))'

# 按钮模型映射
btnEnModelMap = {
    ###### 公共 #######
    'clickcontinue': ImgBtnTapModel("clickcontinue", '点击继续'), # 这个识别度不能降低了，降低了可能会导致检测失败连续开始新的一局
    'clickcontinue2': ImgBtnTapModel("clickcontinue2", '点击继续'),# 这个看起和第一个一样，但是匹配度就是不同
    'continue': ImgBtnTapModel("continue", '继续'),
    'nextStep': ImgBtnTapModel("nextStep", '下一步'),
    'gameFail': ImgBtnTapModel("gameFail", '游戏失败'),
    'backBtnYellow': ImgBtnTapModel("backBtnYellow", '返回'),
    'resetNow': ImgBtnTapModel("resetNow", '立即重置'),
    'tiaozhan': ImgBtnTapModel("tiaozhan", '挑战', sleep=0.5),
    'okBtnYellow': ImgBtnTapModel("okBtnYellow", '确定'),
    'okBtnBlue': ImgBtnTapModel("okBtnBlue", '确定'),
    ###### 公共--健康系统 #######
    'baohuyanjing': ImgBtnTapModel("baohuyanjing", '保护眼睛提示'),
    'baohuyanjingok': ImgBtnTapModel("baohuyanjingok", '保护眼睛提示-确认'),
    'baohujinshai': ImgBtnTapModel("baohujinshai", '保护健康，禁赛'),
    ###### 公共--万象天工 #######
    'wanxiangtiangong': ImgBtnTapModel("wanxiangtiangong", '万象天工', sleep=0.3),
    'maoxianliuguoyuanzheng': ImgBtnTapModel("maoxianliuguoyuanzheng", '冒险挑战'),
    'zaicitiaozhan': ImgBtnTapModel("zaicitiaozhan", '再次挑战'),
    'notautogame': ImgBtnTapModel("notautogame", '切换为自动', acceptableConfidence=0.95),
    'autogame': ImgBtnTapModel("autogame", '切换为手动', acceptableConfidence=0.95),
    'chuangguan': ImgBtnTapModel("chuangguan", '闯关'),
    ###### 冒险挑战 #####
    'maoxianwanfa': ImgBtnTapModel("maoxianwanfa", '冒险玩法', sleep=0.2),
    'maoxiantiaozhan': ImgBtnTapModel("maoxiantiaozhan", '冒险挑战'),
    'maoxianjxxy': ImgBtnTapModel("maoxianjxxy", '稷下学院mod', sleep=0.02),
    'maoxianjxxygameLevel': ImgBtnTapModel("maoxianjxxygameLevel", '稷下小关卡选择', sleep=0.02, acceptableConfidence=0.5),
    'maoxiantiaoguo': ImgBtnTapModel("maoxiantiaoguo", '冒险跳过剧情'),
    'liuguoyuanzhengpageflag': ImgBtnTapModel("liuguoyuanzhengpageflag", "六国远征-页面标志"),
    'maoxianlgyzLevel_1': PosBtnTapModel("maoxianlgyzLevel_1", "六国远征-第一关", 586, 305),
    'maoxianlgyzLevel_2': PosBtnTapModel("maoxianlgyzLevel_2", "六国远征-第二关", 1044, 139),
    'maoxianlgyzLevel_3': PosBtnTapModel("maoxianlgyzLevel_3", "六国远征-第三关", 924, 610),
    'maoxianlgyzLevel_4': PosBtnTapModel("maoxianlgyzLevel_4", "六国远征-第四关", 1273, 473),
    'maoxianlgyzLevel_5': PosBtnTapModel("maoxianlgyzLevel_5", "六国远征-第五关", 1723, 600),
    'maoxianlgyzLevel_6': PosBtnTapModel("maoxianlgyzLevel_6", "六国远征-第六关", 1500, 238),
    'maoxianlgyzLevel_1_case': PosBtnTapModel("maoxianlgyzLevel_1", "六国远征-第一关-宝箱", 828, 215),
    'maoxianlgyzLevel_2_case': PosBtnTapModel("maoxianlgyzLevel_2", "六国远征-第二关-宝箱", 860, 392),
    'maoxianlgyzLevel_3_case': PosBtnTapModel("maoxianlgyzLevel_3", "六国远征-第三关-宝箱", 1108, 671),
    'maoxianlgyzLevel_4_case': PosBtnTapModel("maoxianlgyzLevel_4", "六国远征-第四关-宝箱", 1470, 687),
    'maoxianlgyzLevel_5_case': PosBtnTapModel("maoxianlgyzLevel_5", "六国远征-第五关-宝箱", 1707, 377),
    'maoxianlgyzLevel_6_case': PosBtnTapModel("maoxianlgyzLevel_6", "六国远征-第六关-宝箱", 1311, 210),
}