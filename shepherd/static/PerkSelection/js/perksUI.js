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

function checkCookie() {
  if (getCookie('alliance') != '') {
      hideButtons()
  }
  t1_num = getCookie('t1')
  t2_num = getCookie('t2')
  setTeams(t1_num, t2_num)
}

function storeTeams(t1, t2) {
    var ca = document.cookie.split(';')
    document.cookie = "t1="+t1
    document.cookie = "t2="+t2
}

window.onload = checkCookie

socket.on('teams', function(data) {
  dictionary = JSON.parse(data)
  if (getCookie('alliance') == 'gold') {
      // t1_name = JSON.parse(data).g1name
      t1_num = JSON.parse(data).g1num
      // t2_name = JSON.parse(data).g2name
      t2_num = JSON.parse(data).g2num
  } else if (getCookie('alliance') == 'blue') {
      // t1_name = JSON.parse(data).b1name
      t1_num = JSON.parse(data).b1num
      // t2_name = JSON.parse(data).b2name
      t2_num = JSON.parse(data).b2num
  }
  storeTeams(t1_num, t2_num)
  setTeams(t1_num, t2_num)
})

socket.on('collect_perks', function(data) {
  var origin = window.location.origin
  window.location.href = origin + "/perksUI.html"
})

socket.on('collect_codes', function(data){
  submitPerks()
  //Change to next UI
  var origin = window.location.origin
  window.location.href = origin + "/submit.html"
})

socket.on('reset', function(data){
  var origin = window.location.origin
  window.location.href = origin + "/reset.html"
})


function setTeams(t1_num, t2_num) {
    // TODO: Change name of elements
    $("#team-1-number").val(t1_num);
    // $("#team-1-name").val(t1_name);
    $("#team-2-number").val(t2_num);
    // $("#team-2-name").val(t2_name);
    $("#mr1label").text('Team Number ' + t1_num);
    $("#mr2label").text('Team Number ' + t2_num);
}

function blueClick() {
    hideButtons()
    document.cookie = "alliance=blue"
}

function goldClick() {
    hideButtons()
    document.cookie = "alliance=gold"
}

function murderCookie() {
    document.cookie = "alliance="
    showButtons()
}

function hideButtons() {
    //TODO: $("gold element") set button style to hidden
    //TODO: $("blue element") set button style to hidden
    $("#gold_button").css("display", "none")
    $("#blue_button").css("display", "none")
    $("#as_button").css("display", "none")
    // document.getElementById("gold_button").style.display = "none"
    // document.getElementById("blue_button").style.display = "none"
    // document.getElementById("as_button").style.display = "none"
}

function showButtons() {
  $("#gold_button").css("display", "block")
  $("#blue_button").css("display", "block")
  $("#as_button").css("display", "block")
  // document.getElementById("gold_button").style.display = "block"
  // document.getElementById("blue_button").style.display = "block"
  // document.getElementById("as_button").style.display = "block"
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
    console.log(t1_num)
    var robot = document.getElementsByName('master_robot');
    if (robot[1].checked) {
      master_robot = t2_num;
    } else {
      master_robot = t1_num;
    }
    perk_1 = getPerk('tier1');
    perk_2 = getPerk('tier2');
    perk_3 = getPerk('tier3');
    perks_data = {'alliance' : team_color, 'perk_1' : perk_1, 'perk_2' : perk_2, 'perk_3' : perk_3}
    master_robot_data = {'alliance' : team_color, 'team_num' : master_robot}
    socket.emit('ui-to-server-master-robot', JSON.stringify(master_robot_data))
    socket.emit('ui-to-server-selected-perks', JSON.stringify(perks_data))
}

perk_dict = {"cb1": "bubblegum", "cb2": "diet", "cb3": "sweet_spot", "cb4": "taffy", "cb5": "chocolate_covered_espresso_beans",
      "cb6": "minty_fresh_start", "cb7": "raspberry_cotton_candy", "cb8": "artificial_sweetener", "cb9": "jawbreaker", "cb10": "sour_gummy_worms"}

function getPerk(name) {
  var tier = document.getElementsByName(name);
  console.log(tier)
  var perk = "empty";
  for (var i = 0; i < tier.length; i++) {
    if (tier[i].checked) {
      perk = perk_dict[tier[i].id]
      break;
    }
  }
  return perk;
}
