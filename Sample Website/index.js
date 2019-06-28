
function get_value(){
	var temp = document.getElementById("tx_body").value;
	return temp;
}

function send() {
	var temp = get_value();
	var req = new XMLHttpRequest();
	req.open("POST", "http://192.168.50.9:65430/transaction", true);
	req.withCredentials = true;
	req.setRequestHeader("Content-type", "application/json");
	req.setRequestHeader("Access-Control-Allow-Origin", "*");
	req.send(temp);
}

function check() {
	var temp = get_value();
	var req = new XMLHttpRequest();
	req.onreadystatechange = function() {
		if (req.readyState == XMLHttpRequest.DONE){
			var text = "BAD JSON";
			if (req.status == 200){
				text = req.responseText
				console.log(req.responseText)
			}
			if (req.status == 404){
				text = "NOT VERIFIED!";
			}
			document.getElementById("checkid").innerHTML = text;
		}
	}
	req.open("POST", "http://192.168.50.9:65430/check", true);
	req.setRequestHeader("Content-type", "application/json");
	req.setRequestHeader("Access-Control-Allow-Origin", "*");
	req.send(temp);
}
