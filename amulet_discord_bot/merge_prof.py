import gzip
import re


def main() -> None:
    with open("prof_database", encoding="utf-8") as f:
        prof_in = [l.strip().lower() for l in f.readlines() if l.strip()]
    prof = []
    for l in prof_in:
        prof.append(l)
        if not l.endswith("s"):
            prof.append(f"{l}s")
    prof = sorted(set(prof))
    with open("prof_database", "w", encoding="utf-8") as f:
        f.write("\n".join(prof))
    prof = [re.escape(l) for l in prof]
    with gzip.open("prof", "wb") as f:
        f.write(("(^| )(" + "|".join(prof) + ")( |\\.|$)").encode("utf-8"))


if __name__ == "__main__":
    main()
