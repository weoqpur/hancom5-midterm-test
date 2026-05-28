# Flask Todo App

Flask + SQLite + jQuery를 사용한 할 일 관리 API 및 웹 UI입니다.
Todo 기능에서 발생하는 SQLite 쿼리는 별도 MySQL 서버의 `query_log` 테이블에 저장됩니다.

## 1. MySQL 서버 설정

MySQL 서버 VM에서 먼저 로그 DB와 계정을 생성합니다.
아래 명령은 `mysql_log.sql` 파일이 있는 프로젝트 폴더에서 실행해야 합니다.

```bash
cd <프로젝트명>
sudo mysql < mysql_log.sql
```

Ubuntu MySQL은 기본적으로 `root` 계정이 비밀번호 로그인 대신 `auth_socket` 인증을 쓰는 경우가 많습니다.
이때 `mysql -u root -p`를 사용하면 아래 오류가 날 수 있으므로 `sudo mysql`을 사용합니다.

```text
ERROR 1698 (28000): Access denied for user 'root'@'localhost'
```

직접 MySQL 콘솔에서 실행하려면 아래처럼 접속한 뒤 SQL 파일을 실행합니다.

```bash
sudo mysql
```

```sql
SOURCE /프로젝트경로/mysql_log.sql;
```

예시:

```sql
SOURCE /home/user/hancom5-midterm-test/mysql_log.sql;
```

MySQL 서버 VM에 프로젝트 파일이 없다면 저장소를 클론하거나 `mysql_log.sql` 파일만 복사한 뒤 실행합니다.

```bash
git clone <저장소 주소>
cd <프로젝트명>
sudo mysql < mysql_log.sql
```

`mysql_log.sql`이 생성하는 항목:

- `todo_log` 데이터베이스
- ``query_log(`type`, `sql`, `dateime`)`` 테이블
- `todo_logger` 계정
- `todo_logger` 계정의 `todo_log` DB 접근 권한

Flask 서버와 MySQL 서버가 다른 VM이면 MySQL 외부 접속을 허용합니다.

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

아래 값을 찾습니다.

```text
bind-address = 127.0.0.1
```

다음처럼 변경합니다.

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

## 2. Flask 서버 설정

Flask 서버 VM에서 저장소를 클론한 뒤 프로젝트 폴더로 이동합니다.

```bash
git clone <저장소 주소>
cd <프로젝트명>
```

패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

환경설정 파일을 생성합니다.

```bash
cp .env.example .env
nano .env
```

`.env`에서 MySQL 서버 IP를 실제 IP로 수정합니다.

```env
MYSQL_HOST=MySQL서버IP
```

`.env` 전체 예시:

```env
FLASK_SECRET_KEY=todo-app-secret-key
MYSQL_LOG_ENABLED=1
MYSQL_HOST=192.168.56.102
MYSQL_PORT=3306
MYSQL_USER=todo_logger
MYSQL_PASSWORD=todo_logger_pw
MYSQL_DATABASE=todo_log
```

MySQL 로그를 잠시 끄고 SQLite 기능만 확인하려면 아래처럼 변경합니다.

```env
MYSQL_LOG_ENABLED=0
```

## 3. MySQL 접속 확인

Flask 서버 VM에서 MySQL 서버 접속을 확인합니다.

```bash
mysql -h MySQL서버IP -P 3306 -u todo_logger -p todo_log
```

비밀번호:

```text
todo_logger_pw
```

접속이 안 되면 아래 항목을 확인합니다.

- Flask 서버 `.env`의 `MYSQL_HOST`
- MySQL 서버의 `bind-address`
- MySQL 계정 권한
- MySQL 서버 방화벽 3306 포트
- 두 VM 간 네트워크 통신

MySQL 서버에서 테이블이 만들어졌는지도 확인합니다.

```sql
USE todo_log;
SHOW TABLES;
DESC query_log;
```

## 4. Flask 앱 실행

Flask 서버 VM에서 실행합니다.

```bash
python app.py
```

실행 로그에 아래와 같은 MySQL 설정이 출력됩니다.

```text
[MySQL log config] enabled=True, host=MySQL서버IP, port=3306, user=todo_logger, database=todo_log
```

`host`가 실제 MySQL 서버 IP가 아니라면 `.env`의 `MYSQL_HOST` 값을 수정한 뒤 Flask 앱을 다시 실행합니다.

브라우저에서 Flask 서버 VM의 IP로 접속합니다.

```text
http://Flask서버IP:5000
```

최초 실행 시 `todo.db` 파일이 자동 생성되고, `member`, `todolist` 테이블과 기본 계정이 자동 생성됩니다.

## 5. 기본 로그인 정보

```text
ID: admin
PW: admin1234
```

로그인 화면에는 기본 계정 정보가 자동 입력되지 않습니다.

## 6. 주요 기능

- 회원가입
- 로그인
- 할 일 목록 조회
- 할 일 추가
- 할 일 완료 처리
- 할 일 삭제
- SQLite 쿼리 MySQL 로그 저장

## 7. API 테스트

### 브라우저 확인 방법

