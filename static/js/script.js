function post_json(url, data) {
    $.ajax({type: "POST",
        url: url,
        data: data,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
    });
}

$(document).ready(function(){
    var colorPicker = new iro.ColorPicker("#govle_color_basic", {
        width: 320,
        color: "#f00",
        display: "inline-block",
    });
    $("#govle_btn_color").click(function(e) {
        e.preventDefault();
        post_json("/api/v1/color", JSON.stringify({ "color": colorPicker.color.hexString}))
    });
    $("#govle_btn_on").click(function(e) {
        e.preventDefault();
        post_json("/api/v1/power", JSON.stringify({ "state": true}))
    });
    $("#govle_btn_off").click(function(e) {
        e.preventDefault();
        post_json("/api/v1/power", JSON.stringify({ "state": false}))
    });
});