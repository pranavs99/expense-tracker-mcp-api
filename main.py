import json
import sqlite3
from pathlib import Path
from fastmcp import FastMCP


mcp = FastMCP("expense tracker")

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "expenses.db"
CATEGORIES_PATH = BASE_DIR / "categories.json"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            sub_category TEXT DEFAULT '',
            note TEXT DEFAULT ''
        )
        """
    )
    conn.commit()
    conn.close()



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
def add_expense(
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

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO expenses "
        "(date, amount, category, sub_category, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (date, amount, category, sub_category, note),
    )
    conn.commit()

    new_id = cursor.lastrowid
    conn.close()

    return f"Saved expense #{new_id}: {amount} for {category} on {date}."


@mcp.tool()
def list_expenses(start_date: str, end_date: str) -> list[dict]:
    """
    List every expense between two dates (both days included).

    Args:
        start_date: First day to include, written as YYYY-MM-DD.
        end_date: Last day to include, written as YYYY-MM-DD.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT id, date, amount, category, sub_category, note "
        "FROM expenses "
        "WHERE date BETWEEN ? AND ? "
        "ORDER BY date, id",
        (start_date, end_date),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@mcp.tool()
def summarize_expenses(
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

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(query, params).fetchall()

    conn.close()

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
    init_db()
    mcp.run(
        transport = "http",
        host = "0.0.0.0",
        port = 8000,
    )


if __name__ == "__main__":
    main()
