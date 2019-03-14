// image gallery
// init the state from the input
$(".image-checkbox").each(function () {
  count = false;
  if ($(this).find('input[type="checkbox"]').first().attr("checked") && (count == false)) {
    $(this).addClass('image-checkbox-checked');
  }
  else {
    $(this).removeClass('image-checkbox-checked');
    count = true;
  }
});

$(":input").hover(function() {
    console.log('string')
    $(this).prop('checked', true);
});

function select(id) {
  document.getElementById(id).checked = true
}

// sync the state to the input
$(".image-checkbox").on("click", function (e) {
  console.log('test string')
  $(this).toggleClass('image-checkbox-checked');
  var $checkbox = $(this).find('input[type="checkbox"]');
  $checkbox.prop("checked",!$checkbox.prop("checked"))

  e.preventDefault();
});

 var socket = io('http://127.0.0.1:5001');
 var t1_name, t1_num, t2_name, t2_num
 var master_robot


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

if (getCookie('alliance') != '') {
    hideButtons()
}

socket.on('teams', function(data) {
  dictionary = JSON.parse(data)
  if (getCookie('alliance') == 'gold') {
      t1_name = JSON.parse(match_info).g1_name
      t1_num = JSON.parse(match_info).g1_num
      t2_name = JSON.parse(match_info).g2_name
      t2_num = JSON.parse(match_info).g2_num
  } else if (getCookie('alliance') == 'blue') {
      t1_name = JSON.parse(match_info).b1_name
      t1_num = JSON.parse(match_info).b1_num
      t2_name = JSON.parse(match_info).b2_name
      t2_num = JSON.parse(match_info).b2_num
  }
  setTeams()
})

socket.on('collect_perks', function(data) {

})

socket.on('collect_codes', function(data){
  submitPerks()
  //Change to next UI
})

function setTeams() {
    // TODO: Change name of elements
    $("#team-1-number").val(t1_num);
    $("#team-1-name").val(t1_name);
    $("#team-2-number").val(t2_num);
    $("#team-2-name").val(t2_name);
}

function blueClick() {
    hideButtons()
    document.cookie = "alliance=blue"
}

function goldClick() {
    hideButtons()
    document.cookie = "alliance=gold"
}

function hideButtons() {
    //TODO: $("gold element") set button style to hidden
    //TODO: $("blue element") set button style to hidden
}

function setMasterRobot() {
    //TODO: set master_robot
    //TODO: set clicked robot number prominently
}

//onclick
function submitPerks() {
    team_color = getCookie('alliance')
    //TODO: Gather list of selected perks
    //TODO: data = {'alliance' : team_color, 'master_robot' : 1000, 'perk_1' : '' ...}
    //TODO: socket.emit('ui-to-server-selected-perks', JSON.stringify(data))
    var robot = document.getElementsByName('master_robot');
    if (robot[0].checked) {
      master_robot = robot[0];
    } else {
      master_robot = robot[1];
    }
    perk1 = getPerk('perk1');
    perk2 = getPerk('perk2');
    perk3 = getPerk('perk3');
    data = {'alliance' : team_color, 'master_robot' : master_robot, 'perk1' : perk1, 'perk2' : perk2, 'perk3' : perk3}
    socket.emit('ui-to-server-selected-perks', JSON.stringify(data))
}

function getPerk(name) {
  var tier = document.getElementsByName(name);
  var perk = tier[0];
  for (var i = 0; i < tier.length; i++) {
    if (tier[i].checked) {
      perk = perk[i]
      break;
    }
  }
  return perk;
}
