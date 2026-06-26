import re

from telegram import Update
from telegram.ext import ContextTypes

from app.services.employees import (
    add_employees_from_text,
    delete_employees_from_text,
    get_employee_list_text,
    rename_employee,
)


async def employees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show all registered employees.
    Command:
    /employees
    """
    text = get_employee_list_text()
    await update.message.reply_html(text)


async def addemployees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add multiple employees.
    Command:
    /addemployees
    """
    message_text = update.message.text

    command_match = re.match(r"^/addemployees?(?:@\w+)?\s*", message_text)

    if not command_match:
        return

    content = message_text[command_match.end():].strip()

    if not content:
        await update.message.reply_html(
            "⚠️ <b>ចម្លងគំរូខាងក្រោម រួចកែសម្រួលដើម្បីចុះឈ្មោះបុគ្គលិក៖</b>\n"
            "<b>Copy and edit the template below to register employees:</b>\n\n"
            "<code>/addemployees\n"
            "ឈ្មោះបុគ្គលិក ប 80000\n"
            "ឈ្មោះបុគ្គលិក ស 65000</code>\n\n"
            "ប = ប្រុស\n"
            "ស = ស្រី"
        )
        return

    result = add_employees_from_text(content)

    response_text = ""

    if result["success"]:
        response_text += "✅ <b>Added/Updated Employees:</b>\n"
        response_text += "\n".join(result["success"])

    if result["errors"]:
        if response_text:
            response_text += "\n\n"

        response_text += "⚠️ <b>Errors:</b>\n"
        response_text += "\n".join(result["errors"])

    if not response_text:
        response_text = "⚠️ No valid employees parsed."

    await update.message.reply_html(response_text)


async def updateemployee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Update employee name.
    Command:
    /updateemployee old name -> new name
    """
    message_text = update.message.text

    command_match = re.match(r"^/updateemployees?(?:@\w+)?\s*", message_text)

    if not command_match:
        return

    command_args = message_text[command_match.end():].strip()

    if not command_args or "->" not in command_args:
        await update.message.reply_html(
            "⚠️ <b>ចម្លងគំរូខាងក្រោម រួចកែសម្រួលដើម្បីប្ដូរឈ្មោះបុគ្គលិក៖</b>\n"
            "<b>Copy and edit the template below to rename an employee:</b>\n\n"
            "<code>/updateemployee ឈ្មោះចាស់ -> ឈ្មោះថ្មី</code>"
        )
        return

    old_name, new_name = command_args.split("->", 1)

    success, message = rename_employee(old_name, new_name)

    if success:
        await update.message.reply_html(f"✅ <b>{message}</b>")
    else:
        await update.message.reply_html(f"⚠️ {message}")


async def deleteemployees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Delete multiple employees.
    Command:
    /deleteemployees
    """
    message_text = update.message.text

    command_match = re.match(r"^/deleteemployees?(?:@\w+)?\s*", message_text)

    if not command_match:
        return

    content = message_text[command_match.end():].strip()

    if not content:
        await update.message.reply_html(
            "⚠️ <b>ចម្លងគំរូខាងក្រោម រួចកែសម្រួលដើម្បីលុបឈ្មោះបុគ្គលិក៖</b>\n"
            "<b>Copy and edit the template below to delete employees:</b>\n\n"
            "<code>/deleteemployees\n"
            "ឈ្មោះបុគ្គលិក</code>"
        )
        return

    result = delete_employees_from_text(content)

    response_text = ""

    if result["success"]:
        response_text += "✅ <b>Deleted Employees & History:</b>\n"
        response_text += "\n".join(result["success"])

    if result["errors"]:
        if response_text:
            response_text += "\n\n"

        response_text += "⚠️ <b>Errors / Not Found:</b>\n"
        response_text += "\n".join(result["errors"])

    if not response_text:
        response_text = "⚠️ No valid employee names parsed."

    await update.message.reply_html(response_text)