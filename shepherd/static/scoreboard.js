var socket = io('http://127.0.0.1:5500');
var overTimer = true;
var stageTimer = true;
var timerUno = true;
var timerDos = true;
var timerThres = true;
var timerQuatro = true;
var goldSpoiledNumber = 0;
var blueSpoiledNumber = 0;
var isBlueTwisted = false;
var isGoldTwisted = false;

socket.on('connect', function(data) {
    socket.emit('join', 'scoreboard');
  });

socket.on('stage_timer_start', function(secondsInStage) {
    time = JSON.parse(secondsInStage).time
    stageTimerStart(time)
})

socket.on('launch_button_timer_start', function(allianceButton) {
    alliance = JSON.parse(allianceButton).alliance
    button = JSON.parse(allianceButton).button
    if (alliance == "blue"){
        if (button == 1) {
            runTimer1();
        } else {
            runTimer2();
        }
    } else {
        if (button == 1) {
            runTimer3();
        } else {
            runTimer4();
        }
    }
    });

socket.on("reset_timers", function() {
  overTimer = false;
  stageTimer = false;
  timerUno = false;
  timerDos = false;
  timerThres = false;
  timerQuatro = false;
})

socket.on("overdrive_start", function() {
  overTimer = true;
  startOverdrive(30);
})



socket.on("applied_effect", function(data) {
  console.log('?')
  alliance = JSON.parse(data).alliance
  effect = JSON.parse(data).effect
  if (alliance == "blue"){
      if (effect == "blackmail") {
          blueTwist();
      } else {
          blueSpoiledNumber += 1
           $('#blueSpoiledNumber').html(blueSpoiledNumber)
      }
  } else {
      if (effect == "blackmail") {
          goldTwist();
      } else {
          goldSpoiledNumber += 1
          $('#goldSpoiledNumber').html(goldSpoiledNumber)
      }
  }
})

socket.on("perks_selected", function(data) {
  console.log('selecting perks')
  alliance = JSON.parse(data).alliance
  perk1 = JSON.parse(data).perk_1
  perk2 = JSON.parse(data).perk_2
  perk3 = JSON.parse(data).perk_3

  select_perk(alliance, 1, perk1)
  select_perk(alliance, 2, perk2)
  select_perk(alliance, 3, perk3)
})

function select_perk(alliance, perk_num, perk) {
  id = '#' + alliance + "Perk" + perk_num.toString()
  $(id).attr('src', '../static/PerkSelection/assets/DummyPerks/' + perk + '.png');
}

socket.on("score", function(scores) {
  blueScore = JSON.parse(scores).blue_score;
  goldScore = JSON.parse(scores).gold_score;
  $('#blue-score').html(blueScore);
  $('#gold-score').html(goldScore);
})



function testing() {
  overTimer = false;
  stageTimer = false;
  timerUno = false;
  timerDos = false;
  timerThres = false;
  timerQuatro = false;
}

function stageTimerStart(timeleft) {
  stageTimer = true;
  runStageTimer(timeleft);
}

function runStageTimer(timeleft) {
  if(timeleft >= 0){
    setTimeout(function() {
      $('#stage-timer').html(Math.floor(timeleft/60) + ":"+ pad(timeleft%60))
      if(stageTimer) {
        stageTimerStart(timeleft - 1);
      } else {
        stageTimerStart(0)
        $('#stage-timer').html("0:00")
      }
  }, 1000);
  }
}

function pad(number) {
  return (number < 10 ? '0' : '') + number
}

function progress(timeleft, timetotal, $element) {
    var progressBarWidth = timeleft * $element.width() / timetotal;
    $element.find('div').animate({ width: progressBarWidth }, 500).html(Math.floor(timeleft/60) + ":"+ pad(timeleft%60));
    if(timeleft > 0) {
        setTimeout(function() {
            if(overTimer) {
              progress(timeleft - 1, timetotal, $element);
            } else {
              progress(0, 0, $element)
            }
        }, 1000);
    } else {
      $element.find('div').animate({ width: 0 }, 500).html("")
      $('#overdriveText').css('color', 'white');
    }
};

