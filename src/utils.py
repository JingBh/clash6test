import re


# Reference: https://stackoverflow.com/a/49986645/18176440
def remove_emojis(text: str) -> str:
    regrex_pattern = re.compile("["
                                "\U0001F600-\U0001F64F"  # emoticons
                                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                                "\U0001F680-\U0001F6FF"  # transport & map symbols
                                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)
