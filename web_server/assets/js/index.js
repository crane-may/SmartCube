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
  _.each(arr, function(p) {
    var t = new inode(p, this);
  }, this);
}
inode.prototype.show = function() {
  $("#file_list").empty();
  _.each(this.subs, function(v) {
    if (v.isDir){
      $("#file_list").append('<a href="#'+v.fullpath+
                        '" class="list-group-item"><span class="glyphicon glyphicon-folder-open mr10"></span><strong>'+
                        v.name+' /</strong></a>')
    }else{
      var sizestr = v.size + "B";
      if (v.size > 1024*1024) {
        sizestr = Math.floor(v.size / 1024 / 1024) + "MB";
      }else if (v.size > 1024) {
        sizestr = Math.floor(v.size / 1024) + "KB";
      }
      
      var tar = $('<div class="list-group-item"><span class="glyphicon glyphicon-file mr10"></span>'+
                        v.name+'<span class="label label-info ml10">'+sizestr+'</span></div>');
                        
      $("#file_list").append(tar);
      
      _.each(window.PLUGINS,function(plugin) {
        if (plugin.regex.test(v.name)) {
          plugin.decorate(tar, v);
        }
      });
    }
  }, this);
  
  var tar = $("#full_path").empty();
  var pp = this;
  while (pp){
    if (pp == this) {
      tar.prepend('<li class="active">'+pp.name+'</li>');
    }else{
      tar.prepend('<li><a href="#'+pp.fullpath+'">'+pp.name+'</a></li>');
    }
    pp = pp.parent;
  }
}
var root_inode = new inode({name:"root", size:0, isDir:true}, null);


function on_hash_change() {
  console.log("open" + location.hash);
  var path = location.hash.replace(/^#/,"");
  root_inode.makedirs(path)
  var path_inode = root_inode.sub(path);
  
  $.fetch({
    url: "/GET"+path,
    success: function(result) {
      path_inode.loadsubs(result);
      path_inode.show();
    }
  })
}

$(window).bind('hashchange', function() {
  on_hash_change();
});

if (! location.hash)
  $.go("/");
else
  $.go(location.hash.replace(/^#/,""));