var g_params = {'new_image_name':''};
var r = null, r2 = null, file_path;

function get_params(){
    return g_params;
}

function doFirst_media()
{
    /* 媒体文件上传 */
    r = new Resumable({
        target     : '/plat/media',
        chunkSize  : 1024*512,
        query      : get_params,
        maxFiles   : 1,
        testChunks : false,
    });

    r.assignBrowse($('#browseButton')[0], false);

    r.on('fileAdded', function(file, event){
        if (file.size>1024*1024*400){
            r.cancel();
            alertify.error("文件大小不能超过400M");
        }else if (!!file.file.type.match(/audio.*|video.*/)){
            g_params['new_image_name'] = randomid();
            r.upload();

            var date_str = (new Date()).toISOString().substring(0, 10).replace(/-/g,'');
            var file_type = file.fileName.split('.');
            file_path = date_str+"/"+g_params['new_image_name']+"."+file_type[file_type.length-1];

            var radios = $('input:radio[name=media]');
            if (!!file.file.type.match(/audio.*/)){
                radios.filter('[value=audio]').prop('checked', true)
            } else {
                radios.filter('[value=video]').prop('checked', true)
            }
        }else{
            r.cancel();
            alertify.error("不是音频／视频文件！");
        }
    });
    r.on('uploadStart', function(){
        $("#layout").show();
        $("#over").show();
    });
    r.on('complete', function(){
        $("#layout").hide();
        $("#over").hide();
        alertify.warning("上传成功！");
        // 设置页面数据
        $("#media_file").val(file_path);
    });
    r.on('error', function(message, file){
        $("#layout").hide();
        $("#over").hide();
        alertify.error("出错了："+message);
    });
    r.on('cancel', function(){
        $("#layout").hide();
        $("#over").hide();
    });



    /* 讲师音频上传 */
    r2 = new Resumable({
        target     : '/plat/media',
        chunkSize  : 1024*512,
        query      : get_params,
        maxFiles   : 1,
        testChunks : false,
    });

    r2.assignBrowse($('#speakBrowseButton')[0], false);

    r2.on('fileAdded', function(file, event){
        if (file.size>1024*1024*10){
            r2.cancel();
            alertify.error("文件大小不能超过10M");
        }else if (!!file.file.type.match(/audio.*/)){
            g_params['new_image_name'] = randomid();
            r2.upload();

            var date_str = (new Date()).toISOString().substring(0, 10).replace(/-/g,'');
            var file_type = file.fileName.split('.');
            file_path = date_str+"/"+g_params['new_image_name']+"."+file_type[file_type.length-1];
        }else{
            r2.cancel();
            alertify.error("不是音频文件！");
        }
    });
    r2.on('uploadStart', function(){
        $("#layout").show();
        $("#over").show();
    });
    r2.on('complete', function(){
        $("#layout").hide();
        $("#over").hide();
        alertify.warning("上传成功！");
        // 设置页面数据
        $("#speaker_media").val(file_path);
    });
    r2.on('error', function(message, file){
        $("#layout").hide();
        $("#over").hide();
        alertify.error("出错了："+message);
    });
    r2.on('cancel', function(){
        $("#layout").hide();
        $("#over").hide();
    });

}

function randomid()
{
    var text = "";
    var possible = "abcdefghijklmnopqrstuvwxyz";

    for( var i=0; i < 10; i++ )
        text += possible.charAt(Math.floor(Math.random() * possible.length));

    return text;
}
