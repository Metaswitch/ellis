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
  $(document).ready(function(){
    $.validator.addMethod("validatePwConfirm", function(value, element) {
      var pwVal = $('#password-field').val();
      return pwVal == value && value.length != 0;
    });
    $('#signup-form').validate({
      errorClass: "help-inline",

      rules:{
        username: {
          required: true,
          email: true
        },
        password: "required",
        password_confirm: {validatePwConfirm: true},
        full_name: "required",
        signup_code: "required",
      },

      messages: {
        username: {
          required: "Please provide a valid email",
          email: "Your email must be of the form name@domain.ext"
        },
        password: "Please provide a password",
        password_confirm: "Passwords do not match",
        full_name: "Please provide a name",
        signup_code: "Please provide a valid sign-up code"
      },

      highlight: function(label) {
        $(label).closest('.control-group').removeClass('error warning success');
        $(label).closest('.control-group').addClass('error');
      },

      success: function(label) {
        $(label).closest('.control-group').removeClass('error warning success');
        $(label).closest('.control-group').addClass('success');
        var pwScore = $('#pw-score').attr('value');
        if (pwScore <= 2 && $('#password-field').attr('value').length != 0)
        {
          var pwControlGroup =  $('#password-field').closest('.control-group');
          pwControlGroup.removeClass('success');
          pwScore == 0 ? pwControlGroup.addClass('error') : pwControlGroup.addClass('warning');
        }
      }
    })
  });

  if (location.href.indexOf("status=409") > 0)
  {
    $("#username-taken").show();
  }
  else if (location.href.indexOf("status=403") > 0)
  {
    $("#incorrect-code").show();
  }
  else if (location.href.indexOf("error=true") > 0)
  {
    $("#unknown-error").show();
  }

  $("#signup-form").submit(function(evt) {
    $("#email-field").val($("#username-field").val());
    return true;
  });

  return mod;
})(clearwater, jQuery);
