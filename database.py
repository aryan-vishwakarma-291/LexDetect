import sqlite3


def init_db():

    conn = sqlite3.connect("predictions.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT,

            prediction TEXT,

            confidence REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()

    conn.close()



def save_prediction(filename, prediction, confidence):

    conn = sqlite3.connect("predictions.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO history
        (filename, prediction, confidence)
        VALUES (?, ?, ?)
        """,
        (filename, prediction, confidence)
    )

    conn.commit()

    conn.close()

def get_history():

    conn = sqlite3.connect("predictions.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM history
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_prediction(prediction_id):

    conn = sqlite3.connect("predictions.db")

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id = ?",
        (prediction_id,)
    )

    conn.commit()

    conn.close()

def clear_history():

    conn = sqlite3.connect("predictions.db")

    cursor = conn.cursor()

    cursor.execute("DELETE FROM history")

    conn.commit()

    conn.close()