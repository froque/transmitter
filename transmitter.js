var sess = null;
var wsuri = "wss://" + window.location.hostname + ":8081";
var retryCount = 0;
var retryDelay = 2;
var winterval;

function getRadioValue(radioGroup){
  for (var k = 0; k < document.getElementsByName(radioGroup).length; k++){
    if (document.getElementsByName(radioGroup)[k].checked){
      return document.getElementsByName(radioGroup)[k].value;
    }
  }
}

function updateTime(topicUri, date){
  time_id.innerHTML = date;
}

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

// function to enable or disable the spinbox and following checkbox
function AF_f(cbox, cbox2, fs){
  cb_f(cbox,fs)
  if(cbox2 != null){
    if(cbox.checked){
      cbox2.disabled = false;
    } else {
      if (cbox2.checked){
        cbox2.click();
      }
      cbox2.disabled = true;
    }
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

function setRdsSettings(){
  if (RDS_cb.checked){
    sess.call("rpc:set-RDS", getRadioValue("rds"));
  }
  if (PI_code_cb.checked){
    var country_v = country_id.options[country_id.selectedIndex].value;
    var country_ecc_v = country_ecc_id.options[country_ecc_id.selectedIndex].value;
    var area_coverage_v = area_coverage_id.options[area_coverage_id.selectedIndex].value;
    var pr_v = pr_id.value;
    sess.call("rpc:PI-code", country_v, country_ecc_v, area_coverage_v, pr_v);
  }
  if (A0_settings_cb.checked){
    var tp_v = getRadioValue("tp")
    var ta_v = getRadioValue("ta")
    var ms_v = getRadioValue("ms")
    var dyn_pty_v = getRadioValue("dyn_pty1")
    var compression_v = getRadioValue("compression1")
    var channels_v = getRadioValue("channels1")
    var ah_v = getRadioValue("ah")
    var program_type_v = program_type_id.options[program_type_id.selectedIndex].value;
    sess.call("rpc:A0-settings", tp_v, ta_v, ms_v, dyn_pty_v, compression_v, channels_v, ah_v, program_type_v);
  }
  if (PF_alternative_cb.checked){
      var cb    = new Array();
      var value = new Array();
      cb[0] = AF1_cb_id.checked
      cb[1] = AF2_cb_id.checked
      cb[2] = AF3_cb_id.checked
      cb[3] = AF4_cb_id.checked
      cb[4] = AF5_cb_id.checked
      cb[5] = AF6_cb_id.checked
      cb[6] = AF7_cb_id.checked
      value[0] = AF1_id.value
      value[1] = AF2_id.value
      value[2] = AF3_id.value
      value[3] = AF4_id.value
      value[4] = AF5_id.value
      value[5] = AF6_id.value
      value[6] = AF7_id.value
      sess.call("rpc:PF-alternative", cb, value)
  }
  if (static_PS_cb.checked){
    sess.call("rpc:static-PS", static_PS_id.value);
  }
  if (Time_Date_cb.checked){
    sess.call("rpc:sync-time");
  }
  if (RT_cb.checked){
    sess.call("rpc:RT",RT_id.value);
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
         sess.subscribe("event:update-time", updateTime);
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
