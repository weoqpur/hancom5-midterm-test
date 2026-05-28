import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "todo.db")

app = Flask(__name__)
app.secret_key = "todo-app-secret-key"
CORS(app, supports_credentials=True)


def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS member (
            idx INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT NOT NULL,
            uid TEXT NOT NULL UNIQUE,
            upwd TEXT NOT NULL,
            datetime TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS todolist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            uid TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            datetime TEXT NOT NULL
        )
        """
    )

    cur.execute("SELECT idx FROM member WHERE uid = ?", ("admin",))
    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO member (uname, uid, upwd, datetime)
            VALUES (?, ?, ?, ?)
            """,
            ("관리자", "admin", "admin1234", now_string()),
        )

    conn.commit()
    conn.close()


def login_required():
    if "uid" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return None


def row_to_todo(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "uid": row["uid"],
        "completed": bool(row["completed"]),
        "datetime": row["datetime"],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    uid = data.get("uid", "").strip()
    upwd = data.get("upwd", "").strip()

    if not uid or not upwd:
        return jsonify({"success": False, "message": "아이디와 비밀번호를 입력하세요."}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT idx, uname, uid FROM member WHERE uid = ? AND upwd = ?",
        (uid, upwd),
    )
    member = cur.fetchone()
    conn.close()

    if member is None:
        return jsonify({"success": False, "message": "로그인 정보가 올바르지 않습니다."}), 401

    session["uid"] = member["uid"]
    session["uname"] = member["uname"]
    return jsonify(
        {
            "success": True,
            "message": "로그인 성공",
            "member": {"idx": member["idx"], "uname": member["uname"], "uid": member["uid"]},
        }
    )


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    uname = data.get("uname", "").strip()
    uid = data.get("uid", "").strip()
    upwd = data.get("upwd", "").strip()

    if not uname or not uid or not upwd:
        return jsonify({"success": False, "message": "이름, 아이디, 비밀번호를 모두 입력하세요."}), 400

    created_at = now_string()
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO member (uname, uid, upwd, datetime)
            VALUES (?, ?, ?, ?)
            """,
            (uname, uid, upwd, created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "이미 사용 중인 아이디입니다."}), 409

    member_idx = cur.lastrowid
    conn.close()

    session["uid"] = uid
    session["uname"] = uname

    return jsonify(
        {
            "success": True,
            "message": "회원가입이 완료되었습니다.",
            "member": {"idx": member_idx, "uname": uname, "uid": uid},
        }
    ), 201


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "로그아웃되었습니다."})


@app.route("/me", methods=["GET"])
def me():
    if "uid" not in session:
        return jsonify({"logged_in": False}), 200
    return jsonify({"logged_in": True, "uid": session["uid"], "uname": session["uname"]})


@app.route("/todos", methods=["GET"])
def get_todos():
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, uid, completed, datetime
        FROM todolist
        WHERE uid = ?
        ORDER BY id DESC
        """,
        (session["uid"],),
    )
    todos = [row_to_todo(row) for row in cur.fetchall()]
    conn.close()

    return jsonify({"success": True, "todos": todos})


@app.route("/todos", methods=["POST"])
def add_todo():
    auth_error = login_required()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"success": False, "message": "할 일을 입력하세요."}), 400

    created_at = now_string()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO todolist (title, uid, completed, datetime)
        VALUES (?, ?, ?, ?)
        """,
        (title, session["uid"], 0, created_at),
    )
    conn.commit()
    todo_id = cur.lastrowid
    conn.close()

    return jsonify(
        {
            "success": True,
            "message": "할 일이 추가되었습니다.",
            "todo": {
                "id": todo_id,
                "title": title,
                "uid": session["uid"],
                "completed": False,
                "datetime": created_at,
            },
        }
    ), 201


@app.route("/todos/<int:todo_id>", methods=["PUT"])
def complete_todo(todo_id):
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE todolist
        SET completed = 1
        WHERE id = ? AND uid = ?
        """,
        (todo_id, session["uid"]),
    )
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed == 0:
        return jsonify({"success": False, "message": "할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True, "message": "완료 처리되었습니다."})


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM todolist WHERE id = ? AND uid = ?", (todo_id, session["uid"]))
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed == 0:
        return jsonify({"success": False, "message": "할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True, "message": "삭제되었습니다."})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
