
jQuery(function($){
    //From user pool get the jwt identity token by peel the url string

    var url_with_token = window.location.href;

    var jwt_identity_tokens = [];
    var query = url_with_token.split("#")[1];
    var queryArr = query.split("&");
    queryArr.forEach(function(item){
        var obj = {};
        var value = item.split("=")[1];
        var key = item.split("=")[0];
        obj[key] = value;
        console.log(JSON.stringify(obj));
        jwt_identity_tokens.push(obj);
    });

    /**
     * var jwt_identity_tokens = [
     * {"id_token":""},
     * {"access_token":""},
     * {"expires_in":""},
     * {"token_type"}
     * @type {number}
     */

    AWS.config.update({
        region: 'us-east-2'
    });
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
        region: 'us-east-2',
        IdentityPoolId: 'us-east-2:1e9204c1-1235-478c-95c9-d585c0d43471',
        Logins: {
            'cognito-idp.us-east-2.amazonaws.com/us-east-2_MYMYQUfjA': jwt_identity_tokens[0]['id_token']
        }
    });

    var currentAccessKey="";
    var currentSecretKey="";
    var currentSessionToken="";

    //refreshes credentials using AWS.CognitoIdentity.getCredentialsForIdentity()
    AWS.config.credentials.get(function(){
        // Credentials will be available when this function is called.
        currentAccessKey = AWS.config.credentials.accessKeyId;
        currentSecretKey = AWS.config.credentials.secretAccessKey;
        currentSessionToken = AWS.config.credentials.sessionToken;
        console.log('AccessKey\n' + currentAccessKey);
        console.log('SecretKey\n' + currentSecretKey);
        console.log('SessionToken\n' + currentSessionToken);
        console.log('Successfully logged in!');

    });

    var count = 0;
    var convForm = $('#chat').convform({
        eventList: {
            onInputSubmit: function(convState, ready) {
                console.log('input is being submitted...');
                //here you send the response to your API, get the results and build the next question
                //when ready, call 'ready' callback (passed as the second parameter)
                if(convState.current.answer.value==='end') {
                    convState.current.next = false;
                    //emulating random response time (100-600ms)
                    setTimeout(ready, Math.random()*500+100);
                } else {
                    if(Array.isArray(convState.current.answer)){
                        var answer = convState.current.answer.join(', ');
                    }
                    else{
                        var answer = convState.current.answer.text;
                    }

                    var apigClient = apigClientFactory.newClient({
                        accessKey: currentAccessKey,
                        secretKey: currentSecretKey,
                        sessionToken: currentSessionToken, //OPTIONAL: If you are using temporary credentials you must include the session token
                        region: 'us-east-2'
                    });

                    var body = {
                        messages: [
                            {
                                type: "request",
                                unstructured: {
                                    id: ""+count,
                                    text: answer+"",
                                    timestamp: Date.now().toString()
                                }
                            }
                        ]
                    };

                    apigClient.chatbotPost(null, body).then(function(result){
                            result = result.data.messages;

                            responseResult = result[0].unstructured.text;
                            var responseTime =  result[0].unstructured.timestamp;

                            console.log(responseTime.replace(/['"]+/g, ''));

                            convState.current.next = convState.newState({
                                type: 'input',
                                noAnswer: true,
                                name: 'dynamic-question-'+count,
                                questions: [''+responseResult],
                            });

                            setTimeout(ready, Math.random()*50+100);

                        }).catch(function(result){
                            // Add error callback code here.
                            console.log("error:"+JSON.stringify(result));
                    });

                }
                count++;
            }}});
});