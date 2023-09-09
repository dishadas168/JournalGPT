from openai_utils import GPT
import database
import uuid

db = database.Database()

class Entry:
    def __init__(self, user_id):
        self.user_id=user_id
        self.dialog_id=db.get_user_attribute(user_id, "current_dialog_id")
        self.messages=db.get_dialog_messages(user_id, self.dialog_id)
        self.start_time=self.messages[0]["date"]
        self.end_time=self.messages[-1]["date"]
        self.entry_date=self.start_time.date()
        self.summary=""
        self.title=""
        self.is_embedded=False

    def create_summary(self):
        #TODO: Send these prompts to a template file
        summary_prompt = """Given a dialog between a user and assistant. 
        Imagine you are the user. Please create a summary of the contents from the user speaking in first person.
        Make it look like it's a page from a journal entry."""

        #TODO: Modify prompt to remove the word "Title" from the title.
        title_prompt = """Given a dialog between a user and assistant,  please create a title for the contents from the user.
        Make it look like it's a title for a journal entry written by the user."""
        gpt_instance = GPT(self.messages)
        summary = gpt_instance.get_message(summary_prompt)
        title = gpt_instance.get_message(title_prompt)
        self.summary=summary
        self.title=title
        self.save_entry()
        return title, summary

    def save_entry(self):
        db.add_new_entry(
            user_id=self.user_id,
            start_time= str(self.start_time),
            end_time=str(self.end_time),
            entry_date=str(self.entry_date),
            summary= self.summary,
            title= self.title,
            dialog_id=self.dialog_id,
            is_embedded=self.is_embedded
        )



    