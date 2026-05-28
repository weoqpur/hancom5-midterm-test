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

MySQL 로그 테이블 생성 SQL은 `mysql_log.sql`에 작성했습니다.

```bash
mysql -u root -p < mysql_log.sql
```

로그 테이블 필드:

- `type`: 쿼리 첫 단어
- `sql`: SQL 구문 전체
- `dateime`: 쿼리 발생 시간
