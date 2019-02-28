var socket = io('http://127.0.0.1:5000');
var overTimer = true;
var stageTimer = true;
var timerA = true;
var timerB = true;
var timerC = true;
var timerD = true;
var goldSpoiledNumber = 1;
var blueSpoiledNumber = 1;
var isBlueTwisted = false;
var isGoldTwisted = false;

socket.on('connect', function(data) {
    socket.emit('join', 'scoreboard');
  });

socket.on('teams', function(match_info) {
  b1_name = JSON.parse(match_info).b1_name
  b1_num = JSON.parse(match_info).b1_num
  b2_name = JSON.parse(match_info).b2_name
  b2_num = JSON.parse(match_info).b2_num
  g1_name = JSON.parse(match_info).g1_name
  g1_num = JSON.parse(match_info).g1_num
  g2_name = JSON.parse(match_info).g2_name
  g2_num = JSON.parse(match_info).g2_num
  match_number = JSON.parse(match_info).match_number
  nextMatch(b1_name, b1_num, b2_name, b2_num, g1_name, g1_num, g2_name, g2_num, match_number)
})

socket.on('stage_timer_start', function(secondsInStage) {
    time = JSON.parse(secondsInStage).time
    stageTimerStart(time)
})

socket.on('stage', function(stage_name) {
  stage = JSON.parse(stage_name).stage_name
  setStageName(stage)
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
  resetTimers();
})

socket.on("overdrive_start", function() {
  overTimer = true;
  startOverdrive(30);
})

socket.on("applied_effect", effectHandler)

function effectHandler(data) {
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
}

socket.on("score", function(scores) {
  blueScore = JSON.parse(scores).blue_score;
  goldScore = JSON.parse(scores).gold_score;
  $('#blue-score').html(blueScore);
  $('#gold-score').html(goldScore);
})

function testScore(blueScore, goldScore) {
  $('#blue-score').html(blueScore);
  $('#gold-score').html(goldScore);
}

function testing() {
  resetTimers()
}

function resetTimers(){
  overTimer = false;
  stageTimer = false;
  timerA = false;
  timerB = false;
  timerC = false;
  timerD = false;
}

function setStageName(stage) {
  $('#stage').html(stage)
}

function nextMatch(b1_name, b1_num, b2_name, b2_num, g1_name, g1_num, g2_name, g2_num, match_number){
  //set the names of all the teams and the match number
  $('#blue-1-name').html(b1_name)
  $('#blue-1-num').html(b1_num)
  $('#blue-2-name').html(b2_name)
  $('#blue-2-num').html(b2_num)
  $('#gold-1-name').html(g1_name)
  $('#gold-1-num').html(g1_num)
  $('#gold-2-name').html(g2_name)
  $('#gold-2-num').html(g2_num)
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
   $('#blueTwist').attr('src', 'Twisted.png');
}

function goldTwist() {
   $('#goldTwist').attr('src', 'Twisted.png');
}

function runTimer1() {
  timerA = true;
  //setTimeout(timer1, 0)
  launchButtonTimer('.timer1', '.circle_animation1', timerA);
}


function runTimer2() {
  timerB = true;
  launchButtonTimer('.timer2', '.circle_animation2', timerB);
}

function runTimer3() {
  timerC = true;
  launchButtonTimer('.timer3', '.circle_animation3', timerC);
}

function runTimer4() {
  timerD = true;
  launchButtonTimer('.timer4', '.circle_animation4', timerC);
}

function launchButtonTimer(timerNum, circleNum, timerStatus) { 
  /* how long the timer will run (seconds) */
  
  var time = 30;
  var initialOffset = '440';
  var i = 1;

  /* Need initial run as interval hasn't yet occured... */
  $(timerNum).css('stroke-dashoffset', initialOffset-(1*(initialOffset/time)));

  var interval = setInterval(function() {
      $(timerNum).text(time - i);
      if (timerNum == '.timer1') {
        timerStatus = timerA;
      } else if (timerNum == '.timer2') {
        timerStatus = timerB;
      } else if (timerNum == '.timer3') {
        timerStatus = timerC;
      } else {
        timerStatus = timerD;
      }
      if (i == time||!timerStatus) {  	
        clearInterval(interval);
        $(timerNum).text(30);
        $(circleNum).css('stroke-dashoffset', '0')
        return;
      }
      $(circleNum).css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;  
  }, 1000);

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
      if (i == time||!timerA) {  	
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
      if (i == time || !timerB) {  	
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
      if (i == time||!timerC) {  	
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
      if (i == time || !timerD) {  	
        clearInterval(interval);
        $('.timer4').text(30);
        $('.circle_animation4').css('stroke-dashoffset', '0')
        return;
      }
      $('.circle_animation4').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;
  }, 1000);

}
