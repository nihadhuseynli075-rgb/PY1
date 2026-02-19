import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ===========================
# 🔥 INSERT YOUR TOKEN HERE
# ===========================
TOKEN = "7708346934:AAHwtezftXup2vEczuRfabH-GMYPOM90v2w"

CSV_FILE = "mocktest.csv"

COL_PROVIDER = "Mock tests"
COL_FORMAT = "Online/Offline format"
COL_LANG = "Main foreign language"
COL_TESTNUM = "Number of the test"
COL_BRANCH = "Branch"
COL_REG = "Regestration links"
COL_MAINPAGE = "Main page links"


def load_table():
    df = pd.read_csv(CSV_FILE)
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
    return df


DF = load_table()

# STATES
S_UI_LANG = "ui_lang"
S_PROVIDER = "provider"
S_OTK_FORMAT = "otk_format"
S_OTK_LANG = "otk_lang"
S_OTK_TESTNUM = "otk_testnum"
S_GUVAN_BRANCH = "guvan_branch"


def norm(s):
    return (s or "").strip()


def low(s):
    return norm(s).lower()


def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


UI_LANG_KB = kb([["Русский", "Azərbaycan dili"], ["English"]])
PROVIDER_KB = kb([["OTK", "Guvan"]])
FORMAT_KB = kb([["Online", "Offline"], ["all"]])
DATA_LANG_KB = kb([["English", "German", "French"], ["all"]])
TEST_KB = kb([["1", "2", "3"], ["all"]])


TEXT = {
    "en": {
        "ask_ui": "Choose the bot language:",
        "ask_provider": "Which mock test do you want to participate in? (OTK or Guvan)",
        "ask_format": "Choose Online / Offline / all:",
        "ask_lang": "Choose main foreign language:",
        "ask_test": "Choose test number:",
        "ask_branch": "Choose branch:",
        "found": "Found {n} result(s):",
        "done": "Done. Type /start to search again.",
        "no": "No results found."
    },
    "ru": {
        "ask_ui": "Выбери язык бота:",
        "ask_provider": "В каком mock test хочешь участвовать? (OTK или Guvan)",
        "ask_format": "Выбери Online / Offline / all:",
        "ask_lang": "Выбери основной иностранный язык:",
        "ask_test": "Выбери номер теста:",
        "ask_branch": "Выбери филиал:",
        "found": "Найдено {n}:",
        "done": "Готово. Напиши /start чтобы начать заново.",
        "no": "Ничего не найдено."
    },
    "az": {
        "ask_ui": "Botun dilini seç:",
        "ask_provider": "Hansı mock test? (OTK və ya Guvan)",
        "ask_format": "Online / Offline / all seç:",
        "ask_lang": "Əsas xarici dili seç:",
        "ask_test": "Test nömrəsini seç:",
        "ask_branch": "Filialı seç:",
        "found": "{n} nəticə tapıldı:",
        "done": "Hazır. Yenidən başlamaq üçün /start yaz.",
        "no": "Heç nə tapılmadı."
    }
}


def t(context, key):
    lang = context.user_data.get("ui_lang", "en")
    return TEXT[lang][key]


def filter_provider(df, choice):
    p = low(choice)
    if p == "otk":
        return df[df[COL_PROVIDER].str.lower().isin(["otk", "otk/mqm"])]
    if p == "guvan":
        return df[df[COL_PROVIDER].str.lower() == "guvan"]
    return df


def apply_filter(df, col, value):
    v = low(value)
    if v == "all":
        return df
    s = df[col].astype(str).str.lower()
    return df[(s == v) | (s == "all")]


def branch_keyboard(df):
    branches = df[COL_BRANCH].dropna().unique().tolist()
    rows = []
    for i in range(0, len(branches), 2):
        rows.append(branches[i:i+2])
    rows.append(["all"])
    return kb(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["state"] = S_UI_LANG
    await update.message.reply_text("Choose language / Выбери язык / Dil seç:", reply_markup=UI_LANG_KB)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = norm(update.message.text)
    state = context.user_data.get("state")

    if state == S_UI_LANG:
        if low(text) in ["русский"]:
            context.user_data["ui_lang"] = "ru"
        elif low(text) in ["azərbaycan dili"]:
            context.user_data["ui_lang"] = "az"
        else:
            context.user_data["ui_lang"] = "en"

        context.user_data["state"] = S_PROVIDER
        await update.message.reply_text(t(context, "ask_provider"), reply_markup=PROVIDER_KB)
        return

    if state == S_PROVIDER:
        df = filter_provider(DF, text)
        context.user_data["df"] = df

        if low(text) == "otk":
            context.user_data["state"] = S_OTK_FORMAT
            await update.message.reply_text(t(context, "ask_format"), reply_markup=FORMAT_KB)
        else:
            context.user_data["state"] = S_GUVAN_BRANCH
            await update.message.reply_text(t(context, "ask_branch"), reply_markup=branch_keyboard(df))
        return

    if state == S_OTK_FORMAT:
        df = apply_filter(context.user_data["df"], COL_FORMAT, text)
        context.user_data["df"] = df
        context.user_data["state"] = S_OTK_LANG
        await update.message.reply_text(t(context, "ask_lang"), reply_markup=DATA_LANG_KB)
        return

    if state == S_OTK_LANG:
        df = apply_filter(context.user_data["df"], COL_LANG, text)
        context.user_data["df"] = df
        context.user_data["state"] = S_OTK_TESTNUM
        await update.message.reply_text(t(context, "ask_test"), reply_markup=TEST_KB)
        return

    if state == S_OTK_TESTNUM:
        df = apply_filter(context.user_data["df"], COL_TESTNUM, text)
        await send_results(update, context, df)
        return

    if state == S_GUVAN_BRANCH:
        df = apply_filter(context.user_data["df"], COL_BRANCH, text)
        await send_results(update, context, df)
        return


async def send_results(update, context, df):
    if df.empty:
        await update.message.reply_text(t(context, "no"))
    else:
        await update.message.reply_text(t(context, "found").format(n=len(df)))
        for _, row in df.iterrows():
            await update.message.reply_text(
                f"{row[COL_PROVIDER]} | {row[COL_BRANCH]}\n{row[COL_REG]}"
            )

    context.user_data.clear()
    await update.message.reply_text(t(context, "done"), reply_markup=ReplyKeyboardRemove())


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
