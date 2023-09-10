import config
import database
from datetime import datetime
from openai_utils import GPT
from entry import Entry
from vectordb_utils import Index

from telegram import (
    Update,
    User,
    # InlineKeyboardButton,
    # InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    # CallbackQueryHandler,
    AIORateLimiter,
    filters
)
from telegram.constants import ParseMode

db = database.Database()

async def register_user_if_not_exists(update: Update, context: CallbackContext, user: User):
    if not db.check_if_user_exists(user.id):
        db.add_new_user(
            user.id,
            update.message.chat_id,
            username=user.username,
            first_name=user.first_name,
            last_name= user.last_name
        )
        db.start_new_dialog(user.id)

    if db.get_user_attribute(user.id, "current_dialog_id") is None:
        db.start_new_dialog(user.id)

async def start(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    dialog_id = db.get_user_attribute(user_id, "current_dialog_id")

    reply_message="Welcome to JournalGPT! This bot is designed to help you with your journal entries.\n"\
    "Start writing journals everyday with the help of entry prompts.\n"\
    "Get a summary of your entry.\n"\
    "Chat with your saved journals.\n"\
    "Use the following commands from the menu:\n\n"\

    "/write_journal: Start writing a new journal entry.\n"\
    "/show_summary: Get a summary with title of the most recent journal conversation.\n"\
    "/save_entry: Save the summary.\n"\
    "/ask_questions: Chat with your past self!"

    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML)



