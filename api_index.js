(function onLoad() {
    document.getElementById("signInButton").addEventListener("click", function() {

        var redirect_url="http://localhost:63342/CloudChatBotApt32/index.html";
        window.location.href = "https://cloudcomputing-myh.auth.us-east-2.amazoncognito.com/login?response_type=token&client_id=57jt352krrvm3f2qbka2521fbb&redirect_uri="+redirect_url;
    });
})();