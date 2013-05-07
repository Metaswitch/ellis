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
