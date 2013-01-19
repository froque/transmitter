var sess = null;
var wsuri = "ws://" + window.location.hostname + ":8081";
var retryCount = 0;
var retryDelay = 2;
var winterval;

function changeCell(v,id){
  if (v > 0){
    id.style.backgroundColor = "red";
  } else {
    id.style.backgroundColor = "white";
  }
}

function CheckAlarm(AlarmCode_v){
ampTemp_v    = 0x01 & AlarmCode_v;
SWR_v        = 0x02 & AlarmCode_v;
excTemp_v    = 0x04 & AlarmCode_v;
I_v          = 0x08 & AlarmCode_v;
ampVoltage_v = 0x10 & AlarmCode_v;
standby_v    = 0x20 & AlarmCode_v;

changeCell(ampTemp_v,ampTemp_id);
changeCell(SWR_v,SWR_id);
changeCell(excTemp_v,excTemp_id);
changeCell(I_v,I_id);
changeCell(ampVoltage_v,ampVoltage_id);
changeCell(standby_v,standby_id);
}

function cb_f(att_cb,att_fs){
  if(att_cb.checked){
    att_fs.disabled = false;
  } else {
    att_fs.disabled = true;
  }
}

// Callback used in PubSub for updating Transmitter Status
function TransmitterStatus(topicUri, event) {
    AlarmCode.innerHTML = event.AlarmCode;
    CheckAlarm(parseInt(event.AlarmCode, 10));
    Pfwd.innerHTML = event.Pfwd;
    ref.innerHTML = event.ref;
    Texc.innerHTML = event.Texc;
    Tamp.innerHTML = event.Tamp;
    Uexc.innerHTML = event.Uexc;
    Uamp.innerHTML = event.Uamp;
    audio.innerHTML = event.Audio;
    Iexc.innerHTML = event.Iexc;
    Iamp.innerHTML = event.Iamp;
    Uptime.innerHTML = event.Uptime;
    Freq.innerHTML = event.Freq;
    Firmware.innerHTML = event.Firmware;
    PowerLimit.innerHTML = event.PowerLimit;
}

function readTX() {
   sess.call("rpc:read-tx");
}

function autoReadTx() {
  if (autoread.checked ) {
    readTx.disabled = true;
    winterval = window.setInterval(readTX,2000);
  } else {
    readTx.disabled = false;
    window.clearInterval(winterval);
  }
}

function setSettings() {

  if (stereo.checked) {
    channels = stereo.value;
  } else {
    channels = mono.value;
  }
  attack_v = attack.options[attack.selectedIndex].value;
  decay_v = decay.options[decay.selectedIndex].value;
  interval_v = interval.options[interval.selectedIndex].value;
  threshold_v = threshold.options[threshold.selectedIndex].value;
  compression_v = compression.options[compression.selectedIndex].value;
  swr_alarm_v = swr_alarm.options[swr_alarm.selectedIndex].value;
  current_alarm_v = current_alarm.options[current_alarm.selectedIndex].value;
  temp_alarm_v = temp_alarm.options[temp_alarm.selectedIndex].value;
  Uamp_alarm_v = Uamp_alarm.options[Uamp_alarm.selectedIndex].value;
  treble_v = treble.options[treble.selectedIndex].value;
  bass_v = bass.options[bass.selectedIndex].value;
  left_gain_v = left_gain.options[left_gain.selectedIndex].value;
  right_gain_v = right_gain.options[right_gain.selectedIndex].value;

  if(power_cb.checked){
    sess.call("rpc:set-power",power.value);
  }
  if(freq_cb.checked){
    sess.call("rpc:set-freq",freq.value);
  }
  if(channels_cb.checked){
    sess.call("rpc:set-channels",channels);
  }
  if(DSP_cb.checked){
    sess.call("rpc:set-DSP",attack_v,decay_v,interval_v,
              threshold_v,compression_v);
  }
  if(alarm_cb.checked){
    sess.call("rpc:set-alarms",swr_alarm_v,current_alarm_v,temp_alarm_v,
            Uamp_alarm_v);
  }
  if(bass_treble_cb.checked){
    sess.call("rpc:set-bass-treble",treble_v,bass_v);
  }
  if(audio_cb.checked){
    sess.call("rpc:set-audio",left_gain_v,right_gain_v);
  }
}

function connect() {
   sess = new ab.Session(wsuri,
      // function used after opening session
      function() {
         statusline.innerHTML = "Connected to " + wsuri;
         retryCount = 0;
         // Prefix for CURIE
         sess.prefix("event", "http://example.com/mcu#");
         sess.subscribe("event:tx-status", TransmitterStatus);
         // Prefix for CURIE
         sess.prefix("rpc", "http://example.com/mcu-control#");
      },
      // function used after close, lost, etc session
      function() {
         console.log(retryCount);
         retryCount = retryCount + 1;
         statusline.innerHTML = "Connection lost. Reconnecting (" + retryCount
                                 + ") in " + retryDelay + " secs ..";
         window.setTimeout(connect, retryDelay * 1000);
      }
   );
}

window.onload = function (){
   connect();
};
