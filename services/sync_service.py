import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

DATABASE_FILE = "finance_bot.db"


def sync_with_google_sheets(user_id):
    """
    Синхронізує транзакції користувача з Google Таблицями.
    
    Args:
        user_id (int): ID користувача
        
    Returns:
        bool: True якщо синхронізація пройшла успішно, False у випадку помилки
        str: Повідомлення про результат синхронізації
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)

        spreadsheet_id = "ВАШ_SPREADSHEET_ID"
        sheet = client.open_by_key(spreadsheet_id).sheet1

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, amount, category, type FROM transactions WHERE user_id = ?", (user_id,))
        transactions = cursor.fetchall()
        conn.close()

        if not transactions:
            return False, "⚠️ У вас немає транзакцій для синхронізації."

        sheet.clear()
        sheet.append_row(["Дата", "Сума", "Категорія", "Тип"])
        sheet.append_rows(transactions)

        return True, "✅ Дані успішно синхронізовано з Google Таблицями!"

    except Exception as e:
        error_message = f"❌ Помилка при синхронізації: {str(e)}"
        print(error_message)
        return False, error_message
