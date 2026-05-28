# Flask Todo App

Flask + SQLite + jQuery를 사용한 할 일 관리 API 및 웹 UI 예제입니다.

## 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:5000
```

## 기본 로그인 정보

```text
ID: admin
PW: admin1234
```

최초 실행 시 `todo.db` 파일이 자동 생성되고, `member`, `todolist` 테이블과 기본 계정이 자동으로 생성됩니다.

MySQL 로그 기능을 사용하려면 실행 전에 MySQL 접속 환경변수를 설정합니다.

```bash
export MYSQL_HOST=MySQL서버IP
export MYSQL_PORT=3306
export MYSQL_USER=todo_logger
export MYSQL_PASSWORD=todo_logger_pw
export MYSQL_DATABASE=todo_log
python app.py
```

MySQL 로그를 잠시 끄고 SQLite 기능만 확인하려면 아래처럼 실행할 수 있습니다.

```bash
MYSQL_LOG_ENABLED=0 python app.py
```

## 주요 기능

- 회원가입
- 로그인
- 할 일 목록 조회
- 할 일 추가
- 할 일 완료 처리
- 할 일 삭제

## API

### 회원가입

```http
POST /signup
Content-Type: application/json

{
  "uname": "홍길동",
  "uid": "hong",
  "upwd": "1234"
}
```

### 로그인

```http
POST /login
Content-Type: application/json

{
  "uid": "admin",
  "upwd": "admin1234"
}
```

### 할 일 조회

```http
GET /todos
```

### 할 일 추가

```http
POST /todos
Content-Type: application/json

{
  "title": "Flask 과제하기"
}
```

### 할 일 완료 처리

```http
PUT /todos/1
```

### 할 일 삭제

```http
DELETE /todos/1
```

## 데이터베이스

### SQLite

SQLite 파일명은 `todo.db`입니다.

사용 테이블:

- `member(idx, uname, uid, upwd, datetime)`
- `todolist(id, title, uid, completed, datetime)`

### MySQL 로그 테이블

Todo 기능에서 발생하는 SQLite 쿼리는 MySQL `query_log` 테이블에 함께 저장됩니다.

저장 필드:

- `type`: 쿼리 첫 단어
- `sql`: SQL 구문 전체
- `dateime`: 쿼리 발생 시간

예시:

```text
type: insert
sql: INSERT INTO todolist (title, uid, completed, datetime) VALUES ('Flask 과제하기', 'admin', 0, '2026-05-28 10:00:00')
dateime: 2026-05-28 10:00:00
```

## MySQL 서버 설정

MySQL 서버 VM에서 root 또는 관리자 계정으로 아래 SQL 파일을 실행합니다.

```bash
mysql -u root -p < mysql_log.sql
```

`mysql_log.sql`은 아래 작업을 수행합니다.

- `todo_log` 데이터베이스 생성
- `query_log(type, sql, dateime)` 테이블 생성
- Flask 서버가 사용할 `todo_logger` 계정 생성
- `todo_logger` 계정에 `todo_log` DB 접근 권한 부여

### MySQL 외부 접속 허용

Flask 서버와 MySQL 서버가 다른 VM이면 MySQL 서버에서 외부 접속을 허용해야 합니다.

MySQL 설정 파일을 엽니다.

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

아래 값을 찾습니다.

```text
bind-address = 127.0.0.1
```

다른 VM에서 접속할 수 있도록 변경합니다.

```text
bind-address = 0.0.0.0
```

MySQL을 재시작합니다.

```bash
sudo systemctl restart mysql
```

방화벽을 사용하는 경우 Flask 서버 IP에서 3306 포트 접속을 허용합니다.

```bash
sudo ufw allow from Flask서버IP to any port 3306
```

### 접속 확인

Flask 서버 VM에서 MySQL 접속을 확인합니다.

```bash
mysql -h MySQL서버IP -P 3306 -u todo_logger -p todo_log
```

비밀번호:

```text
todo_logger_pw
```

로그 확인 쿼리:

```sql
SELECT type, sql, dateime FROM query_log ORDER BY dateime DESC;
```
