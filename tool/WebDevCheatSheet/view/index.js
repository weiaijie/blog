$(document).ready(function() {
    // 导航菜单点击事件
    $("#nav ul li a").click(function() {
        var index = $(this).parent().index();
        $("#nav ul li").removeClass("on");
        $(this).parent().addClass("on");
        $(".content").hide();
        $(".content").eq(index).show();
    });

    // 使元素可拖动
    $(".ui-draggable").draggable();

    // 关闭按钮事件
    $("#closebox").click(function() {
        $("#snippet").hide();
    });

    // 其他交互功能
    $("a").hover(function() {
        $(this).next("span").show();
    }, function() {
        $(this).next("span").hide();
    });
});
