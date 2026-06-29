from telegram import Update
from telegram.ext import ContextTypes

from app.database.repository import record_borrow
from app.services.salary import calculate_borrow_deduction, calculate_debt


async def borrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Record employee borrow amount.

    Command:
    /borrow employee_name amount

    Example:
    /borrow ប៉ែន ទិត្យ 250000
    """
    args = context.args

    if len(args) < 2:
        await update.message.reply_html(
            "<b>Copy and edit the template below to record borrow:</b>\n\n"
            "<code>/borrow ឈ្មោះបុគ្គលិក 250000</code>"
        )
        return

    amount_text = args[-1].replace(",", "")

    try:
        amount = float(amount_text)

        if amount < 0:
            raise ValueError()

    except ValueError:
        await update.message.reply_html(
            "⚠️ <b>Error:</b> amount must be a non-negative number.\n\n"
            "Example:\n"
            "<code>/borrow ប៉ែន ទិត្យ 250000</code>"
        )
        return

    employee_name = " ".join(args[:-1]).strip()

    deduction = calculate_borrow_deduction(amount)

    success, result_or_error, report_day = record_borrow(
        employee_name,
        amount,
        deduction,
    )

    if not success:
        await update.message.reply_html(result_or_error)
        return

    registered_name = result_or_error

    if amount == 0:
        await update.message.reply_html(
            "✅ <b>បានលុបការខ្ចីប្រាក់របស់បុគ្គលិក / Borrow Cleared:</b>\n\n"
            f"👤 <b>បុគ្គលិក:</b> <b>{registered_name}</b>\n"
            f"📅 <b>ថ្ងៃទី:</b> <b>{report_day}</b>"
        )
        return

    debt = calculate_debt(amount, deduction)

    await update.message.reply_html(
        "<b>កត់ត្រាការខ្ចីប្រាក់ជោគជ័យ</b>\n\n"
        f"<b>បុគ្គលិក:</b> <b>{registered_name}</b>\n"
        f"<b>ថ្ងៃទី:</b> <b>{report_day}</b>\n"
        f"<b>ខ្ចីលុយ:</b> <b>{int(amount):,}៛</b>\n"
        f"<b>ប្រាក់កាត់:</b> <b>{int(deduction):,}៛</b>\n"
        f"<b>លុយជំពាក់:</b> <b>{int(debt):,}៛</b>"
    )