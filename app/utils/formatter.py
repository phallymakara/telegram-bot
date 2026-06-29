def format_usd(value: float) -> str:
    """
    Format USD value.
    Example:
    10.0 -> 10$
    10.5 -> 10.5$
    10.25 -> 10.25$
    """
    if value == int(value):
        return f"{int(value)}$"

    text = f"{value:.2f}"

    if text.endswith("0"):
        text = text[:-1]

    return f"{text}$"


def format_riel(value: float) -> str:
    """
    Format Khmer Riel.
    Example:
    80000 -> 80k
    75500 -> 75500
    """
    riel = int(round(value))

    if riel >= 1000 and riel % 1000 == 0:
        return f"{riel // 1000}k"

    return f"{riel}"


def get_num_emoji(index: int) -> str:
    """
    Convert number to emoji number.
    Example:
    1 -> 1️⃣
    10 -> 🔟
    12 -> 1️⃣2️⃣
    """
    emojis = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
        10: "🔟",
    }

    if index in emojis:
        return emojis[index]

    result = ""

    for char in str(index):
        result += char + "️⃣"

    return result