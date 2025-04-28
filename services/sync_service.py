import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

DATABASE_FILE = "finance_bot.db"

def sync_with_google_sheets(user_id):
    """
    Синхронизирует транзакции пользователя с Google Таблицами.
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        bool: True если синхронизация прошла успешно, False в случае ошибки
        str: Сообщение о результате синхронизации
    """
    try:
        # Подключение к Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
        client = gspread.authorize(creds)

        spreadsheet_id = "ВАШ_SPREADSHEET_ID"  # <-- Заменить на ваш
        sheet = client.open_by_key(spreadsheet_id).sheet1

        # Получаем транзакции пользователя
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, amount, category, type FROM transactions WHERE user_id = ?", (user_id,))
        transactions = cursor.fetchall()
        conn.close()

        if not transactions:
            return False, "⚠️ У вас нет транзакций для синхронизации."

        # Обновление таблицы
        sheet.clear()
        sheet.append_row(["Дата", "Сумма", "Категория", "Тип"])
        sheet.append_rows(transactions)

        return True, "✅ Данные успешно синхронизированы с Google Таблицами!"

    except Exception as e:
        error_message = f"❌ Ошибка при синхронизации: {str(e)}"
        print(error_message)
        return False, error_message