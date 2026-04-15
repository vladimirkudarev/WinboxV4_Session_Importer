import re
import json

def parse_wbx_structured(path):
    with open(path, "rb") as f:
        data = f.read()

    # вытаскиваем строки
    strings = re.findall(rb"[ -~]{3,}", data)
    strings = [s.decode("utf-8", errors="ignore") for s in strings]

    sessions = []
    current = {}

    for s in strings:
        if s.startswith("group"):
            # новая запись начинается
            if current:
                sessions.append(current)
                current = {}
            current["group"] = s[5:]

        elif s.startswith("host"):
            current["host"] = s[4:]

        elif s.startswith("login"):
            current["user"] = s[5:]

        elif s.startswith("pwd"):
            current["password"] = s[3:]

        elif s.startswith("note"):
            current["comment"] = s[4:]

    if current:
        sessions.append(current)

    return sessions


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")

    args = parser.parse_args()

    sessions = parse_wbx_structured(args.input)

    with open(args.output, "w") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

    print(f"[+] Parsed {len(sessions)} sessions")


if __name__ == "__main__":
    main()
                                                                                                                                                                                                                                   
