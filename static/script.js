$(function () {
    checkLogin();

    $("#auth-toggle").on("click", function () {
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
    $("#login-section").addClass("hidden");
    $("#todo-section").removeClass("hidden");
    $("#user-info").text(member.uname + " (" + member.uid + ")");
}

function loadTodos() {
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
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
