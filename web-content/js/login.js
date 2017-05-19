/**
 * Copyright (C) Metaswitch Networks
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var clearwater = (function(mod, $){
  var parsedUrl = mod.parseUrl();

  $(document).ready(function(){
    $('#login-form').validate({
      errorClass: "help-inline",

      rules: {
        username: {
          required: true
        },
        password: {
          required: true
        }
      },

      messages: {
        username: "Please enter your username",
        password: "Please enter your password"
      },

      highlight: function(label) {
        $(label).closest('.control-group').removeClass('error warning success');
        $(label).closest('.control-group').addClass('error');
      },

      success: function(label) {
        $(label).closest('.control-group').removeClass('error warning success');
        $(label).closest('.control-group').addClass('success');
      }

    });

    $('#forgot-email-anchor').click(function()
    {
      emailField = $('#login-username');
      document.location.href = "/forgotpassword.html?email=" + emailField.val();
    });
  });

  if (parsedUrl.params.error == "true")
  {
    $("#login-error").show();
  }

  if (parsedUrl.params.info)
  {
    $("#login-info").text(parsedUrl.params.info);
    $("#login-info").show();
  }  

  return mod;
})(clearwater, jQuery);