async def save_entry(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    dialog_id = db.get_user_attribute(user_id, "current_dialog_id")
    entry = db.get_entry(user_id, dialog_id)
    index = Index("journalgpt-index", user_id)
    result = index.push_to_index(entry)
    if result:
        db.set_entry_attribute(entry["_id"], "is_embedded", True)

    await update.message.reply_text("Entry saved to database successfully!", parse_mode=ParseMode.HTML)


async def show_summary(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    entry = Entry(user_id)
    title, summary = entry.create_summary()
    title_reply = title["choices"][0]["message"]["content"]
    summary_reply = summary["choices"][0]["message"]["content"]
    reply_message = f"{title_reply}\n\n{summary_reply}"

    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML)

async def write_journal(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    db.set_user_attribute(user_id, "current_chat_mode", "write_journal")
    db.start_new_dialog(user_id)

    reply_message="Welcome! What would you like to talk about today?"
    # update user data
    new_dialog_message = {"role": "assistant", "content": reply_message, "date": datetime.now()}
    db.set_dialog_messages(
        user_id,
        db.get_dialog_messages(user_id, dialog_id=None) + [new_dialog_message],
        dialog_id=None
    )
    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML)

async def ask_questions(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    db.set_user_attribute(user_id, "current_chat_mode", "ask_questions")

    reply_message="Welcome! You can now chat with your past self. What would you like to ask your past self?"

    await update.message.reply_text(reply_message, parse_mode=ParseMode.HTML)

async def message_handle(update: Update, context: CallbackContext, message=None, use_new_dialog_timeout=True):
    _message = message or update.message.text
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    chat_mode = db.get_user_attribute(user_id, "current_chat_mode")

    #TODO: Put modes in different functions
    if chat_mode=="ask_questions":
        index = Index("journalgpt-index", user_id)
        reply_text= index.get_answer(_message, user_id)

    if chat_mode=="write_journal":
        #TODO: Put the prompt in a template file
        journal_prompt = """
        Based on the given conversation, ask questions to the user based on the given context.
        """
        #TODO: Create a function out of updating dialog
        new_dialog_message = {"role": "user", "content": _message, "date": datetime.now()}
        updated_dialog_message= db.get_dialog_messages(user_id, dialog_id=None) + [new_dialog_message]
        db.set_dialog_messages(
            user_id,
            updated_dialog_message,
            dialog_id=None
        )
        gpt_instance= GPT(updated_dialog_message)
        reply_message = gpt_instance.get_message(journal_prompt)
        reply_text = reply_message["choices"][0]["message"]["content"]

        #TODO: Update with function for setting dialog
        new_dialog_message = {"role": "assistant", "content": reply_text, "date": datetime.now()}
        updated_dialog_message= db.get_dialog_messages(user_id, dialog_id=None) + [new_dialog_message]
        db.set_dialog_messages(
            user_id,
            updated_dialog_message,
            dialog_id=None
        )

    await update.message.chat.send_action(action="typing")
    #TODO: TESTING
    # await update.message.reply_text([message["content"] for message in updated_dialog_message], parse_mode=ParseMode.HTML)
    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

    # async def message_handle_fn():
    #     chat_mode = db.get_user_attribute(user_id, "current_chat_mode")

    #     try:
    #         # send placeholder message to user
    #         placeholder_message = await update.message.reply_text("...")
            
    #         dialog_messages = db.get_dialog_messages(user_id, dialog_id=None)
            
    #         parse_mode = {
    #             "html": ParseMode.HTML,
    #             "markdown": ParseMode.MARKDOWN
    #         }[config.chat_modes[chat_mode]["parse_mode"]]
            
    #         redditgpt_instance = langchain_utils.RedditGPT(model=current_model)
            
    #         if chat_mode=='QA' and not is_url:
    #             answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed = await redditgpt_instance.send_qa_response(
    #                 _message,
    #                 dialog_messages=dialog_messages,
    #                 user_id = user_id,
    #                 chat_mode=chat_mode
    #             )
    #             async def fake_gen():
    #                 yield "finished", answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed

    #             gen = fake_gen()
    #         else:
    #             gen = redditgpt_instance.send_message(
    #                 _message,
    #                 dialog_messages=dialog_messages,
    #                 user_id=user_id,
    #                 chat_mode=chat_mode,
    #                 is_url = is_url
    #             )

    #         prev_answer = ""
    #         async for gen_item in gen:
    #             status, answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed = gen_item
                
    #             answer = answer[:4096]  # telegram message limit

    #             # update only when 100 new symbols are ready
    #             if abs(len(answer) - len(prev_answer)) < 100 and status != "finished":
    #                 continue

    #             try:
    #                 await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=parse_mode)
    #             except telegram.error.BadRequest as e:
    #                 if str(e).startswith("Message is not modified"):
    #                     continue
    #                 else:
    #                     await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)

    #             await asyncio.sleep(0.01)  # wait a bit to avoid flooding

    #             prev_answer = answer

    #         # update user data
    #         new_dialog_message = {"user": _message, "bot": answer, "date": datetime.now()}
    #         db.set_dialog_messages(
    #             user_id,
    #             db.get_dialog_messages(user_id, dialog_id=None) + [new_dialog_message],
    #             dialog_id=None
    #         )

    #         db.update_n_used_tokens(user_id, current_model, n_input_tokens, n_output_tokens)

    #     except Exception as e:
    #         error_text = f"Something went wrong during completion. Reason: {e}"
    #         logger.error(error_text)
    #         await update.message.reply_text(error_text)
    #         return

#TODO: add a command for /start
async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/start", "Introduction"),
        BotCommand("/write_journal", "Start writing a new journal entry"),
        BotCommand("/show_summary", "Show the summary and save the entry"),
        BotCommand("/save_entry", "Save the entry to database"),
        BotCommand("/ask_questions", "Chat with your journal entries")
    ])

def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .post_init(post_init)
        .build()
    )

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ALL, message_handle))

    application.add_handler(CommandHandler("start", start, filters=filters.ALL))
    application.add_handler(CommandHandler("write_journal", write_journal, filters=filters.ALL))
    application.add_handler(CommandHandler("show_summary", show_summary, filters=filters.ALL))
    application.add_handler(CommandHandler("save_entry", save_entry, filters=filters.ALL))
    application.add_handler(CommandHandler("ask_questions", ask_questions, filters=filters.ALL))


    # start the bot
    application.run_polling()


if __name__ == "__main__":
    run_bot()