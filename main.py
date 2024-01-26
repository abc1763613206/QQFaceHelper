import time
from selenium import webdriver
import re
from urllib.parse import unquote
import os
import sys
import requests
from tqdm import tqdm

DynamicFlag = False
NoPromptFlag = False


def fetchID():
    print("进入模拟浏览器流程，请确保同目录下有与 Chrome 版本相同的 chromedriver 文件")
    mobile_emulation = {
        "deviceMetrics": {
            "width": 720,
            "height": 1080,
            "pixelRatio": 1.75,
            "touch": True,
            "mobile": True,
        },
        "clientHints": {
            "platform": "Android",
            "mobile": True,
        },
        "userAgent": "Mozilla/5.0 (Linux; Android 13; 2206122SC Build/TKQ1.220829.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/109.0.5414.86 MQQBrowser/6.2 TBS/046613 Mobile Safari/537.36 V1_AND_SQ_8.9.80_4614_YYB_D QQ/8.9.80.12440 NetType/WIFI WebP/0.3.0 AppId/537176868 Pixel/1080 StatusBarHeight/82 SimpleUISwitch/0 QQTheme/1000 StudyMode/0 CurrentMode/0 CurrentFontScale/1.0 GlobalDensityScale/1.0 AllowLandscape/false InMagicWin/0",
    }  # 8.9.80 QQ 自带 UA
    options = webdriver.ChromeOptions()
    caps = webdriver.DesiredCapabilities.CHROME
    caps["goog:loggingPrefs"] = {"performance": "ALL"}
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    # 正常 UA 情况下会跳转登录页，而不是二维码扫描页
    driver = webdriver.Chrome(options=options, desired_capabilities=caps)
    driver.get(
        "https://zb.vip.qq.com/hybrid/emoticonmall/search?_wv=1027&appid=1"
    )  # QQ 表情商城搜索页
    print("QQ 登录页可能无法响应「登录」按钮操作，此时您可以尝试在输入好账号密码后，在密码框手动 Enter 回车...")
    while True:
        dat = driver.get_log("browser")
        for i in dat:
            if "jsbridge://ui/openUrl?" in i["message"]:
                txt = unquote(i["message"], "utf-8")
                match = re.match('.*id=(\d+)"', txt)
                if match:
                    print("成功发现 ID " + match.group(1))
                    driver.quit()
                    return match.group(1)
        time.sleep(0.5)


def download(id):
    widthURI = "https://gxh.vip.qq.com/club/item/parcel/{}/{}_android.json".format(
        str(id)[-1:], id
    )
    data = requests.get(widthURI).json()
    height = data["supportSize"][0]["Height"]
    width = data["supportSize"][0]["Width"]
    print("表情尺寸：{}x{}".format(width, height))
    type = data["type"]
    cnt = data["imgs"].__len__()
    print("表情数量：{}".format(cnt))
    if NoPromptFlag == False:
        choice = input("脚本无法判断表情类型，请自行判断原表情是否为动态表情？（Y/N）")
    else:
        if DynamicFlag == True:
            choice = "Y"
        else:
            choice = "N"
    if not os.path.exists(os.getcwd() + "/downloads"):
        os.mkdir(os.getcwd() + "/downloads")
    os.chdir(os.getcwd() + "/downloads")
    if choice == "Y" or choice == "y":
        print("已选择下载动态表情")
        if not os.path.exists("[{}] {} (动态)".format(id, data["name"])):
            os.mkdir("[{}] {} (动态)".format(id, data["name"]))
        os.chdir("[{}] {} (动态)".format(id, data["name"]))
    else:
        print("已选择下载静态表情")
        if not os.path.exists("[{}] {}".format(id, data["name"])):
            os.mkdir("[{}] {}".format(id, data["name"]))
        os.chdir("[{}] {}".format(id, data["name"]))
    plist = tqdm(data["imgs"])
    for i in plist:
        if choice == "Y":
            imgURI = (
                "https://gxh.vip.qq.com/club/item/parcel/item/{}/{}/raw{}.gif".format(
                    i["id"][0:2], i["id"], height
                )
            )
            img = requests.get(imgURI)
            # print("{} - {} {}".format(i["name"], i["id"], img.status_code))
            with open("{}.gif".format(i["name"]), "wb") as f:
                f.write(img.content)
        else:
            imgURI = (
                "https://gxh.vip.qq.com/club/item/parcel/item/{}/{}/{}x{}.png".format(
                    i["id"][0:2], i["id"], height, width
                )
            )
            img = requests.get(imgURI)
            # print("{} - {} {}".format(i["name"], i["id"], img.status_code))
            with open("{}.png".format(i["name"]), "wb") as f:
                f.write(img.content)
    print("下载完成！保存路径：{}".format(os.getcwd()))


