mport json
import subprocess
import time
import sys
import shutil
import os

# 1. Проверка системных зависимостей (xdotool и xclip)
def check_dependencies():
    deps = ["xdotool", "xclip"]
    missing = [d for d in deps if shutil.which(d) is None]
    if missing:
        print(f"❌ Ошибка: В системе не найдены утилиты: {', '.join(missing)}")
        print("💡 Установите их командой:")
        print("   Arch: sudo pacman -S xdotool xclip")
        print("   Debian/Ubuntu: sudo apt install xdotool xclip")
        sys.exit(1)

# 2. Загрузка карты табуляции из TabMap.txt
def get_tab_steps(map_file):
    mapping = {}
    if not os.path.exists(map_file):
        print(f"❌ Ошибка: Файл карты переходов '{map_file}' не найден.")
        print("💡 Создайте файл TabMap.txt с разметкой полей Winbox.")
        sys.exit(1)
        
    try:
        with open(map_file, "r", encoding="utf-8") as f:
            for line in f:
                if "." in line:
                    parts = line.split(".", 1)
                    idx = int(parts[0].strip())
                    name = parts[1].strip().lower()
                    mapping[name] = idx
        return mapping
    except Exception as e:
        print(f"❌ Ошибка чтения {map_file}: {e}")
        sys.exit(1)

# 3. Функция вставки через буфер обмена
def paste_text(text):
    if text is not None:
        try:
            # Копируем текст в буфер обмена через xclip
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(input=str(text).encode('utf-8'))
            # Эмулируем нажатие Ctrl+V для вставки
            subprocess.run(["xdotool", "key", "ctrl+v"])
            time.sleep(0.15) # Пауза для стабильности Winbox
        except Exception as e:
            print(f"⚠ Ошибка вставки текста: {e}")

# 4. Функция для перехода между полями через Tab
def press_tab(count):
    if count > 0:
        for _ in range(count):
            subprocess.run(["xdotool", "key", "Tab"])
            time.sleep(0.05)

# --- ПОДГОТОВКА И ПРОВЕРКИ ---
check_dependencies()

# Выбор файла данных: 
# 1. Из аргумента (python script.py my.json)
# 2. По умолчанию session.json (как в вашем списке файлов)
# 3. По умолчанию sessions.json
if len(sys.argv) > 1:
    session_file = sys.argv[1]
elif os.path.exists("session.json"):
    session_file = "session.json"
else:
    session_file = "sessions.json"

try:
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[+] Файл '{session_file}' успешно загружен.")
except FileNotFoundError:
    print(f"❌ Ошибка: Файл данных не найден (проверены аргументы, session.json и sessions.json).")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"❌ Ошибка: Файл '{session_file}' имеет неверный формат JSON.")
    sys.exit(1)

if not data:
    print(f"⚠ Файл '{session_file}' не содержит данных для импорта.")
    sys.exit(0)

# Загружаем карту переходов
tab_map = get_tab_steps("TabMap.txt")

# Рассчитываем прыжки (количество нажатий Tab) между ключевыми полями
# Если ключа нет в TabMap, используются стандартные значения для Winbox v4
steps = {
    "to_login": tab_map.get("login", 2) - tab_map.get("connect to", 1),
    "to_pass": tab_map.get("password", 3) - tab_map.get("login", 2),
    "to_group": tab_map.get("group", 11) - tab_map.get("password", 3),
    "to_comment": tab_map.get("comment", 12) - tab_map.get("group", 11),
    "to_save": tab_map.get("save to list", 13) - tab_map.get("comment", 12),
    "return_home": 15 # Фиксированный прыжок для возврата в начало списка
}

# --- ПРОВЕРКА ПРИВИЛЕГИЙ СИСТЕМЫ ---
print("\n[!] Проверка доступности xdotool...")
subprocess.run(["xdotool", "key", "shift"]) 
time.sleep(0.5)

print("\n" + "!"*60)
print(" ИНСТРУКЦИЯ:")
print(" 1. Откройте Winbox v4.")
print(" 2. Установите КУРСОР в поле 'Connect To' (самое первое поле).")
print(" 3. Вернитесь сюда и нажмите ENTER.")
print("!"*60)

input("\nНажмите ENTER для начала обратного отсчета...")

# Финальная пауза для переключения окна
for i in range(10, 0, -1):
    sys.stdout.write(f"\r[!] Начало через {i} сек... Переключитесь на Winbox! ")
    sys.stdout.flush()
    time.sleep(1)
print("\n[+*+] ПОЕХАЛИ!\n")

# --- ОСНОВНОЙ ЦИКЛ ИМПОРТА ---
for i, s in enumerate(data):
    current_host = s.get("host", "Unknown")
    print(f"[{i+1}/{len(data)}] Импорт: {current_host}          ", end="\r")
    
    try:
        # 1. Ввод Host (Connect To)
        paste_text(s.get("host", ""))
        press_tab(steps["to_login"])
        
        # 2. Ввод Login
        paste_text(s.get("user", "admin"))
        press_tab(steps["to_pass"])
        
        # 3. Ввод Password
        paste_text(s.get("password", ""))
        press_tab(steps["to_group"])
        
        # 4. Ввод Group
        paste_text(s.get("group", ""))
        press_tab(steps["to_comment"])
        
        # 5. Ввод Comment
        paste_text(s.get("comment", ""))
        press_tab(steps["to_save"])
        
        # 6. Нажатие кнопки 'Add/Save'
        subprocess.run(["xdotool", "key", "Return"])
        
        # Ожидание записи и возврат в начало формы
        time.sleep(0.8)
        press_tab(steps["return_home"])
        
    except Exception as e:
        print(f"\n❌ Ошибка на хосте {current_host}: {e}")
        subprocess.run(["xdotool", "key", "Escape"]) 
        time.sleep(1)
        continue

print("\n\n[+] ГОТОВО! Все сессии обработаны.")
                                                  
