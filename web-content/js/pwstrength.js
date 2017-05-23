/**
 * Copyright (C) Metaswitch Networks 2017
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var clearwater = (function(mod, $){ 
  
  var emptyPasswordHint = $('#hidden-password-div').html();
  
  function updatePwStrength(password)
  {
    var pwDiv = $('#hidden-password-div');
    var signInBtn = $('#signup-button');
    signInBtn.removeAttr('disabled');
    
    if(password.length == 0)
    {
      pwDiv.closest('.control-group').removeClass('warning success');
      pwDiv.html(emptyPasswordHint);
    }
    else
    {
      var inputs = [$('#username-field').val(), $('#full-name').val()];
      var score = zxcvbn(password, inputs).score;
      score = (password.length < 8) ? 0 : score;
      
      $('#pw-score').attr('value', score);

      if(score == 0)
      {
        signInBtn.attr('disabled', 'disabled');
      }
      var cgStyle = ['error', 'warning', 'warning', 'success', 'success'];
      
      var hint = "<ul><li>using several uncommon words</li>" +
                      "<li>adding numbers or symbols</li>" +
                      "<li>using uPeRCase at random</li>" +
                      "<li>increasing the length</li>" +
                      "<li>using creeative spellung.</li></ul>";

      var formMessage = ["Password is too easy to guess. Try" + hint,
                         "Password is easy to guess. Try" + hint,
                         "Password is easy to guess. Try" + hint,
                         "Great, that password looks hard to guess.",
                         "Awesome, that password looks very hard to guess."];

      $(pwDiv).closest('.control-group').removeClass('error warning success');
      $(pwDiv).closest('.control-group').addClass(cgStyle[score]);

      pwDiv.html(formMessage[score]);
    }
  }
  
  var pwField = $('#password-field'); 
  pwField.keyup(function(){
    updatePwStrength(pwField.val());
  });
  
  return mod;
})(clearwater, jQuery);
