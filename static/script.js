$(function () {
    // 새로고침 후에도 세션이 남아 있으면 바로 Todo 화면을 보여준다.
    checkLogin();

    $("#auth-toggle").on("click", function () {
        // 로그인 폼과 회원가입 폼을 한 화면에서 전환한다.
        const signupMode = $("#signup-form").hasClass("hidden");
        $("#login-message").text("");

        if (signupMode) {
            $("#auth-title").text("Todo 회원가입");
            $("#login-form").addClass("hidden");
            $("#signup-form").removeClass("hidden");
            $("#auth-toggle").text("로그인으로 돌아가기");
        } else {
            $("#auth-title").text("Todo 로그인");
            $("#signup-form").addClass("hidden");
            $("#login-form").removeClass("hidden");
            $("#auth-toggle").text("회원가입");
        }
    });

    $("#login-form").on("submit", function (event) {
        event.preventDefault();

        // 로그인 API로 JSON 데이터를 전송한다.
        $.ajax({
            url: "/login",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                uid: $("#uid").val(),
                upwd: $("#upwd").val()
            }),
            success: function (res) {
                $("#login-message").text(res.message);
                showTodo(res.member);
                loadTodos();
            },
            error: function (xhr) {
                const res = xhr.responseJSON || {};
                $("#login-message").text(res.message || "로그인 중 오류가 발생했습니다.");
            }
        });
    });

    $("#signup-form").on("submit", function (event) {
        event.preventDefault();

        // 회원가입 성공 시 서버가 세션을 생성하므로 바로 Todo 목록을 불러온다.
        $.ajax({
            url: "/signup",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                uname: $("#signup-uname").val(),
                uid: $("#signup-uid").val(),
                upwd: $("#signup-upwd").val()
            }),
            success: function (res) {
                $("#login-message").text(res.message);
                showTodo(res.member);
                loadTodos();
            },
            error: function (xhr) {
                const res = xhr.responseJSON || {};
                $("#login-message").text(res.message || "회원가입 중 오류가 발생했습니다.");
            }
        });
    });

    $("#logout-btn").on("click", function () {
        // 서버 세션을 삭제하고 로그인 화면으로 돌아간다.
        $.ajax({
            url: "/logout",
            method: "POST",
            success: function () {
                $("#todo-section").addClass("hidden");
                $("#login-section").removeClass("hidden");
                $("#todo-list").empty();
                $("#todo-message").text("");
            },
            error: function () {
                $("#todo-message").text("로그아웃 중 오류가 발생했습니다.");
            }
        });
    });

    $("#todo-form").on("submit", function (event) {
        event.preventDefault();

        // 입력한 할 일을 POST /todos로 추가한다.
        $.ajax({
            url: "/todos",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ title: $("#title").val() }),
            success: function (res) {
                $("#title").val("");
                $("#todo-message").text(res.message);
                loadTodos();
            },
            error: function (xhr) {
                const res = xhr.responseJSON || {};
                $("#todo-message").text(res.message || "할 일 추가 중 오류가 발생했습니다.");
            }
        });
    });

    $("#todo-list").on("click", ".complete-btn", function () {
        // 동적으로 생성된 완료 버튼은 이벤트 위임으로 처리한다.
        const id = $(this).closest("li").data("id");

        $.ajax({
            url: "/todos/" + id,
            method: "PUT",
            success: function (res) {
                $("#todo-message").text(res.message);
                loadTodos();
            },
            error: function (xhr) {
                const res = xhr.responseJSON || {};
                $("#todo-message").text(res.message || "완료 처리 중 오류가 발생했습니다.");
            }
        });
    });

    $("#todo-list").on("click", ".delete-btn", function () {
        // 동적으로 생성된 삭제 버튼은 이벤트 위임으로 처리한다.
        const id = $(this).closest("li").data("id");

        $.ajax({
            url: "/todos/" + id,
            method: "DELETE",
            success: function (res) {
                $("#todo-message").text(res.message);
                loadTodos();
            },
            error: function (xhr) {
                const res = xhr.responseJSON || {};
                $("#todo-message").text(res.message || "삭제 중 오류가 발생했습니다.");
            }
        });
    });
});

function checkLogin() {
    // 현재 로그인 상태를 확인한다.
    $.ajax({
        url: "/me",
        method: "GET",
        success: function (res) {
            if (res.logged_in) {
                showTodo({ uid: res.uid, uname: res.uname });
                loadTodos();
            }
        }
    });
}

function showTodo(member) {
    // 인증 영역을 숨기고 Todo 영역을 표시한다.
    $("#login-section").addClass("hidden");
    $("#todo-section").removeClass("hidden");
    $("#user-info").text(member.uname + " (" + member.uid + ")");
}

function loadTodos() {
    // GET /todos로 목록을 가져와 화면에 렌더링한다.
    $.ajax({
        url: "/todos",
        method: "GET",
        success: function (res) {
            renderTodos(res.todos);
        },
        error: function (xhr) {
            const res = xhr.responseJSON || {};
            $("#todo-message").text(res.message || "할 일 목록을 불러오지 못했습니다.");
        }
    });
}

function renderTodos(todos) {
    // 서버에서 받은 Todo 배열을 li 요소로 변환한다.
    const $list = $("#todo-list");
    $list.empty();

    if (todos.length === 0) {
        $list.append('<li class="empty">등록된 할 일이 없습니다.</li>');
        return;
    }

    $.each(todos, function (_, todo) {
        const completedClass = todo.completed ? "completed" : "";
        const completeButton = todo.completed
            ? '<span class="done-label">완료</span>'
            : '<button type="button" class="complete-btn">완료</button>';

        const item = [
            '<li data-id="' + todo.id + '" class="' + completedClass + '">',
            '  <div class="todo-content">',
            '    <strong>' + escapeHtml(todo.title) + '</strong>',
            '    <span>' + todo.datetime + '</span>',
            '  </div>',
            '  <div class="actions">',
            completeButton,
            '    <button type="button" class="delete-btn">삭제</button>',
            '  </div>',
            '</li>'
        ].join("");

        $list.append(item);
    });
}

function escapeHtml(value) {
    // 사용자가 입력한 제목이 HTML로 실행되지 않도록 이스케이프한다.
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
