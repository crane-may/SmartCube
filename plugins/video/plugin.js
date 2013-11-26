(function() {

var base_url = 'http://' + location.host.split(':')[0] +':'+PLUGIN_CONFIGS.VIDEO.port;

function clabel(cnt, cls) {
  return $(' <span class="label label-'+cls+' ml10">'+cnt+'</span>');
}
function cbutton(cnt, func) {
  var tar = $(' <button type="button" class="btn btn-default btn-sm ml10">'+cnt+'</button>');
  tar.click(func);
  return tar;
}

var inline_decorate = function(tar, file) {
  $(".glyphicon", tar).removeClass("glyphicon-file").addClass("glyphicon-film");
}

var video_decorate = function(tar, file) {
  if (file.plugin["video:info"]) {
    var video_info = $.parseJSON(file.plugin["video:info"]);
    tar.append(clabel('时长: '+Math.floor(video_info.format.duration/60)+' 分钟', 'default'));
  }
  
  var stats = file.plugin["video:stats"];
  if (! stats) {
    tar.append(cbutton('提取视频信息',function() {
      $.fetch(base_url+'/INFO'+file.fullpath);
    }));
  }
  
  else if (stats == '1') {
    tar.append(cbutton('准备播放',function() {
      $.fetch(base_url+'/DECODE'+file.fullpath);
    }));
  }
  
  else if (stats == '2') tar.append(clabel('准备中...', 'warning'));
  else if (stats == '3') tar.append(clabel('建立索引中...', 'warning'));
  else if (stats == '－1') tar.append(clabel('出错'), 'danger');
  
  else if (stats == '4' || stats == '5') {
    if (stats == '4') tar.append(clabel('转码中...', 'warning'));
    
    var btn = $(' <a class="btn btn-primary btn-sm ml10" href="'+base_url+'/PLAY/'+file.plugin['video:signature']+
                '/v.m3u8'+'" target="_blank">播放</a>');
    tar.append(btn);
    if (root_inode.sub(file.fullpath + '.srt')){
      var btn = $(' <a class="btn btn-primary btn-sm ml10" href="'+base_url+'/PLAY/'+file.plugin['video:signature']+
                  '/vsub.m3u8?srt='+decodeURIComponent(file.fullpath + '.srt')+'" target="_blank">带字幕播放</a>');
      tar.append(btn);
    }
  }
}

window.PLUGINS = window.PLUGINS || [];
window.PLUGINS.push({
  regex: /[.](mkv|mov)$/,
  inline_decorate: inline_decorate,
  decorate: video_decorate
});
})();

