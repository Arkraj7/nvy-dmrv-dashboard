(function() {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', 'assets/icons/icons.svg', true);
  xhr.onload = function() {
    if (xhr.status >= 200 && xhr.status < 400) {
      var div = document.createElement('div');
      div.style.display = 'none';
      div.innerHTML = xhr.responseText;
      document.body.insertBefore(div, document.body.firstChild);
    }
  };
  xhr.send();
})();
