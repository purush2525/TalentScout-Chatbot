import re

def mask_contact(s: str) -> str:
    if not s:
        return s
    # mask emails
    if "@" in s:
        name, _, domain = s.partition("@")
        name_mask = name[0] + "***" if name else "***"
        return f"{name_mask}@{domain}"
    # mask phone digits
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 4:
        return "***" + digits[-4:]
    return "***"