function startOverdrive(time) {
    overTimer = true;
    $('#overdriveText').css('color', 'pink');
    progress(time, time, $('#progressBar'));
}

var a = 0
  , pi = Math.PI
  , t = 30

var counter = t;

console.log($("textbox").text() + "x")
console.log(t)

function draw() {
  // a should depend on the amount of time left
  a++;
  a %= 360;
  var r = ( a * pi / 180 )
    , x = Math.sin( r ) * 15000
  , y = Math.cos( r ) * - 15000
  , mid = ( a > 180 ) ? 1 : 0
    , anim =
        'M 0 0 v -15000 A 15000 15000 1 '
           + mid + ' 1 '
           +  x  + ' '
           +  y  + ' z';
  //[x,y].forEach(function( d ){
  //  d = Math.round( d * 1e3 ) / 1e3;
  //});
  $("#loader").attr( 'd', anim );
  console.log(counter);

  // time left should be calculated using a timer that runs separately
  if (a % (360 / t) == 0){
    counter -= 1;
    if (counter <= 9) {
      $("#textbox").css("left = '85px';")
    }
    $("#textbox").html(counter);
  }
  if (a == 0){
    return;
  }
  setTimeout(draw, 20); // Redraw
};

function blueTwist() {
   $('#blueTwist').attr('src', '../static/Twisted.png');
}

function goldTwist() {
   $('#goldTwist').attr('src', '../static/Twisted.png');
}

function runTimer1() {
  timerUno = true;
  setTimeout(timer1, 0)
}


function runTimer2() {
  timerDos = true;
  setTimeout(timer2, 0)
}

function runTimer3() {
  timerThres = true;
  setTimeout(timer3, 0)
}

function runTimer4() {
  timerQuatro = true;
  setTimeout(timer4, 0)
}
function timer1() {
  /* how long the timer will run (seconds) */

  var time = 30;
  var initialOffset = '440';
  var i = 1;

  /* Need initial run as interval hasn't yet occured... */
  $('.circle_animation1').css('stroke-dashoffset', initialOffset-(1*(initialOffset/time)));

  var interval = setInterval(function() {
      $('.timer1').text(time - i);
      if (i == time||!timerUno) {
        clearInterval(interval);
        $('.timer1').text(30);
        $('.circle_animation1').css('stroke-dashoffset', '0')
        return;
      }
      $('.circle_animation1').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;
  }, 1000);

}

function timer2() {
  /* how long the timer will run (seconds) */
  var time = 30;
  var initialOffset = '440';
  var i = 1;

  /* Need initial run as interval hasn't yet occured... */
  $('.circle_animation2').css('stroke-dashoffset', initialOffset-(1*(initialOffset/time)));

  var interval = setInterval(function() {
      $('.timer2').text(time - i);
      if (i == time || !timerDos) {
        clearInterval(interval);
        $('.timer2').text(30);
        $('.circle_animation2').css('stroke-dashoffset', '0')
        return;
      }
      $('.circle_animation2').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;
  }, 1000);

}

function timer3() {
  /* how long the timer will run (seconds) */
  var time = 30;
  var initialOffset = '440';
  var i = 1;

  /* Need initial run as interval hasn't yet occured... */
  $('.circle_animation3').css('stroke-dashoffset', initialOffset-(1*(initialOffset/time)));

  var interval = setInterval(function() {
      $('.timer3').text(time - i);
      if (i == time||!timerThres) {
        clearInterval(interval);
        $('.timer3').text(30);
        $('.circle_animation3').css('stroke-dashoffset', '0')
        return;
      }
      $('.circle_animation3').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;
  }, 1000);

}

function timer4() {
  /* how long the timer will run (seconds) */
  var time = 30;
  var initialOffset = '440';
  var i = 1;

  /* Need initial run as interval hasn't yet occured... */
  $('.circle_animation4').css('stroke-dashoffset', initialOffset-(1*(initialOffset/time)));

  var interval = setInterval(function() {
      $('.timer4').text(time - i);
      if (i == time || !timerQuatro) {
        clearInterval(interval);
        $('.timer4').text(30);
        $('.circle_animation4').css('stroke-dashoffset', '0')
        return;
      }
      $('.circle_animation4').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;
  }, 1000);

}
