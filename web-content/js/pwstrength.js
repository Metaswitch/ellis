/**
 * Project Clearwater - IMS in the Cloud
 * Copyright (C) 2013  Metaswitch Networks Ltd
 *
 * This program is free software: you can redistribute it and/or modify it 
 * under the terms of the GNU General Public License as published by the 
 * Free Software Foundation, either version 3 of the License, or (at your 
 * option) any later version, along with the “Special Exception” for use of 
 * the program along with SSL, set forth below. This program is distributed 
 * in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
 * A PARTICULAR PURPOSE.  See the GNU General Public License for more 
 * details. You should have received a copy of the GNU General Public 
 * License along with this program.  If not, see 
 * <http://www.gnu.org/licenses/>.
 *
 * The author can be reached by email at clearwater@metaswitch.com or by 
 * post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
 *
 * Special Exception
 * Metaswitch Networks Ltd  grants you permission to copy, modify, 
 * propagate, and distribute a work formed by combining OpenSSL with The 
 * Software, or a work derivative of such a combination, even if such 
 * copying, modification, propagation, or distribution would otherwise 
 * violate the terms of the GPL. You must comply with the GPL in all 
 * respects for all of the code used other than OpenSSL.
 * "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL 
 * Project and licensed under the OpenSSL Licenses, or a work based on such 
 * software and licensed under the OpenSSL Licenses.
 * "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License 
 * under which the OpenSSL Project distributes the OpenSSL toolkit software,
 * as those licenses appear in the file LICENSE-OPENSSL.
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
