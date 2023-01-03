var end_time = document.getElementsByClassName('end-time');
var end = new Array();
var countDownDate = new Array();
for (let i = 0; i < end_time.length; i++) {
    end.push(end_time[i].innerText);
    countDownDate.push(new Date(end[i]).getTime());
}

// Run func every second
var show_time = setInterval(function() {
    var now = new Date().getTime();
    var flag = 0;

    for (let i = 0; i < end_time.length; i++) {
        var timeleft = countDownDate[i] - now;
        var days = Math.floor(timeleft / (1000 * 60 * 60 * 24));
        var hours = Math.floor((timeleft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((timeleft % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((timeleft % (1000 * 60)) / 1000);

        end_time[i].innerText = hours + "h "+ minutes + "m "+ seconds + "s";

        if (timeleft <= 0)
            end_time[i].innerHTML = '<span class="text-danger">Sorry, this item is expired!</span>';
        else
            flag = 1;
    }
    console.log(flag);

    if (!flag) {
        clearInterval(show_time);
        document.getElementById('disable-it').disabled = true;
    }
}, 1000);