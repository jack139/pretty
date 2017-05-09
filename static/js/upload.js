var image_list=[];
var rand_id_list = [];

function doFirst()
{
(function () {
    var input = $("#images")[0], formdata = false;
    var rand_id = Math.random().toString(36).slice(2);

    function showUploadedItem (source) {
        var list = $("#image-list")[0],
            li   = document.createElement("li"),
            img  = document.createElement("img"),
            but = document.createElement("button");
        img.src = source;
        li.id = rand_id;
        li.style.cssText = "width: 450px;";
        but.innerHTML = "删除";
        but.onclick = function(){
            remove_image(rand_id);
            return false;
        };
        li.appendChild(img);
        li.appendChild(but);
        list.appendChild(li);

        return rand_id;
    }   

    if (window.FormData) {
        formdata = new FormData();
        $("#btn").hide();
    }
    
    input.addEventListener("change", function (evt) {
        $("#response").html("正在上传 . . .");
        var i = 0, len = this.files.length, img, reader, file, rand_id;
    
        for ( ; i < len; i++ ) { /* 只有上传一个文件，否则 rand_id 会被覆盖 */
            file = this.files[i];
    
            console.log(file.type);

            if (!!file.type.match(/image.*/)) {
                if ( window.FileReader ) {
                    reader = new FileReader();
                    reader.onloadend = function (e) { 
                        rand_id = showUploadedItem(e.target.result, file.fileName);
                    };
                    reader.readAsDataURL(file);
                }
                if (formdata) {
                    formdata.append("images", file);
                }
            }
            else {
                $("#response").html("不是图片文件！"); 
                formdata = false;
            }

            break; /* 只上传一个文件 */
        }
    
        if (formdata) {
            $.ajax({
                url: "/plat/image",
                type: "POST",
                data: formdata,
                processData: false,
                contentType: false,
                dataType: "json",
                complete: function(xhr, textStatus){
                    if(xhr.status==200){
                        var retJson = JSON.parse(xhr.responseText);
                        if (retJson["ret"]==0){
                            $("#response").html("保存为 " + retJson["image"]);
                            //$("#images").hide(); 
                            //formdata = new FormData();
                            image_list = image_list.concat(retJson["image"]);
                            rand_id_list = rand_id_list.concat(rand_id);
                            $("#form_image").val(image_list);
                        }
                        else{
                            $("#response").html("上传失败！"); 
                        }
                    }
                    else{
                        $("#response").html("网络异常！("+xhr.status+")");
                    }
                }
            });
        }

        formdata = new FormData();

    }, false);

    /* 初始话图片列表 */
    $("#image-list").children().each(function() {
        rand_id_list = rand_id_list.concat($(this).attr('id'));
        image_list = image_list.concat($(this).attr('id').replace('_','.'));
    });
    $("#form_image").val(image_list);

}());


}

/* 删除图片 */
function remove_image(image_id){
    var pos = rand_id_list.indexOf(image_id);
    if (pos==-1) /* 未找到id */
        return;

    rand_id_list.splice(pos,1);
    image_list.splice(pos,1);
    $("#form_image").val(image_list);

    $('#'+image_id).hide();
}
