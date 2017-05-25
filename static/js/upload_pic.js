var image_list=[];
var rand_id_list = [];

var g_params = {'new_image_name':''};
var r9 = null;

function get_params(){
    return g_params;
}

function doFirst_pic()
{
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


    /* 图片文件上传 */
    r9 = new Resumable({
        target     : '/plat/image2',
        chunkSize  : 1024*512,
        query      : get_params,
        maxFiles   : 1,
        testChunks : false,
    });

    r9.assignBrowse($('#picBrowseButton')[0], false);

    r9.on('fileAdded', function(file, event){
        if (file.size>1024*1024*1){
            r9.cancel();
            alertify.error("文件大小不能超过1M");
        }else if (!!file.file.type.match(/image.*/)){
            g_params['new_image_name'] = randomid();
            r9.upload();

            //var date_str = (new Date()).toISOString().substring(0, 10).replace(/-/g,'');
            var file_type = file.fileName.split('.');
            g_params['file_name'] = g_params['new_image_name']+"."+file_type[file_type.length-1];
            g_params['file_path'] = g_params['new_image_name'].substring(0,2)+"/"+g_params['file_name'];

        }else{
            r9.cancel();
            alertify.error("不是图片文件！");
        }
    });
    r9.on('uploadStart', function(){
        $("#layout").show();
        $("#over").show();
    });
    r9.on('complete', function(){
        $("#layout").hide();
        $("#over").hide();
        alertify.warning("上传成功！");
        // 设置页面数据
        var file_url = '/static/image/product/' + g_params['file_path'];
        rand_id = showUploadedItem(file_url);
        image_list = image_list.concat(g_params['file_name']);
        rand_id_list = rand_id_list.concat(rand_id);
        $("#form_image").val(image_list);
    });
    r9.on('error', function(message, file){
        $("#layout").hide();
        $("#over").hide();
        alertify.error("出错了："+message);
    });
    r9.on('cancel', function(){
        $("#layout").hide();
        $("#over").hide();
    });


    /* 初始话图片列表 */
    $("#image-list").children().each(function() {
        rand_id_list = rand_id_list.concat($(this).attr('id'));
        image_list = image_list.concat($(this).attr('id').replace('_','.'));
    });
    $("#form_image").val(image_list);

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

function randomid()
{
    var text = "";
    var possible = "abcdefghijklmnopqrstuvwxyz";

    for( var i=0; i < 10; i++ )
        text += possible.charAt(Math.floor(Math.random() * possible.length));

    return text;
}
