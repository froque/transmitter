var sess = null;
var wsuri = "ws://" + window.location.hostname + ":8081";
var retryCount = 0;
var retryDelay = 2;
var interval;

// Callback used in PubSub for updating Transmitter Status
function TransmitterStatus(topicUri, event) {
    AlarmCode.innerHTML = event.AlarmCode
    Pfwd.innerHTML = event.Pfwd
    ref.innerHTML = event.ref
    Texc.innerHTML = event.Texc
    Tamp.innerHTML = event.Tamp
    Uexc.innerHTML = event.Uexc
    Uamp.innerHTML = event.Uamp
    audio.innerHTML = event.Audio
    Iexc.innerHTML = event.Iexc
    Iamp.innerHTML = event.Iamp
    Uptime.innerHTML = event.Uptime
    Freq.innerHTML = event.Freq
    Firmware.innerHTML = event.Firmware
    PowerLimit.innerHTML = event.PowerLimit
}

function readTX() {
   sess.call("rpc:read-tx");
}

function autoReadTx() {
  if (autoread.checked == true) {
    readTx.disabled = true;
    interval = window.setInterval(readTX,2000);
  } else {
    readTx.disabled = false;
    window.clearInterval(interval);
  }
}

function connect() {
   statusline = document.getElementById('statusline');
   sess = new ab.Session(wsuri,
      // function used after opening session
      function() {
         statusline.innerHTML = "Connected to " + wsuri;
         retryCount = 0;
         sess.prefix("event", "http://example.com/mcu#");         // Prefix for CURIE
         sess.subscribe("event:tx-status", TransmitterStatus);
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
   connect();
};