1. 브라우저에서 `http://Flask서버IP:5000` 접속
2. 기본 계정 또는 회원가입 계정으로 로그인
3. 할 일을 입력하고 `추가` 버튼 클릭
4. 목록에 새 할 일이 표시되는지 확인
5. `완료` 버튼 클릭 후 완료 표시와 취소선 확인
6. `삭제` 버튼 클릭 후 목록에서 사라지는지 확인
7. MySQL 서버에서 `query_log` 테이블에 select, insert, update, delete 로그가 저장됐는지 확인

### Postman 확인 방법

Postman에서는 로그인 요청 후 발급되는 세션 쿠키를 유지해야 `/todos` API를 사용할 수 있습니다.
같은 Postman 탭/컬렉션에서 아래 순서대로 요청하면 됩니다.

### MySQL 로그 상태 확인

로그인 후 아래 주소에 접속하면 Flask 앱이 MySQL 로그 DB에 접속 가능한지 확인할 수 있습니다.

```http
GET /mysql-log-status
```

테스트 로그 한 줄을 직접 넣어보려면 아래 주소에 접속합니다.

```http
GET /mysql-log-status?test=1
```

정상 예시:

```json
{
  "enabled": true,
  "connected": true,
  "message": "MySQL 로그 DB에 정상 접속했습니다.",
  "log_count": 10,
  "test_insert": true
}
```

`connected`가 `false`이면 `last_error` 값을 확인합니다.

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

기대 결과:

```json
{
  "success": true,
  "message": "회원가입이 완료되었습니다."
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

기대 결과:

```json
{
  "success": true,
  "message": "로그인 성공"
}
```

### 할 일 조회

```http
GET /todos
```

기대 결과:

```json
{
  "success": true,
  "todos": []
}
```

### 할 일 추가

```http
POST /todos
Content-Type: application/json

{
  "title": "Flask 과제하기"
}
```

기대 결과:

```json
{
  "success": true,
  "message": "할 일이 추가되었습니다."
}
```

### 할 일 완료 처리

```http
PUT /todos/1
```

기대 결과:

```json
{
  "success": true,
  "message": "완료 처리되었습니다."
}
```

### 할 일 삭제

```http
DELETE /todos/1
```

기대 결과:

```json
{
  "success": true,
  "message": "삭제되었습니다."
}
```

로그인하지 않고 `/todos` API를 호출하면 아래처럼 차단됩니다.

```json
{
  "success": false,
  "message": "로그인이 필요합니다."
}
```

## 8. 데이터베이스 구조

SQLite 파일명은 `todo.db`입니다.

SQLite 테이블:

- `member(idx, uname, uid, upwd, datetime)`
- `todolist(id, title, uid, completed, datetime)`

MySQL 로그 테이블:

- ``query_log(`type`, `sql`, `dateime`)``

로그 예시:

```text
type: insert
sql: INSERT INTO todolist (title, uid, completed, datetime) VALUES ('Flask 과제하기', 'admin', 0, '2026-05-28 10:00:00')
dateime: 2026-05-28 10:00:00
```

로그 확인 쿼리:

```sql
SELECT `type`, `sql`, `dateime` FROM query_log ORDER BY `dateime` DESC;
```

`sql`은 MySQL에서 문법 키워드처럼 해석될 수 있으므로 반드시 백틱(`)으로 감싸서 조회합니다.
아래처럼 백틱 없이 실행하면 문법 오류가 발생할 수 있습니다.

```sql
SELECT type, sql, dateime FROM query_log ORDER BY dateime DESC;
```

전체 컬럼을 간단히 확인하려면 아래 명령도 사용할 수 있습니다.

```sql
SELECT * FROM query_log ORDER BY `dateime` DESC;
```

## 9. MySQL 로그가 남지 않을 때

아래 순서대로 확인합니다.

1. Flask 서버에서 최신 코드를 받았는지 확인

```bash
git pull
```

2. Flask 서버의 `.env` 확인

```bash
cat .env
```

아래 값이 맞아야 합니다.

```env
MYSQL_LOG_ENABLED=1
MYSQL_HOST=MySQL서버IP
MYSQL_PORT=3306
MYSQL_USER=todo_logger
MYSQL_PASSWORD=todo_logger_pw
MYSQL_DATABASE=todo_log
```

3. Flask 앱을 재시작하고 콘솔의 MySQL 설정 출력 확인

```bash
python app.py
```

4. 브라우저에서 로그인 후 MySQL 로그 상태 확인

```text
http://Flask서버IP:5000/mysql-log-status
```

5. 테스트 로그 직접 삽입 확인

```text
http://Flask서버IP:5000/mysql-log-status?test=1
```

이 요청 후 `log_count`가 증가하면 Flask 앱에서 MySQL INSERT 권한까지 정상입니다.

6. MySQL 서버에서 로그 확인

```sql
USE todo_log;
SELECT `type`, `sql`, `dateime` FROM query_log ORDER BY `dateime` DESC;
```

7. 로그가 계속 비어 있으면 Todo 화면에서 조회, 추가, 완료, 삭제를 한 번씩 실행한 뒤 다시 확인
