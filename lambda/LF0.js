/**
 * Created by GraceHan on 2/27/19.
 */
var AWS = require('aws-sdk');

exports.handler = function(event, context, callback) {
    AWS.config.region = 'us-east-1';
    var lexUserId = 'chatbot-demo';
    var lexruntime = new AWS.LexRuntime({
        accessKeyId: "AKIAINI6VRSNOMGPY6LQ",
        secretAccessKey: "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"
    });
    var text = event.messages[0].unstructured.text;
    var params = {
        botAlias: "FirstChatBot",
        botName: "DinningSuggestions",
        inputText: text,
        userId: lexUserId,
        sessionAttributes: {}
    };

    lexruntime.postText(params, function(err, data) {
        if (err) {
            console.log(err, err.stack);
        }
        if (data) {
            console.log(data); // got something back from Amazon Lex
            let d = new Date()
            if (d.getHours() < 5) {var hour = d.getHours() + 24}
            var time = String(d.getHours() - 5) +':' + String(d.getMinutes()) +':' + String(d.getSeconds())
            return_info = {"messages": [{"type": "string","unstructured": {"id": lexUserId,"text": data.message,"timestamp": time}}]}
            context.succeed(return_info);
        }
    });
};