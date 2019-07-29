# 明日方舟辅助

明日方舟安卓客户端自动刷图

## Installation

### Install adb

Ubuntu:

```
> sudo apt install android-tools-adb
```

### Test adb

连接手机

```
> adb devices
List of devices attached
DXLNW***********	device
```

### Install python requirements

```
> pip3 install -r requirements.txt
```

## Usage

### Settings

设置执行次数： 修改 `main.py` 中 `play_times` 

### Run

1. 选择关卡，不要点“开始行动”

2. 运行辅助 `python3 main.py`

