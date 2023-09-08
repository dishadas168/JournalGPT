from openai_utils import GPT
import database
import uuid

db = database.Database()

class Entry:
    def __init__(self, user_id):
        self.dialog_id=db.get_user_attribute(user_id, "current_dialog_id")
        self.messages=db.get_dialog_messages(user_id, self.dialog_id)
        self.start_time=self.messages[0]["date"]
        self.end_time=self.messages[-1]["date"]
        self.entry_date=self.start_time.date()
        self.summary=""
        self.title=""
        self.isEmbedded=False

    def create_summary(self):

        summary_prompt = """ """
        title_prompt = """ """
        gpt_instance = GPT(self.messages)
        summary = gpt_instance.get_message(summary_prompt)
        title = gpt_instance.get_message(title_prompt)
        self.summary=summary
        self.title=title
        self.save_entry()
        return summary

    def save_entry(self):
        db.add_new_entry(
            start_time= self.start_time,
            end_time=self.end_time,
            entry_date=self.entry_date,
            summary= self.summary,
            title= self.title,
            dialog_id=self.dialog_id,
            isEmbedded=self.isEmbedded
        )



    