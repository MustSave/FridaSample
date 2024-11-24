import os
import subprocess
import platform
from var import *

def get_focused_app_package():
    """
    현재 포커스된 앱의 패키지 이름을 반환합니다.

    Returns:
        str: 포커스된 앱의 패키지 이름 (없으면 None)
    """
    try:
        # adb shell dumpsys activity 명령 실행
        result = subprocess.run(["adb", "shell", "dumpsys", "activity"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        # 에러가 발생한 경우
        if result.returncode != 0:
            print(f"Error executing adb: {result.stderr}")
            return None

        # 출력 결과를 줄 단위로 분리
        dump = result.stdout.splitlines()

        # mFocusedWindow를 포함하는 줄 필터링
        focused = [line.strip() for line in dump if "mFocusedWindow" in line]
        if focused:
            # mFocusedWindow에서 패키지 이름 추출
            line = focused[0]
            if '=' in line:
                window_info = line.split('=')[1].strip()  # '=' 뒤의 정보 추출
                if '/' in window_info:
                    package_name = window_info.split('/')[0]  # '/' 이전의 패키지 이름 추출
                    package_name = package_name.split()[-1]
                    print(f"Package name: {package_name}")
                    return package_name
                else:
                    print("Could not find a package name.")
            else:
                print("Could not parse the focused window information.")
        else:
            print("No focused window found.")
            return None

    except FileNotFoundError:
        print("Error: adb command not found. Ensure Android SDK is installed and in PATH.")
        return None

def run_command_in_background(command):
    """
    플랫폼에 따라 주어진 명령어를 백그라운드에서 실행하는 함수.

    Args:
        command (str): 실행할 명령어
    """
    system_platform = platform.system()

    try:
        if system_platform == "Windows":
            # Windows에서는 subprocess.Popen 사용
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # macOS 및 Linux에서는 쉘 백그라운드 명령 실행
            subprocess.Popen(f"{command} > /dev/null 2>&1 &", shell=True, executable="/bin/bash")
        print(f"Command started in background: {command}")
    except Exception as e:
        print(f"Failed to execute command: {e}")

def setup_android_path_env():
    global android_sdk_path

    # OS에 따라 Android SDK 경로 설정
    system_platform = platform.system()  # 운영 체제 이름 반환

    if system_platform == "Darwin":  # macOS
        android_sdk_path = "~/Library/Android/sdk"
    elif system_platform == "Linux":  # Linux
        android_sdk_path = "~/Android/Sdk"
    elif system_platform == "Windows":  # Windows
        android_sdk_path = "~/AppData/Local/Android/Sdk"
    else:
        raise EnvironmentError(
            f"Unsupported platform: {system_platform}. "
            "Please ensure the Android Emulator path is set manually."
        )

    # 경로를 절대 경로로 확장
    android_sdk_path = os.path.expanduser(android_sdk_path)

    # SDK 경로 확인
    if not os.path.exists(android_sdk_path):
        raise FileNotFoundError(f"The Android SDK was not found at {android_sdk_path}.")

    # 신버전 경로 우선 확인
    android_emulator_path_new = os.path.join(android_sdk_path, "emulator")
    tools_path_new = os.path.join(android_sdk_path, "cmdline-tools", "latest", "bin")

    # 구버전 경로 확인
    android_emulator_path_old = os.path.join(android_sdk_path, "tools", "emulator")
    tools_path_old = os.path.join(android_sdk_path, "tools", "bin")

    # Emulator 경로 설정
    if os.path.exists(android_emulator_path_new):
        android_emulator_path = android_emulator_path_new
    elif os.path.exists(android_emulator_path_old):
        android_emulator_path = android_emulator_path_old
    else:
        raise FileNotFoundError("The Android Emulator binary was not found in either new or old SDK structure.")

    # tools 경로 설정
    if os.path.exists(tools_path_new):
        tools_path = tools_path_new
    elif os.path.exists(tools_path_old):
        tools_path = tools_path_old
    else:
        raise FileNotFoundError("The tools path was not found in either new or old SDK structure.")

    # build-tools 경로 설정 (가장 높은 버전)
    build_tools_dir = os.path.join(android_sdk_path, "build-tools")
    if not os.path.exists(build_tools_dir):
        raise FileNotFoundError(f"The build-tools directory was not found at {build_tools_dir}.")

    build_tool_versions = [
        d for d in os.listdir(build_tools_dir) 
        if os.path.isdir(os.path.join(build_tools_dir, d))
    ]
    if not build_tool_versions:
        raise FileNotFoundError("No build-tools versions found.")
    
    # 가장 높은 버전 선택
    highest_build_tool_version = max(build_tool_versions, key=lambda v: list(map(int, v.split('.'))))
    build_tools_path = os.path.join(build_tools_dir, highest_build_tool_version)

    # 환경변수 PATH에 tools, emulator, build-tools 경로 추가
    current_path = os.environ.get("PATH", "")
    paths_to_add = [tools_path, android_emulator_path, build_tools_path]
    for path in paths_to_add:
        if path not in current_path:
            os.environ["PATH"] = f"{path}{os.pathsep}{os.environ['PATH']}"


    # 모든 경로 출력
    print("Android SDK Path:", android_sdk_path)
    print("Android Emulator Path:", android_emulator_path)
    print("Tools Path Added to PATH:", tools_path)
    print("Build Tools Path Added to PATH:", build_tools_path)