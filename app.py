import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_PATH = os.path.join(BASE_DIR, "todo.db")
MYSQL_LOG_ENABLED = os.getenv("MYSQL_LOG_ENABLED", "1") == "1"
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "todo_logger")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "todo_logger_pw")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "todo_log")

mysql_warning_shown = False
mysql_last_error = None
mysql_last_success = None

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "todo-app-secret-key")
CORS(app, supports_credentials=True)


def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def compact_sql(sql):
    return " ".join(sql.split())


def quote_sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def build_log_sql(sql, params=()):
    # SQLite의 ? 파라미터를 실제 값으로 바꿔 MySQL 로그에 남길 SQL 문자열을 만든다.
    logged_sql = compact_sql(sql)
    for param in params:
        logged_sql = logged_sql.replace("?", quote_sql_value(param), 1)
    return logged_sql


def get_sql_type(sql):
    # 로그 type 필드는 쿼리의 첫 단어만 소문자로 저장한다.
    return compact_sql(sql).split(" ", 1)[0].lower()


def get_mysql_connection():
    import mysql.connector

    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
    )


def init_mysql_log_db():
    if not MYSQL_LOG_ENABLED:
        return

    try:
        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS query_log (
                `type` VARCHAR(20) NOT NULL,
                `sql` TEXT NOT NULL,
                `dateime` DATETIME NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
        remember_mysql_success("MySQL log table ready")
    except Exception as exc:
        show_mysql_warning(exc)


def show_mysql_warning(exc):
    global mysql_last_error, mysql_warning_shown

    mysql_last_error = str(exc)

    if mysql_warning_shown:
        return

    mysql_warning_shown = True
    print(f"[MySQL log error] {exc}")


def remember_mysql_success(message):
    global mysql_last_error, mysql_last_success

    mysql_last_error = None
    mysql_last_success = message


def log_query(sql, params=()):
    if not MYSQL_LOG_ENABLED:
        return False

    try:
        conn = get_mysql_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_log (`type`, `sql`, `dateime`) VALUES (%s, %s, %s)",
            (get_sql_type(sql), build_log_sql(sql, params), now_string()),
        )
        conn.commit()
        conn.close()
        remember_mysql_success("Last query logged")
        return True
    except Exception as exc:
        show_mysql_warning(exc)
        return False


def execute_sql(cur, sql, params=()):
    # SQLite 쿼리를 실행한 뒤 같은 쿼리 정보를 MySQL 로그 테이블에 저장한다.
    cur.execute(sql, params)
    log_query(sql, params)
    return cur


def get_db():
    # SQLite 결과를 dict처럼 다루기 위해 Row factory를 설정한다.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    init_mysql_log_db()

    # 앱 최초 실행 시 필요한 SQLite 테이블과 기본 계정을 자동 생성한다.
    conn = get_db()
    cur = conn.cursor()

    execute_sql(
        cur,
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

    execute_sql(
        cur,
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

    execute_sql(cur, "SELECT idx FROM member WHERE uid = ?", ("admin",))
    if cur.fetchone() is None:
        execute_sql(
            cur,
            """
            INSERT INTO member (uname, uid, upwd, datetime)
            VALUES (?, ?, ?, ?)
            """,
            ("관리자", "admin", "admin1234", now_string()),
        )

    conn.commit()
    conn.close()


def login_required():
    # Todo API는 로그인한 사용자만 접근할 수 있다.
    if "uid" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    return None


def row_to_todo(row):
    # SQLite의 0/1 값을 JSON boolean 값으로 변환한다.
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
    # JSON으로 받은 uid/upwd를 member 테이블에서 확인한다.
    data = request.get_json(silent=True) or {}
    uid = data.get("uid", "").strip()
    upwd = data.get("upwd", "").strip()

    if not uid or not upwd:
        return jsonify({"success": False, "message": "아이디와 비밀번호를 입력하세요."}), 400

    conn = get_db()
    cur = conn.cursor()
    execute_sql(
        cur,
        "SELECT idx, uname, uid FROM member WHERE uid = ? AND upwd = ?",
        (uid, upwd),
    )
    member = cur.fetchone()
    conn.close()

    if member is None:
        return jsonify({"success": False, "message": "로그인 정보가 올바르지 않습니다."}), 401

    # 로그인 성공 시 세션에 사용자 정보를 저장한다.
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
    # member 테이블에 새 사용자를 등록하고, 성공하면 바로 로그인 처리한다.
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
        execute_sql(
            cur,
            """
            INSERT INTO member (uname, uid, upwd, datetime)
            VALUES (?, ?, ?, ?)
            """,
            (uname, uid, upwd, created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # uid 컬럼이 UNIQUE이므로 중복 아이디는 IntegrityError로 처리된다.
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


@app.route("/mysql-log-status", methods=["GET"])
def mysql_log_status():
    auth_error = login_required()
    if auth_error:
        return auth_error

    status = {
        "enabled": MYSQL_LOG_ENABLED,
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "database": MYSQL_DATABASE,
        "last_success": mysql_last_success,
        "last_error": mysql_last_error,
    }

    if not MYSQL_LOG_ENABLED:
        status["connected"] = False
        status["message"] = "MYSQL_LOG_ENABLED=0 상태입니다."
        return jsonify(status)

    try:
        conn = get_mysql_connection()
        cur = conn.cursor()
        if request.args.get("test") == "1":
            cur.execute(
                "INSERT INTO query_log (`type`, `sql`, `dateime`) VALUES (%s, %s, %s)",
                ("select", "SELECT 1 -- mysql log status test", now_string()),
            )
            conn.commit()

        cur.execute("SELECT COUNT(*) FROM query_log")
        count = cur.fetchone()[0]
        conn.close()
        status["connected"] = True
        status["log_count"] = count
        status["test_insert"] = request.args.get("test") == "1"
        status["message"] = "MySQL 로그 DB에 정상 접속했습니다."
        remember_mysql_success("MySQL status check passed")
    except Exception as exc:
        show_mysql_warning(exc)
        status["connected"] = False
        status["last_error"] = str(exc)
        status["message"] = "MySQL 로그 DB 접속에 실패했습니다."

    return jsonify(status)


@app.route("/todos", methods=["GET"])
def get_todos():
    # 현재 로그인한 사용자의 Todo만 조회한다.
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    execute_sql(
        cur,
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
    # JSON으로 받은 title을 현재 사용자의 Todo로 저장한다.
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
    execute_sql(
        cur,
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
    # 자신의 Todo만 완료 처리할 수 있도록 uid 조건을 함께 사용한다.
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    execute_sql(
        cur,
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
    # 자신의 Todo만 삭제할 수 있도록 uid 조건을 함께 사용한다.
    auth_error = login_required()
    if auth_error:
        return auth_error

    conn = get_db()
    cur = conn.cursor()
    execute_sql(cur, "DELETE FROM todolist WHERE id = ? AND uid = ?", (todo_id, session["uid"]))
    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed == 0:
        return jsonify({"success": False, "message": "할 일을 찾을 수 없습니다."}), 404

    return jsonify({"success": True, "message": "삭제되었습니다."})


if __name__ == "__main__":
    init_db()
    print(
        "[MySQL log config] "
        f"enabled={MYSQL_LOG_ENABLED}, host={MYSQL_HOST}, port={MYSQL_PORT}, "
        f"user={MYSQL_USER}, database={MYSQL_DATABASE}"
    )
    app.run(host="0.0.0.0", port=5000, debug=True)
