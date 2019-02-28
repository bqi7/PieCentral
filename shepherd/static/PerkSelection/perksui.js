var socket = io('http://127.0.0.1:5000');

socket.on('connect', function(data) {
  socket.emit('join', 'perks');
});

function getCookie(cname) {
  var name = cname + "=";
  var ca = document.cookie.split(';');
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') c = c.substring(1);
    if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
  }
  return "";
}


socket.on(--PERKS_HEADER.TEAMS--, function(data) {
  dictionary = JSON.parse(data)
  if (getCookie(alliance) == 'gold') {
      t1_name = JSON.parse(match_info).g1_name
      t1_num = JSON.parse(match_info).g1_num
      t2_name = JSON.parse(match_info).g2_name
      t2_num = JSON.parse(match_info).g2_num
  } else if (getCookie(alliance) == 'blue') {
      t1_name = JSON.parse(match_info).b1_name
      t1_num = JSON.parse(match_info).b1_num
      t2_name = JSON.parse(match_info).b2_name
      t2_num = JSON.parse(match_info).b2_num
  }

})


document.cookie = "cookiename=cookievalue"


//onclick
function submitPerks() {

}
