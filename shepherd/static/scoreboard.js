function progress(timeleft, timetotal, $element) {
    var progressBarWidth = timeleft * $element.width() / timetotal;
    $element.find('div').animate({ width: progressBarWidth }, 500).html(Math.floor(timeleft/60) + ":"+ timeleft%60);
    if(timeleft > 0) {
        setTimeout(function() {
            progress(timeleft - 1, timetotal, $element);
        }, 1000);
    }
};

function startOverdrive() {
    progress(30, 30, $('#progressBar'));
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
   $('#blueTwist').attr('src', 'BlueTwisted.png');
}

function blueClear() {
   $('#blueTwist').attr('src', 'Blank.png');
}

function goldTwist() {
   $('#goldTwist').attr('src', 'GoldTwisted.png');
}

function goldClear() {
   $('#goldTwist').attr('src', 'Blank.png');
}

function runTimer1() {
  setTimeout(timer1, 0)
}


function runTimer2() {
  setTimeout(timer2, 0)
}

function runTimer3() {
  setTimeout(timer3, 0)
}

function runTimer4() {
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
      if (i == time) {  	
        clearInterval(interval);
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
      if (i == time) {  	
        clearInterval(interval);
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
      if (i == time) {  	
        clearInterval(interval);
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
      if (i == time) {  	
        clearInterval(interval);
        return;
      }
      $('.circle_animation4').css('stroke-dashoffset', initialOffset-((i+1)*(initialOffset/time)));
      i++;  
  }, 1000);

}


