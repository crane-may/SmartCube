jQuery.extend({
go: function(s) {
  if (location.hash == "#" + s) {
    on_hash_change();
  }else{
    location.hash = "#" + s;
  }
},

fetch:function(op) {
  if (_.isString(op)) {
    var a = $('<script src="'+op+'"></script>');
    $("body").append(a);
    return;
  }
  if (op.success) {
    var success_org = op.success;
    op.success = function(result){
      if (result.fail) {
        $.fail(result.fail);
      }else{
        success_org(result.result);
      }
    }
  }
  op.fail = function() {
  }
  op.dataType = "json";
  op.contentType = "application/json; charset=utf-8";
  $.ajax(op);
},

size: function(sz) {
  var sizestr = sz + "B";
  if (sz > 1024*1024) sizestr = Math.floor(sz / 1024 / 1024) + "MB";
  else if (sz > 1024) sizestr = Math.floor(sz / 1024) + "KB";
  return sizestr;
}

}); 

function inode(p, parent){
  _.each(p, function(v, k) {
    this[k] = v;
  }, this);
  this.parent = null;
  this.fullpath = "/";
  if (parent) {
    parent.subs[this.name] = this;
    this.parent = parent;
    this.fullpath = this.parent.fullpath.replace(/\/$/,"")+"/"+this.name;
  }
  this.subs = {};
}
inode.prototype.sub = function (path) {
  var arr = _.compact(path.split("/"));
  if (arr.length == 0) {
    return this;
  }else if (arr.length == 1){
    return this.subs[arr[0]];
  }else {
    return this.subs[arr[0]].sub(_.rest(arr).join("/"));
  }
};
inode.prototype.makedirs = function(path) {
  var arr = _.compact(path.split("/"));
  if (arr.length > 0){
    if (! this.subs[arr[0]]) this.subs[arr[0]] = new inode({name:arr[0], size:0, isDir:true}, this);
  }
  if (arr.length > 1){
    this.subs[arr[0]].makedirs(_.rest(arr).join("/"));
  }
}
inode.prototype.loadsubs = function(arr) {
  _(arr).chain().sortBy(function(f) {
    return (f.isDir ? 'd':'f') + f.name;
  }).each(function(p) {
    var t = new inode(p, this);
  }, this);
}
inode.prototype.show = function() {
  window.cur_inode = this;
  $('#bar_title').html(this.name);
  $(".nav-ops li").show();
  if (this == root_inode){
    $("#rename_dialog_btn,#delete_btn").closest('li').hide();
  }
  
  if (this.isDir){
    $("#file_list").empty().show();
    $("#file_info").hide();
    _.each(this.subs, function(v) {
      if (v.isHidden()){
        return;
      }else if (v.isDir){
        $("#file_list").append('<a href="#'+v.fullpath+
                          '" class="list-group-item"><span class="glyphicon glyphicon-folder-open mr10"></span><strong>'+
                          v.name+' /</strong></a>')
      }else{
        var tar = $('<a href="#'+v.fullpath+
                    '" class="list-group-item"><span class="glyphicon glyphicon-file mr10"></span>'+
                    v.name+' <span class="label label-info ml10">'+$.size(v.size)+'</span></a>');
        $("#file_list").append(tar);
              
        _.each(window.PLUGINS,function(plugin) {
          if (plugin.regex.test(v.name)) plugin.inline_decorate(tar, v);
        });
      }
    }, this);    
  }else{
    $("#upload_dialog_btn,#create_dir_dialog_btn").closest('li').hide();
    
    $("#file_list").hide();
    $("#file_info").show().find('.panel-body').html('<span class="label label-info">'+$.size(this.size)+'</span>');
    
    _.each(window.PLUGINS,function(plugin) {
      if (plugin.regex.test(this.name)) plugin.decorate($("#file_info .panel-body"), this);
    },this);
  }
  
  var tar = $("#full_path").empty();
  var pp = this;
  while (pp){
    if (pp == this) tar.prepend('<li class="active">'+pp.name+'</li>');
    else tar.prepend('<li><a href="#'+pp.fullpath+'">'+pp.name+'</a></li>');
    pp = pp.parent;
  }
}
inode.prototype.isHidden = function() { return /^[.]/.test(this.name); }

var root_inode = new inode({name:"root", size:0, isDir:true}, null);


function on_hash_change() {
  console.log("open " + location.hash);
  var path = location.hash.replace(/^#/,"");
  
  $.fetch({
    url: "/LS"+path,
    success: function(result) {
      // dir
      if (_.isArray(result)) {
        root_inode.makedirs(path)
        var path_inode = root_inode.sub(path);
        path_inode.loadsubs(result);
        path_inode.show();
      }
      
      // file
      else if (_.isObject(result)){
        var parent = path.replace(/\/[^/]+$/,'');
        root_inode.makedirs(parent);
        var parent_inode = root_inode.sub(parent);
        
        var cur = new inode(result, parent_inode);
        cur.show();
      }
    }
  })
}

$(window).bind('hashchange', function() {
  on_hash_change();
});

$.go(location.hash ? location.hash.replace(/^#/,"") : "/");
  
  
//////////////////////////////////////////////////////////////////

$("#upload_dialog_btn").click(function() {
  $("#upload_dialog").modal('show');
});
$("#create_dir_dialog_btn").click(function() {
  $("#create_dir_name").val('');
  $("#create_dir_dialog").modal('show');
});
$("#rename_dialog_btn").click(function() {
  $("#rename_name").val(cur_inode.name);
  $("#rename_dialog").modal('show');
});


$("#upload_btn").click(function() {
  $("#upload_ref").val(location.href);
  $("#upload_path").val(cur_inode.fullpath);
  $("#upload_form").submit();
});
$("#create_dir_btn").click(function() {
  $("#create_dir_ref").val(location.href);
  $("#create_dir_path").val(cur_inode.fullpath);
  $("#create_dir_form").submit();
});
$("#rename_btn").click(function() {
  $("#rename_ref").val(location.href);
  $("#rename_old_path").val(cur_inode.fullpath);
  $("#rename_new_path").val(cur_inode.fullpath.replace(/\/[^\/]+$/,'') +'/'+ $("#rename_name").val());
  $("#rename_form").submit();
})

$("#delete_btn").click(function() {
  if (confirm("确定删除？")) {
    $("#delete_form").attr("action", '/DELETE'+cur_inode.fullpath).submit();
  }
})