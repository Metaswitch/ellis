/**
 * Copyright (C) Metaswitch Networks 2017
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
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
