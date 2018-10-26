String.prototype.replaceAll = function(sub, nsub) {
    return this.split(sub).join(nsub);
}
String.prototype.format = function() {
    var str = this;
    for (var i in arguments) {
        str = str.replaceAll('{' + i + '}', arguments[i]);
    }
    return str;
}

HTMLTextAreaElement.prototype.setLengthLimit = function(limit) {
    this.on("input", function() {
        this.value = this.value.slice(0, limit);
    })
}

function status(value) {
    $("#status").html(value);
}
function statusColor(color) {
    $("#status").css("color", color);
}
function activateHighlight(highlightedText) {
    console.log(highlightedText);   
    $("#highlighter").html(highlightedText);
    window.highlightActivated = true;
    $("#highlightUndoer").prop("disabled", false);
    $("#highlightUndoer").css("border", "3px solid red");
    $("high").filter(function(){
        return this.hasAttribute('definition');
    }).each(function(){
        console.log(this);
        $(this).balloon({
            contents: this.getAttribute("definition"),
            css: {
                fontSize: ".5rem"
            }
        });
    });
}

function highlightText() {
    if (!$("#modeSelect").val()) {
        status("No mode specified");
        statusColor("rgb(246, 155, 48)")
        return;
    }
    window.timer = 0;
    window.loadAnimationId = setInterval(function() {
        status("Requesting highlight" + ".".repeat(window.timer + 1));
        window.timer = (window.timer + 1) % 3;
    }, 500)
    $("#sendButton").prop("disabled", true);
    var reqTimeout = 10000;
    if ($("#modeSelect").val() == "Wiki")
        reqTimeout = 0;+
    $.ajax({
        url: "/highlightWithMode",
        timeout: reqTimeout,
        data: {
            mode: $("#modeSelect").val(),
            text: $("#highlighter").text()
        },
        success: function(result) {
            //console.log(result); // Just for debugging
            activateHighlight(result.highlightedText);
            clearInterval(window.loadAnimationId);
            status("Done");
            statusColor("rgb(94, 228, 11)");
            $("#sendButton").prop("disabled", false);
        },
        error: function(xhr, message) {
            clearInterval(window.loadAnimationId);
            status("Error: " + message);
            statusColor("red");
            $("#sendButton").prop("disabled", false);
        }
    })
}
function undoHighlight() {
    if (!window.highlightActivated)
        return;
    window.highlightActivated = false;
    $("#highlighter").html($("#highlighter").text());
    $("#highlightUndoer").prop("disabled", true);
    $("#highlightUndoer").css("border", "");
}

$(function(){
    window.highlightActivated = false;
    $("#sendButton").click(highlightText);
    $("#highlightUndoer").click(undoHighlight);
});


