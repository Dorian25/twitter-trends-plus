function display








function startTime() {
  const today = new Date();
  let h = today.getHours();
  let m = today.getMinutes();
  let s = today.getSeconds();
  m = checkTime(m);
  s = checkTime(s);
  document.getElementById('txt').innerHTML =  h + ":" + m + ":" + s;
  setTimeout(startTime, 1000);
}

function checkTime(i) {
  if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
  return i;
}

var data = ct.getCountry('FR');




const date = new Date();

// ✅ Get a string according to a provided Time zone
console.log(
  date.toLocaleString('en-US', {
    timeZone: 'America/Los_Angeles',
  }),
); // 👉️ "1/15/2022, 11:54:44 PM"

console.log(
  date.toLocaleString('de-DE', {
    timeZone: 'Europe/Berlin',
  }),
); // 👉️ "16.1.2022, 08:54:44"



const berlinDate = changeTimeZone(new Date(), 'Europe/Berlin');
console.log(berlinDate); // 👉️ "Sun Jan 16 2022 08:54:44"
