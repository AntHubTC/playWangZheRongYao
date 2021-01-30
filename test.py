import time

from device import DeviceEmulator

if __name__ == '__main__':
    device = DeviceEmulator()
    # device.tryBtnTap(btnName = 'duizhan', stage='main') # 对战
    # device.tryBtnTap(btnName = 'duizhan') # 对战
    # device.tryBtnTap('chuangguan')  # 闯关
    # device.tryBtnTap('baohujinshai')  # 闯关

    # device.doTryTapAction('maoxianlgyzLevel_1_case')
    # device.doTryTapAction('okBtnYellow')
    device.screenshot() # 截屏
    # print(device.recognitionImg('clickcontinue2'))
    # device.tryBtnTap('maoxianliuguoyuanzheng')



