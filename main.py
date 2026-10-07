import json
import aiosqlite
import sqlite3
import tempfile
from pathlib import Path

from fastmcp import FastMCP


mcp = FastMCP("expense tracker")

BASE_DIR = Path(__file__).parent
CATEGORIES_PATH = BASE_DIR / "categories.json"

DATA_DIR = Path(tempfile.gettempdir()) / "expense_tracker_data"
DATA_DIR.mkdir(
    parents = True,
    exist_ok = True,
)
DB_PATH = DATA_DIR / "expenses.db"

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATETIME NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        sub_category TEXT DEFAULT '',
        note TEXT DEFAULT ''
    )
"""


def load_categories() -> dict:
    if CATEGORIES_PATH.exists():
        return json.loads(
            CATEGORIES_PATH.read_text(
                encoding = "utf-8",
            )
        )
    return {
        "Other": ["Miscellaneous"],
    }


@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    sub_category: str = "",
    note: str = "",
) -> str:
    """
    Save one expense in the database.

    Always call list_categories first and pick the category and
    sub_category from that list, spelled exactly the same way.

    Args:
        date: The day of the expense, written as YYYY-MM-DD.
        amount: How much money was spent.
        category: The main group, for example Food or Transport.
        sub_category: The smaller group, for example Groceries or Cab.
        note: A short description of the expense.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        cursor = db.execute(
            "INSERT INTO expenses "
            "(date, amount, category, sub_category, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (date, amount, category, sub_category, note),
        )
        await db.commit()
        new_id = cursor.lastrowid

    return f"Saved expense #{new_id}: {amount} for {category} on {date}."


@mcp.tool()
async def list_expenses(start_date: str, end_date: str) -> list[dict]:
    """
    List every expense between two dates (both days included).

    Args:
        start_date: First day to include, written as YYYY-MM-DD.
        end_date: Last day to include, written as YYYY-MM-DD.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, date, amount, category, sub_category, note "
            "FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date, id",
            (start_date, end_date),
        )
        rows = await cursor.fetchall()

    return [dict(row) for row in rows]


@mcp.tool()
async def summarize_expenses(
    start_date: str,
    end_date: str,
    category: str = "",
) -> list[dict]:
    """
    Add up the spending for each category between two dates.

    Args:
        start_date: First day to include, written as YYYY-MM-DD.
        end_date: Last day to include, written as YYYY-MM-DD.
        category: Leave empty for all categories, or give one name.
    """

    query = (
        "SELECT category, SUM(amount) AS total, COUNT(*) AS entries "
        "FROM expenses "
        "WHERE date BETWEEN ? AND ?"
    )
    params = [start_date, end_date]

    if category:
        query += " AND category = ?"
        params.append(category)
    query += " GROUP BY category ORDER BY total DESC"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            query, params,
        )
        rows = await cursor.fetchall()

    return [dict(row) for row in rows]


@mcp.tool()
def list_categories() -> dict:
    """Return the allowed categories and their sub-categories."""
    return load_categories()


@mcp.resource("expense://categories")
def categories_resource() -> str:
    """The allowed expense categories, as a JSON text document."""
    return json.dumps(load_categories(), indent=2)


def main():
    mcp.run(
        transport = "http",
        host = "0.0.0.0",
        port = 8000,
    )


if __name__ == "__main__":
    main()
