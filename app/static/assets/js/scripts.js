/* Open */
function openNav() {
    document.getElementById("search-container").style.height = "100%";
  }
  
  /* Close */
  function closeNav() {
    document.getElementById("search-container").style.height = "0%";
  }

  $('.search-button').click(function(){
    $(this).parent().toggleClass('open');
  });