def check(id):
    infodataURI = "https://gxh.vip.qq.com/qqshow/admindata/comdata/vipEmoji_item_{}/xydata.json".format(
        id
    )
    try:
        infodataRAW = requests.get(infodataURI)
        infodata = infodataRAW.json()["data"]
    except Exception as e:
        print("请求错误！" + str(e))
        print(infodataRAW.status_code)
        sys.exit()
    print(
        "[{}] {} - {}".format(
            id, infodata["baseInfo"][0]["name"], infodata["baseInfo"][0]["desc"]
        )
    )
    print("{}".format(infodata["baseInfo"][0]["tag"][0]))
    if NoPromptFlag == False:
        choiceFlag = False
        choice = input("是否继续下载？（Y/N）")
        while not choiceFlag:
            if choice == "N" or choice == "n":
                choiceFlag = True
                return
            elif choice == "Y" or choice == "y":
                choiceFlag = True
                download(id)
            else:
                choice = input("输入错误，请重新输入：（Y/N）")
    else:
        download(id)


if __name__ == "__main__":
    id = -1
    if len(sys.argv) == 2:
        id = sys.argv[1]
        try:
            assert id.isdigit()
        except AssertionError:
            print("参数错误，退出...")
            print("命令行使用方法：python main.py [表情 ID] [参数(--dynamic/--static)(可选)])")
            sys.exit()
        id = int(id)
        print("已检测到参数，直接下载 ID {}".format(id))
    elif len(sys.argv) == 3:
        id = sys.argv[1]
        try:
            assert id.isdigit()
        except AssertionError:
            print("参数错误，退出...")
            print("命令行使用方法：python main.py [表情 ID] [参数(--dynamic/--static)(可选)])")
            sys.exit()
        id = int(id)
        if sys.argv[2] == "--dynamic":
            print("已检测到参数，下载动态表情 ID {}".format(id))
            DynamicFlag = True
            NoPromptFlag = True
        elif sys.argv[2] == "--static":
            print("已检测到参数，下载静态表情 ID {}".format(id))
            DynamicFlag = False
            NoPromptFlag = True
        else:
            print("参数错误，退出...")
            print("命令行使用方法：python main.py [表情 ID] [参数(--dynamic/--static)(可选)])")
            sys.exit()
    else:
        print(
            """
QQ 表情商城下载工具 V1.2 By @wowjerry
请选择操作：
1. 调用 selenium 获取表情 ID（请保证同目录下有与 Chrome 版本相同的 chromedriver.exe 文件）
2. 已知表情 ID，直接下载

开源地址：https://github.com/abc1763613206/QQFaceHelper
命令行使用方法： python main.py [表情 ID] [参数(--dynamic/--static)(可选)])
"""
        )
        try:
            choice = input("请输入操作序号：")
        except Exception as e:
            print(e)
            sys.exit()
        if choice == "1":
            id = fetchID()
        elif choice == "2":
            id = input("请输入表情 ID：")
        else:
            print("输入错误，退出...")
            sys.exit()
    check(id)
