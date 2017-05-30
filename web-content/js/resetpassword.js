/**
 * Copyright (C) Metaswitch Networks 2013
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var clearwater = (function(mod, $){
  var parsedUrl = mod.parseUrl();

  $(document).ready(function(){
    $('#pwreset-form').validate({
      errorClass: "help-inline",

      rules: {
        username: {
          required: true
        },
      },

      messages: {
        username: "Please enter your email address",
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
  });

  if (parsedUrl.params.error == "true")
  {
    var details;
    if (parsedUrl.params.status == 400)
    {
      details = "The password you supplied is unacceptable. Please try again.";
    }
    else if (parsedUrl.params.status == 422)
    {
      details = "This password reset link has expired. Please create a new one by clicking \"Forgot password\" on the login page.";
    }
    else if (parsedUrl.params.status == 503)
    {
      details = "The service is currently too busy to handle your request. Please try again later.";
    }
    else
    {
      details = "The service could not handle your request. Please try again later. (" + 
                parsedUrl.params.status + " " + parsedUrl.params.message + ": " + parsedUrl.params.reason + ")";
    }

    $("#pwreset-error").text(details);
    $("#pwreset-error").show();
  }

  if (parsedUrl.params.email)
  {
    $("#email-field").val(parsedUrl.params.email);
  }

  if (parsedUrl.params.token)
  {
    $("#token-field").val(parsedUrl.params.token);
  }

  // While loading the page, rewrite the action URL and
  // onsuccess/onfailure hidden fields to the required values, based
  // on the email address and token found in the URL.
  var subs = mod.multiSubst({
    "EMAIL": parsedUrl.params.email,
    "SUCCESS_PARAMS": "info=" + encodeURIComponent("Your password has been reset."),
    "FAILURE_PARAMS": "email=" + encodeURIComponent(parsedUrl.params.email) +
                      "&token=" + encodeURIComponent(parsedUrl.params.token)
  });

  $("#pwreset-form").attr("action", subs);
  $("#pwreset-onsuccess").val(subs);
  $("#pwreset-onfailure").val(subs);

  return mod;
})(clearwater, jQuery);
