import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import logging
import json
import os

STATS_FILE = "stats.json"
ADMIN_ID = 123456789  # ← ВСТАВЬ СВОЙ TELEGRAM ID
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7708346934:AAHwtezftXup2vEczuRfabH-GMYPOM90v2w"

CSV_FILE = "mocktests.csv"

COL_PROVIDER = "Mock tests"
COL_FORMAT = "Online/Offline format"
COL_LANG = "Main foreign language"
COL_TEST = "Number of the test"
COL_BRANCH = "Branch"
COL_SECTOR = "sector"
COL_REG = "Regestration links"
COL_MAIN = "Main page links"

df = pd.read_csv(CSV_FILE)
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()


def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


LANG_KB = kb([["English","Русский"],["Azərbaycan dili"]])
FORMAT_KB = kb([["Online","Offline"],["all"]])
FOREIGN_KB = kb([["English","German","French"],["all"]])
TEST_KB = kb([["1","2","3"],["all"]])


TEXT = {

"English":{
"choose_lang":"Choose language",
"choose_mock":"Which mock test do you want to participate in?",
"choose_format":"Choose Online / Offline / all",
"choose_foreign":"Choose main foreign language",
"choose_test":"Choose test number",
"choose_branch":"Choose branch",
"choose_sector":"Choose sector",
"found":"Found",
"no":"No results found",
"done":"Done. Type /start to search again"
},

"Русский":{
"choose_lang":"Выберите язык",
"choose_mock":"Какой пробный экзамен вы хотите выбрать?",
"choose_format":"Выберите Online / Offline / all",
"choose_foreign":"Выберите основной иностранный язык",
"choose_test":"Выберите номер теста",
"choose_branch":"Выберите филиал",
"choose_sector":"Выберите сектор",
"found":"Найдено",
"no":"Ничего не найдено",
"done":"Готово. Напишите /start чтобы начать снова"
},

"Azərbaycan dili":{
"choose_lang":"Dil seçin",
"choose_mock":"Hansı sınaq imtahanında iştirak etmək istəyirsiniz?",
"choose_format":"Online / Offline / all seçin",
"choose_foreign":"Əsas xarici dili seçin",
"choose_test":"Test nömrəsini seçin",
"choose_branch":"Filialı seçin",
"choose_sector":"Sektoru seçin",
"found":"Tapıldı",
"no":"Nəticə tapılmadı",
"done":"/start yazaraq yenidən axtarın"
}

}


STATE_LANG = 0
STATE_PROVIDER = 1
STATE_FORMAT = 2
STATE_FOREIGN = 3
STATE_TEST = 4
STATE_BRANCH = 5
STATE_SECTOR = 6

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"users": []}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def track_user(user_id):
    stats = load_stats()
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
    save_stats(stats)
    
def text(context,key):
    lang = context.user_data.get("lang","English")
    return TEXT[lang][key]


def filter_all(data,col,val):

    v = val.lower()

    if v=="all":
        return data

    s = data[col].str.lower()

    return data[(s==v) | (s=="all")]


def provider_keyboard():

    providers = df[COL_PROVIDER].dropna().unique().tolist()

    rows=[]

    for p in providers:
        if p.lower()=="otk/mqm":
            continue
        rows.append([p])

    return kb(rows)


def branch_keyboard(data):

    branches=data[COL_BRANCH].dropna().unique().tolist()

    rows=[]

    for i in range(0,len(branches),2):
        rows.append(branches[i:i+2])

    rows.append(["all"])

    return kb(rows)


def sector_keyboard(data):

    sectors=data[COL_SECTOR].dropna().unique().tolist()

    rows=[]

    for i in range(0,len(sectors),2):
        rows.append(sectors[i:i+2])

    rows.append(["all"])

    return kb(rows)


def provider_filter(choice):

    c=choice.lower()

    if c=="otk":
        return df[df[COL_PROVIDER].str.lower().isin(["otk","otk/mqm"])]

    return df[df[COL_PROVIDER].str.lower()==c]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    logger.info(f"user {user_id} started")

    track_user(user_id)  # ← ВОТ ЭТО ДОБАВИЛИ

    context.user_data.clear()
    context.user_data["state"]=STATE_LANG

    await update.message.reply_text(
        "Choose language",
        reply_markup=LANG_KB
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text_msg=update.message.text
    state=context.user_data.get("state")


    if state==STATE_LANG:

        context.user_data["lang"]=text_msg
        context.user_data["state"]=STATE_PROVIDER

        await update.message.reply_text(
            text(context,"choose_mock"),
            reply_markup=provider_keyboard()
        )

        return


    if state==STATE_PROVIDER:

        data=provider_filter(text_msg)

        context.user_data["data"]=data

        if text_msg.lower()=="guvan":

            context.user_data["state"]=STATE_BRANCH

            await update.message.reply_text(
                text(context,"choose_branch"),
                reply_markup=branch_keyboard(data)
            )

        elif text_msg.lower()=="imza":

            context.user_data["state"]=STATE_SECTOR

            await update.message.reply_text(
                text(context,"choose_sector"),
                reply_markup=sector_keyboard(data)
            )

        else:

            context.user_data["state"]=STATE_FORMAT

            await update.message.reply_text(
                text(context,"choose_format"),
                reply_markup=FORMAT_KB
            )

        return


    if state==STATE_FORMAT:

        data=filter_all(context.user_data["data"],COL_FORMAT,text_msg)

        context.user_data["data"]=data
        context.user_data["state"]=STATE_FOREIGN

        await update.message.reply_text(
            text(context,"choose_foreign"),
            reply_markup=FOREIGN_KB
        )

        return


    if state==STATE_FOREIGN:

        data=filter_all(context.user_data["data"],COL_LANG,text_msg)

        context.user_data["data"]=data
        context.user_data["state"]=STATE_TEST

        await update.message.reply_text(
            text(context,"choose_test"),
            reply_markup=TEST_KB
        )

        return


    if state==STATE_TEST:

        data=filter_all(context.user_data["data"],COL_TEST,text_msg)

        await send_results(update,context,data)

        context.user_data.clear()

        return


    if state==STATE_BRANCH:

        data=filter_all(context.user_data["data"],COL_BRANCH,text_msg)

        await send_results(update,context,data)

        context.user_data.clear()

        return


    if state==STATE_SECTOR:

        data=filter_all(context.user_data["data"],COL_SECTOR,text_msg)

        await send_results(update,context,data)

        context.user_data.clear()

        return
        
async def stats_command(update, context):
    if update.effective_user.id != 7755680287:
        await update.message.reply_text("No access")
        return

    stats = load_stats()
    total = len(stats["users"])

    await update.message.reply_text(f"Unique users: {total}")


async def send_results(update,context,data):

    if data.empty:

        await update.message.reply_text(text(context,"no"))

    else:

        await update.message.reply_text(
            f"{text(context,'found')} {len(data)}"
        )

        for _,row in data.iterrows():

            if row[COL_PROVIDER].lower()=="imza":

                msg=f"""
{row[COL_PROVIDER]}

Registration:
{row[COL_REG]}
"""

            else:

                msg=f"""
{row[COL_PROVIDER]}

Main page:
{row[COL_MAIN]}

Registration:
{row[COL_REG]}
"""

            await update.message.reply_text(msg)


    await update.message.reply_text(
        text(context,"done"),
        reply_markup=ReplyKeyboardRemove()
    )


def main():

    app=ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle))

    print("Bot running...")

    app.run_polling()


if __name__=="__main__":
    main()
