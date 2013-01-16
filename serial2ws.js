var sess = null;
var wsuri = "ws://" + window.location.hostname + ":8081";
var retryCount = 0;
var retryDelay = 2;
var analog0 = null;

// Callback used in PubSub
function onAnalogValue(topicUri, event) {
   switch (event.id) {
      case 0:
         analog0.innerHTML = event.value;
         break;
      default:
         break;
   }
}

// calls McuProtocol.controlLed in file serial2ws.py trough RPC
function controlLed(status) {
   sess.call("rpc:control-led", status);
//.always(ab.log);
}

function connect() {
   statusline = document.getElementById('statusline');
   sess = new ab.Session(wsuri,
      // function used after opening session
      function() {
         statusline.innerHTML = "Connected to " + wsuri;
         retryCount = 0;
         sess.prefix("event", "http://example.com/mcu#");         // Prefix for CURIE
         sess.subscribe("event:analog-value", onAnalogValue);
         sess.prefix("rpc", "http://example.com/mcu-control#");   // Prefix for CURIE
      },
      // function used after close, lost, etc session
      function() {
         console.log(retryCount);
         retryCount = retryCount + 1;
         statusline.innerHTML = "Connection lost. Reconnecting (" + retryCount + ") in " + retryDelay + " secs ..";
         window.setTimeout(connect, retryDelay * 1000);
      }
   );
}

window.onload = function (){
   analog0 = document.getElementById('analog0');
   connect();
};
