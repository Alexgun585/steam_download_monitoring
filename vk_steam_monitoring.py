import time
import os
import re
import winreg
from datetime import datetime


def get_steam_path():
    """
    Поиск пути установки Steam
    """
    #  убрать ниже если указываются вручную
    # steam_path_manual = r"C:\Program Files (x86)\Steam" 
    steam_path_manual = ""   # это оставить пустым чтобы использовался поиск в реестре

    if steam_path_manual.strip():
        return os.path.normpath(steam_path_manual)

    possible_locations = [
        (winreg.HKEY_CURRENT_USER,   r"Software\Valve\Steam",           "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE,  r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE,  r"SOFTWARE\Valve\Steam",           "InstallPath"),
    ]

    for hive, reg_path, value_name in possible_locations:
        try:
            key = winreg.OpenKey(hive, reg_path)
            path, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return os.path.normpath(path)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Ошибка {reg_path}: {e}")
    print("Не удалось")
    return None


def parse_download_log(steam_path):
    log_file = os.path.join(steam_path, "logs", "content_log.txt")

    if not os.path.exists(log_file):
        return None, 0.0, "Лог-файл не найден"

    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-100:]
    except Exception as e:
        return None, 0.0, f"Ошибка чтения лога: {e}"

    game = None
    speed_mb_s = 0.0
    status = "Нет активной загрузки"

    for line in reversed(lines):
        # ищем название и скорость загрузки игры
        match = re.search(
            r"Downloading app \d+ : (.+?) : ([\d\.]+) ([KMG]?B)/s",
            line, re.IGNORECASE
        )
        if match:
            game_name, speed_str, unit = match.groups()
            game = game_name.strip('" ')
            
            try:
                speed_val = float(speed_str)
                unit = unit.upper()
                if unit == "KB":
                    speed_mb_s = speed_val / 1024
                elif unit == "MB":
                    speed_mb_s = speed_val
                elif unit == "GB":
                    speed_mb_s = speed_val * 1024
                else:
                    speed_mb_s = speed_val / 1024 / 1024
            except:
                speed_mb_s = 0.0

            status = "Загружается"
            break

        
        if any(x in line.lower() for x in ["download paused", "paused download", "on pause"]):
            status = "На паузе"

    return game, speed_mb_s, status


def main():
    steam_path = get_steam_path()
    if not steam_path:
        print("указать путь вручную")
        return

    print(f"Путь к steam: {steam_path}")
    print("Мониторинг 5 загрузок по 60 с\n")

    for i in range(1, 6):
        game, speed, status = parse_download_log(steam_path)
        now = datetime.now().strftime("%H:%M:%S")

        if game:
            print(f"[{i}/5] {now} | {game:<40} | {status:12} | {speed:6.2f} MB/s")
        else:
            print(f"[{i}/5] {now} | {'—':<40} | {status:12} | —")

        if i < 5:
            time.sleep(60)


if __name__ == "__main__":

    main()
