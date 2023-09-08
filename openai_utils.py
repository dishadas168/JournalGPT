import openai
import config


# setup openai
openai.api_key = config.openai_api_key
if config.openai_api_base is not None:
    openai.api_base = config.openai_api_base

OPENAI_COMPLETION_OPTIONS = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "request_timeout": 60.0,
}

class GPT:
    def __init__(self, dialog_messages):
        self.model="gpt-3.5-turbo"
        self.dialog_messages=dialog_messages
    
    def get_message(self, prompt):
        messages= self.generate_prompt_messages(prompt)
        answer = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            **OPENAI_COMPLETION_OPTIONS
        ) 
        return answer

    def generate_prompt_messages(self, prompt):
        messages = [{"role": "system", "content": prompt}]
        for dialog_message in self.dialog_messages:
            messages.append({"role": "user", "content": dialog_message["user"]})
            messages.append({"role": "assistant", "content": dialog_message["bot"]})
        return messages

    # def send_message(self, message, dialog_messages=[], chat_mode="assistant", is_url = False):
    #     if chat_mode not in config.chat_modes.keys():
    #         raise ValueError(f"Chat mode {chat_mode} is not supported")

    #     n_dialog_messages_before = len(dialog_messages)
    #     answer = None
    #     while answer is None:
    #         try:
    #                 if is_url: #If reddit url
    #                     messages = self._generate_prompt_for_thread(message, chat_mode, user_id)
    #                 else:
    #                     messages = self._generate_prompt_messages(message, dialog_messages, chat_mode)

    #                 r_gen = await openai.ChatCompletion.acreate(
    #                     model=self.model,
    #                     messages=messages,
    #                     stream=True,
    #                     **OPENAI_COMPLETION_OPTIONS
    #                 )

    #                 answer = ""
    #                 async for r_item in r_gen:
    #                     delta = r_item.choices[0].delta
    #                     if "content" in delta:
    #                         answer += delta.content
    #                         n_input_tokens, n_output_tokens = self._count_tokens_from_messages(messages, answer, model=self.model)
    #                         n_first_dialog_messages_removed = n_dialog_messages_before - len(dialog_messages)
    #                         yield "not_finished", answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed

    #             else:
    #                 raise ValueError(f"Unknown model: {self.model}")

    #             answer = self._postprocess_answer(answer)
    #         except openai.error.InvalidRequestError as e:  # too many tokens
    #             if len(dialog_messages) == 0:
    #                 raise ValueError("Dialog messages is reduced to zero, but still has too many tokens to make completion") from e

    #             # forget first message in dialog_messages
    #             dialog_messages = dialog_messages[1:]

    #     n_first_dialog_messages_removed = n_dialog_messages_before - len(dialog_messages)

    #     yield "finished", answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed
    

