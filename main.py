import time
from selenium import webdriver
import re
from urllib.parse import unquote
import os
import sys
import requests
from tqdm import tqdm


def fetchID():
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
    choice = input("脚本无法判断表情类型，请自行判断原表情是否为动态表情？（Y/N）")
    if not os.path.exists(os.getcwd() + "/downloads"):
        os.mkdir(os.getcwd() + "/downloads")
    os.chdir(os.getcwd() + "/downloads")
    if choice == "Y":
        if not os.path.exists("[{}] {} (动态)".format(id, data["name"])):
            os.mkdir("[{}] {} (动态)".format(id, data["name"]))
        os.chdir("[{}] {} (动态)".format(id, data["name"]))
    else:
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


def check(id):
    infodataURI = "https://gxh.vip.qq.com/qqshow/admindata/comdata/vipEmoji_item_{}/xydata.json".format(
        id
    )
    infodata = requests.get(infodataURI).json()["data"]
    print(
        "[{}] {} - {}".format(
            id, infodata["baseInfo"][0]["name"], infodata["baseInfo"][0]["desc"]
        )
    )
    print("{}".format(infodata["baseInfo"][0]["tag"][0]))
    choice = input("是否继续下载？（Y/N）")
    if choice == "N":
        return
    elif choice == "Y":
        download(id)


if __name__ == "__main__":
    print(
        """
QQ 表情商城下载工具 V1.1 By @wowjerry
请选择操作：
1. 调用 selenium 获取表情 ID（请保证同目录下有与 Chrome 版本相同的 chromedriver.exe 文件）
2. 已知表情 ID，直接下载
"""
    )
    id = -1
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
