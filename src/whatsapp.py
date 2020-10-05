import pandas as pd


MESSAGE_COMPONENTS = ["Time", "User", "Message"]


def split_chat_line_into_message_components(line):
    time, rest = line.split(" - ")
    user, message = rest.split(": ")
    return pd.Series([time, user, message], index=MESSAGE_COMPONENTS)


def raw_chat_to_message_components(chat_file_name):
    chat = pd.DataFrame(columns=MESSAGE_COMPONENTS)

    HEADER_LINES = 3
    with open(chat_file_name, "r", encoding="utf8") as f:
        i = 0
        for line in f:
            if i < HEADER_LINES:
                i += 1
                continue
            chat = chat.append(split_chat_line_into_message_components(line), ignore_index=True)

    return chat


def process_chat_components(chat_components):
    chat_components["Time"] = chat_components["Time"].astype("datetime64")
    chat_components["Message"] = chat_components["Message"].str.strip()
    return chat_components


def read_chat(chat_file_name):
    chat_components = raw_chat_to_message_components(chat_file_name)
    chat = process_chat_components(chat_components)
    return chat
