var online_list=[];

function doFirst()
{
    (function () {
        /* 初始化列表 */
        saveFormOnline();
    }());
}

function saveFormOnline(){
    online_list=[];
    $("#online_obj option").each(function() {
        online_list = online_list.concat($(this).val());
    });
    $("#form_online").val(online_list);
}

function MoveLeftOrRight(LeftOrRight) {
    //查出select中有多少个可选节点
    var leftOptionLength = $("#online_obj option").length;
    var rightOptionLength = $("#all_obj option").length;
    var tmp_list=[];

    //左移节点
    if (LeftOrRight) {
        for (var i = 0; i < rightOptionLength; i++) {
            if ($("#all_obj option:eq(" + i + ")").is(":selected")) 
                tmp_list.push($("#all_obj option:eq(" + i + ")"));
        }
        $.each(tmp_list, function( index, value ) {
            $("#online_obj").append(value);
        })
    }
    //右移节点
    else {
        for (var i = 0; i < leftOptionLength; i++) {
            if ($("#online_obj option:eq(" + i + ")").is(":selected")) 
                tmp_list.push($("#online_obj option:eq(" + i + ")"));
        }
        $.each(tmp_list, function( index, value ) {
            $("#all_obj").append(value);
        })
    }

    saveFormOnline();
}

//上移下移功能的实现
function MoveUpOrDown(UpOrDown) {
    //查出select中有多少个可选节点
    var selecteOptionLength = $("#online_obj option").length;
    
    //上移节点
    if (UpOrDown) {
        for (var i = 0; i < selecteOptionLength; i++) {
            if ($("#online_obj option:eq(" + i + ")").is(":selected")) {
                if (i == 0) {
                    alertify.warning("到顶了！");
                    break;
                }
                $("#online_obj option:eq(" + i + ")").insertBefore($("#online_obj option:eq(" + i + ")").prev("option"));
            }
        }
    }
    //下移节点
    else {
        for (var i = selecteOptionLength - 1; i >= 0; i--) {
            if ($("#online_obj option:eq(" + i + ")").is(":selected")) {
                //判断是否选中最后一个节点
                if (i == selecteOptionLength - 1) {
                    alertify.warning("到底了！");
                    break;
                }
                //执行插入节点操作
                $("#online_obj option:eq(" + i + ")").insertAfter($("#online_obj option:eq(" + i + ")").next("option"));
            }
        }
    }

    saveFormOnline();
}

