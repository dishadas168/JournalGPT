from typing import List
import math
import re
import tiktoken 

OPEN_AI_CHAT_TYPE = "OpenAI Chat"
OPEN_AI_INSTRUCT_TYPE = "OpenAI Instruct"

def estimate_word_count(num_tokens: int) -> int:
    """
    Given the number of GPT-2 tokens, estimates the real word count.
    """
    # The average number of real words per token for GPT-2 is 0.56, according to OpenAI.
    # Multiply the number of tokens by this average to estimate the total number of real
    # words.
    return math.ceil(num_tokens * 0.56)

def num_tokens_from_string(string: str, model_type: str = OPEN_AI_CHAT_TYPE) -> int:
    """
    Returns the number of tokens in a text string.
    NOTE: openAI and Anthropics have different token counting mechanisms.
    https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
    """

    num_tokens = len(tiktoken.get_encoding("p50k_base").encode(string))
    return num_tokens

def group_bodies_into_chunks(contents: str, token_length: int) -> List[str]:
    """
    Concatenate the content lines into a list of newline-delimited strings
    that are less than token_length tokens long.
    """
    results: List[str] = []
    current_chunk = ""

    for line in contents.split("\n"):
        line = re.sub(r"\n+", "\n", line).strip()
        line = line[: estimate_word_count(1000)] + "\n"

        if num_tokens_from_string(current_chunk + line) > token_length:
            results.append(current_chunk)
            current_chunk = ""

        current_chunk += line

    if current_chunk:
        results.append(current_chunk)

    return results