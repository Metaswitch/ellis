/**
 * Copyright (C) Metaswitch Networks 2017
 * If license terms are provided to you in a COPYING file in the root directory
 * of the source code repository by which you are accessing this code, then
 * the license outlined in that COPYING file applies to your use.
 * Otherwise no rights are granted except for those provided to you by
 * Metaswitch Networks in a separate written agreement.
 */

var clearwater = (function(mod, $){
  var parsedUrl = mod.parseUrl();

  $(document).ready(function(){
    $('#forgot-form').validate({
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

    $('#forgot-form').submit(function(){
      // On form submit, rewrite the action URL and onsuccess/onfailure hidden fields to
      // the required values, based on the email address entered in the form.
      var email = $("#email-field").val();
      var subs = mod.multiSubst({
        "EMAIL": email,
        "SUCCESS_PARAMS": "info=" + encodeURIComponent("A password reset email has been sent to " + email + "."),
        "FAILURE_PARAMS": "email=" + encodeURIComponent(email),
      });

      $("#forgot-form").attr("action", subs);
      $("#forgot-onsuccess").val(subs);
      $("#forgot-onfailure").val(subs);
    });
  });

  if (parsedUrl.params.error == "true")
  {
    var details;
    if (parsedUrl.params.status == 400)
    {
      details = "The email address you entered is not valid.  Please try again.";
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

    $("#forgot-error").text(details);
    $("#forgot-error").show();
  }

  if (parsedUrl.params.email)
  {
    $("#email-field").val(parsedUrl.params.email);
  }

  return mod;
})(clearwater, jQuery);
